import os
import time
import requests

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in .env")


# ============================================================
# CONFIGURATION
# ============================================================

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

OLLAMA_BASE_URL = "http://localhost:11434"

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


# ------------------------------------------------------------
# DO NOT CHANGE THIS
# This is your current interview question model.
# ------------------------------------------------------------

MODEL_NAME = "deepseek/deepseek-r1"


# ------------------------------------------------------------
# Ollama model
# ------------------------------------------------------------

OLLAMA_MODEL = "llama3.2:latest"


# ------------------------------------------------------------
# Gemini model ONLY for final interview result
# ------------------------------------------------------------

# IMPORTANT:
# Gemini is used ONLY for final interview evaluation.
#
# Do not use the old gemini-2.5-flash model here.

GEMINI_MODEL = "gemini-3.6-flash"


# ============================================================
# TIMEOUTS
# ============================================================

OPENROUTER_TIMEOUT = 30

GEMINI_TIMEOUT = 30

OLLAMA_TIMEOUT = 180


# ============================================================
# OPENROUTER
# ============================================================

def _call_openrouter(
    messages,
    temperature=0.7,
    max_tokens=2048
):

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "CareerLaunch AI"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    last_error = None

    for attempt in range(3):

        try:

            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=OPENROUTER_TIMEOUT
            )

            response.raise_for_status()

            result = response.json()

            if "choices" not in result or not result["choices"]:

                raise RuntimeError(
                    f"OpenRouter returned an unexpected response: {result}"
                )

            content = result["choices"][0]["message"]["content"]

            if not content:

                raise RuntimeError(
                    "OpenRouter returned an empty response."
                )

            return content


        except requests.exceptions.HTTPError as e:

            last_error = e

            status_code = (
                e.response.status_code
                if e.response is not None
                else None
            )

            try:
                details = e.response.text
            except Exception:
                details = str(e)


            print(
                f"⚠️ OpenRouter HTTP error: {status_code}"
            )

            print(
                "OpenRouter response:",
                details
            )


            # ------------------------------------------------
            # AUTHENTICATION
            # ------------------------------------------------

            if status_code in [401, 403]:

                raise RuntimeError(
                    f"OPENROUTER_AUTH_ERROR: {details}"
                )


            # ------------------------------------------------
            # NO CREDITS
            # ------------------------------------------------

            if status_code == 402:

                raise RuntimeError(
                    f"OPENROUTER_NO_CREDITS: {details}"
                )


            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if status_code == 429:

                raise RuntimeError(
                    f"OPENROUTER_RATE_LIMIT: {details}"
                )


            # ------------------------------------------------
            # TOKEN / CONTEXT LIMIT
            #
            # OpenRouter commonly reports these as 400.
            # We deliberately send them to the fallback.
            # ------------------------------------------------

            if status_code == 400:

                error_lower = details.lower()

                token_error_words = [
                    "token",
                    "context",
                    "maximum",
                    "max_tokens",
                    "too long",
                    "length",
                    "context_length",
                    "prompt"
                ]

                if any(
                    word in error_lower
                    for word in token_error_words
                ):

                    raise RuntimeError(
                        f"OPENROUTER_TOKEN_LIMIT: {details}"
                    )

                raise RuntimeError(
                    f"OPENROUTER_BAD_REQUEST: {details}"
                )


            # ------------------------------------------------
            # SERVER ERRORS
            # ------------------------------------------------

            if status_code in [500, 502, 503, 504]:

                raise RuntimeError(
                    f"OPENROUTER_SERVER_ERROR: {details}"
                )


            # ------------------------------------------------
            # OTHER HTTP ERRORS
            # ------------------------------------------------

            raise RuntimeError(
                f"OpenRouter API error ({status_code}): "
                f"{details}"
            )


        except requests.exceptions.Timeout as e:

            last_error = e

            raise RuntimeError(
                "OPENROUTER_TIMEOUT: "
                f"OpenRouter did not respond within "
                f"{OPENROUTER_TIMEOUT} seconds."
            )


        except requests.exceptions.RequestException as e:

            last_error = e

            raise RuntimeError(
                f"OPENROUTER_CONNECTION_ERROR: {e}"
            )


        except Exception as e:

            last_error = e

            raise


    raise RuntimeError(
        f"OpenRouter request failed: {last_error}"
    )


# ============================================================
# OLLAMA
# ============================================================

