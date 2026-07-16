"""Standalone test: send a hardcoded email body to Gemini and print the reply."""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",
    system_instruction="You are an email assistant. Draft a short, professional reply.",
)


def draft_reply(email_text: str) -> str:
    response = model.generate_content(email_text)
    return response.text


if __name__ == "__main__":
    test_email = "Where is my package? It's been 2 weeks."
    print(draft_reply(test_email))