import os
from dotenv import load_dotenv
from google import genai

# Load .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Gemini API key not found!")

client = genai.Client(api_key=API_KEY)


def ask_gemini(prompt):
    """
    One-time prompt.
    Used for ATS Resume Analyzer.
    """

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )

    return response.text


class GeminiChat:

    def __init__(self, system_prompt):

        self.chat = client.chats.create(
            model="gemini-flash-latest"
        )

        # Give Gemini its role
        self.chat.send_message(system_prompt)

    def send(self, message):

        response = self.chat.send_message(message)

        return response.text