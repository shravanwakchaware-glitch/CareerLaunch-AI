import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

# Load .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Gemini API key not found!")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3-flash-preview"


def ask_gemini(prompt):
    """
    One-time prompt.
    Used for ATS Resume Analyzer.
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            return response.text

        except ServerError:
            print(f"Gemini busy... Retry {attempt + 1}/3")
            time.sleep(5)

    raise Exception("Gemini servers are busy. Please try again in a minute.")


class GeminiChat:

    def __init__(self, system_prompt):

        self.chat = client.chats.create(
            model=MODEL_NAME
        )

        # Give Gemini its role
        for attempt in range(3):
            try:
                self.chat.send_message(system_prompt)
                break

            except ServerError:
                print(f"Retrying system prompt... {attempt + 1}/3")
                time.sleep(5)
        else:
            raise Exception("Gemini servers are busy. Please try again later.")

    def send(self, message):

        for attempt in range(3):
            try:
                response = self.chat.send_message(message)
                return response.text

            except ServerError:
                print(f"Retrying message... {attempt + 1}/3")
                time.sleep(5)

        raise Exception("Gemini servers are busy. Please try again later.")