def _call_ollama(
    messages,
    temperature=0.7,
    max_tokens=2048
):

    print("🦙 Using local Ollama...")
    print(f"🦙 Model: {OLLAMA_MODEL}")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }

    try:

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )

        response.raise_for_status()

        result = response.json()

        if "message" not in result:

            raise RuntimeError(
                f"Ollama returned an unexpected response: {result}"
            )

        content = result["message"].get(
            "content",
            ""
        )

        if not content:

            raise RuntimeError(
                "Ollama returned an empty response."
            )

        print("✅ Ollama response received.")

        return content


    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "OLLAMA_CONNECTION_ERROR: "
            "Ollama is not running. "
            "Start Ollama and make sure "
            f"{OLLAMA_MODEL} is installed."
        )


    except requests.exceptions.Timeout:

        raise RuntimeError(
            "OLLAMA_TIMEOUT: "
            f"Ollama took longer than "
            f"{OLLAMA_TIMEOUT} seconds."
        )


    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"OLLAMA_API_ERROR: {e}"
        )


# ============================================================
# NORMAL AI CALL
#
# THIS IS FOR INTERVIEW QUESTIONS.
#
# DO NOT CHANGE THE MODEL/FLOW.
#
# OpenRouter → Ollama
# ============================================================

def _call_ai(
    messages,
    temperature=0.7,
    max_tokens=2048
):

    try:

        print()
        print("☁️ Trying OpenRouter...")
        print()

        response = _call_openrouter(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        print("✅ OpenRouter response received.")

        return response


    except Exception as openrouter_error:

        print()
        print("=" * 60)
        print("⚠️ OPENROUTER FAILED")
        print("=" * 60)
        print(str(openrouter_error))
        print("=" * 60)
        print("🔄 Falling back to Ollama...")
        print("=" * 60)
        print()

        try:

            return _call_ollama(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

        except Exception as ollama_error:

            raise RuntimeError(
                "Both AI providers failed.\n\n"
                f"OpenRouter error:\n"
                f"{openrouter_error}\n\n"
                f"Ollama error:\n"
                f"{ollama_error}"
            )


# ============================================================
# GEMINI
#
# THIS IS ONLY FOR FINAL INTERVIEW RESULTS.
#
# Gemini 3.6 Flash
# ============================================================

def _call_gemini(
    prompt,
    temperature=0.3,
    max_tokens=4096
):

    if not GEMINI_API_KEY:

        raise RuntimeError(
            "GEMINI_API_KEY not found in .env"
        )


    print()
    print("🟢 Trying Gemini for final evaluation...")
    print(f"🟢 Gemini model: {GEMINI_MODEL}")
    print()


    url = (
        f"{GEMINI_BASE_URL}/models/"
        f"{GEMINI_MODEL}:generateContent"
    )


    headers = {
        "Content-Type": "application/json"
    }


    params = {
        "key": GEMINI_API_KEY
    }


    # --------------------------------------------------------
    # IMPORTANT
    #
    # Gemini 3.6 Flash:
    #
    # Do NOT send temperature/top_p/top_k.
    #
    # We only send maxOutputTokens.
    # --------------------------------------------------------

    payload = {

        "contents": [

            {
                "role": "user",

                "parts": [

                    {
                        "text": prompt
                    }

                ]

            }

        ],

        "generationConfig": {

            "maxOutputTokens": max_tokens

        }

    }


    try:

        response = requests.post(

            url,

            headers=headers,

            params=params,

            json=payload,

            timeout=GEMINI_TIMEOUT

        )


        response.raise_for_status()


        result = response.json()


        candidates = result.get(
            "candidates",
            []
        )


        if not candidates:

            raise RuntimeError(
                f"Gemini returned no candidates: {result}"
            )


        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )


        if not parts:

            raise RuntimeError(
                f"Gemini returned no text: {result}"
            )


        text = parts[0].get(
            "text",
            ""
        )


        if not text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )


        print(
            "✅ Gemini final evaluation received."
        )


        return text


    except requests.exceptions.Timeout:

        raise RuntimeError(
            "GEMINI_TIMEOUT: "
            f"Gemini did not respond within "
            f"{GEMINI_TIMEOUT} seconds."
        )


    except requests.exceptions.HTTPError as e:

        try:
            details = e.response.text
        except Exception:
            details = str(e)


        raise RuntimeError(
            f"GEMINI_API_ERROR: {details}"
        )


    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"GEMINI_CONNECTION_ERROR: {e}"
        )


# ============================================================
# FINAL INTERVIEW EVALUATION
#
# Gemini → OpenRouter → Ollama
#
# ONLY THE RESULT USES THIS.
# ============================================================

