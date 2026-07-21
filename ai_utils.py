"""AI drafting logic — system prompt, drafting, and error handling.
Uses Google Gemini's free-tier API (no billing required)."""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


def _get_api_key():
    try:
        import streamlit as st
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    return os.getenv("GOOGLE_API_KEY")


genai.configure(api_key=_get_api_key())

SYSTEM_PROMPT = """You are an email-reply assistant. Given the text of an incoming email, draft a reply.

Rules:
- Match the requested tone exactly (Professional, Casual, or Urgent).
- Never invent names, dates, order numbers, or facts not present in the original email.
- If information is missing (e.g. no name to address), use a neutral greeting like "Hi,".
- Keep the reply concise — 3-6 sentences unless the email requires more detail.
- Do not include a subject line, only the email body.
- Sign off with "Best," on its own line (no name, the user will add their own).
"""

model = genai.GenerativeModel(model_name="gemini-3.5-flash", system_instruction=SYSTEM_PROMPT)


def draft_reply(email_text: str, tone: str = "Professional") -> str:
    """Send email text to Gemini and return a drafted reply. Raises on failure."""
    try:
        response = model.generate_content(f"Tone: {tone}\n\nOriginal email:\n{email_text}")
        return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini API returned an error: {e}")