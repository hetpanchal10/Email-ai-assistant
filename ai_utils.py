"""AI drafting logic — system prompt, drafting, and error handling.
Uses Google Gemini via the current google-genai SDK."""
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def _get_api_key():
    try:
        import streamlit as st
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    return os.getenv("GOOGLE_API_KEY")


_client = genai.Client(api_key=_get_api_key())

SYSTEM_PROMPT = """You are an email-reply assistant. Given the text of an incoming email, draft a reply.

Rules:
- Match the requested tone exactly (Professional, Casual, or Urgent).
- Never invent names, dates, order numbers, or facts not present in the original email.
- If information is missing (e.g. no name to address), use a neutral greeting like "Hi,".
- Keep the reply concise — 3-6 sentences unless the email requires more detail.
- Do not include a subject line, only the email body.
- Sign off with "Best," on its own line (no name, the user will add their own).
"""

MODEL_NAME = "gemini-3.6-flash"  # current-gen flash model, per Google's guidance for this key


def draft_reply(email_text: str, tone: str = "Professional") -> str:
    """Send email text to Gemini and return a drafted reply. Raises on failure."""
    try:
        response = _client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Tone: {tone}\n\nOriginal email:\n{email_text}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty response (possibly blocked by safety filters).")
        return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini API returned an error: {e}")