def evaluate_with_gemini(
    prompt,
    temperature=0.2,
    max_tokens=4096
):

    # --------------------------------------------------------
    # 1. GEMINI
    # --------------------------------------------------------

    try:

        return _call_gemini(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )


    except Exception as gemini_error:

        print()
        print("=" * 60)
        print("⚠️ GEMINI FINAL EVALUATION FAILED")
        print("=" * 60)
        print(str(gemini_error))
        print("=" * 60)
        print("🔄 Falling back to OpenRouter...")
        print("=" * 60)
        print()


    # --------------------------------------------------------
    # 2. OPENROUTER
    # --------------------------------------------------------

    try:

        messages = [

            {
                "role": "user",
                "content": prompt
            }

        ]


        response = _call_openrouter(

            messages=messages,

            temperature=temperature,

            max_tokens=max_tokens

        )


        print(
            "✅ OpenRouter final evaluation received."
        )


        return response


    except Exception as openrouter_error:

        print()
        print("=" * 60)
        print("⚠️ OPENROUTER FINAL EVALUATION FAILED")
        print("=" * 60)
        print(str(openrouter_error))
        print("=" * 60)
        print("🔄 Falling back to Ollama...")
        print("=" * 60)
        print()


    # --------------------------------------------------------
    # 3. OLLAMA
    # --------------------------------------------------------

    try:

        messages = [

            {
                "role": "user",
                "content": prompt
            }

        ]


        response = _call_ollama(

            messages=messages,

            temperature=temperature,

            max_tokens=max_tokens

        )


        print(
            "✅ Ollama final evaluation received."
        )


        return response


    except Exception as ollama_error:

        raise RuntimeError(

            "All three AI providers failed "
            "during final evaluation.\n\n"

            f"Gemini error:\n"
            f"{gemini_error}\n\n"

            f"OpenRouter error:\n"
            f"{openrouter_error}\n\n"

            f"Ollama error:\n"
            f"{ollama_error}"

        )


# ============================================================
# ONE-TIME AI FUNCTION
#
# EXISTING PROJECT FUNCTION.
#
# This remains OpenRouter → Ollama.
# ============================================================

def ask_gemini(prompt):

    messages = [

        {
            "role": "user",
            "content": prompt
        }

    ]


    return _call_ai(

        messages=messages,

        temperature=0.7,

        max_tokens=2048

    )


# ============================================================
# CHAT CLASS
#
# USED BY INTERVIEW QUESTIONS.
#
# OpenRouter → Ollama
# ============================================================

class GeminiChat:

    def __init__(self, system_prompt):

        self.system_prompt = system_prompt


        self.messages = [

            {
                "role": "system",
                "content": system_prompt
            }

        ]


    def send(self, message):

        self.messages.append(

            {
                "role": "user",
                "content": message
            }

        )


        try:

            response = _call_ai(

                messages=self.messages,

                temperature=0.7,

                max_tokens=2048

            )


            self.messages.append(

                {
                    "role": "assistant",
                    "content": response
                }

            )


            return response


        except Exception:

            # Remove failed user message

            if (

                self.messages

                and

                self.messages[-1]["role"] == "user"

                and

                self.messages[-1]["content"] == message

            ):

                self.messages.pop()


            raise


# ============================================================
# PROVIDER STATUS
# ============================================================

def check_ollama():

    try:

        response = requests.get(

            f"{OLLAMA_BASE_URL}/api/tags",

            timeout=5

        )


        response.raise_for_status()


        data = response.json()


        models = data.get(
            "models",
            []
        )


        for model in models:

            if model.get("name") == OLLAMA_MODEL:

                return True


        return False


    except Exception:

        return False


# ------------------------------------------------------------

def check_openrouter():

    try:

        response = requests.get(

            f"{OPENROUTER_BASE_URL}/models",

            headers={

                "Authorization":
                    f"Bearer {OPENROUTER_API_KEY}"

            },

            timeout=5

        )


        response.raise_for_status()


        return True


    except Exception:

        return False


# ------------------------------------------------------------

def check_gemini():

    if not GEMINI_API_KEY:

        return False


    try:

        response = requests.get(

            f"{GEMINI_BASE_URL}/models",

            params={
                "key": GEMINI_API_KEY
            },

            timeout=5

        )


        response.raise_for_status()


        return True


    except Exception:

        return False


# ============================================================
# TEST AI PROVIDERS
# ============================================================

def test_ai():

    print()

    print("=" * 60)

    print(
        "🚀 CareerLaunch AI - AI Provider Test"
    )

    print("=" * 60)

    print()


    print(
        "Gemini available:",
        check_gemini()
    )


    print(
        "OpenRouter available:",
        check_openrouter()
    )


    print(
        "Ollama available:",
        check_ollama()
    )


    print()


    print(
        "Testing normal AI..."
    )


    print()


    try:

        response = ask_gemini(

            "Say hello to CareerLaunch AI "
            "in one short sentence."

        )


        print()

        print(
            "AI RESPONSE:"
        )

        print(
            "-" * 60
        )

        print(response)

        print(
            "-" * 60
        )

        print()

        print(
            "✅ AI test successful."
        )


    except Exception as e:

        print()

        print(
            "❌ AI test failed."
        )

        print(e)


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    test_ai()