# AI Email Assistant

A human-in-the-loop dashboard that reads unread Gmail messages, drafts replies with Claude, and lets you edit and send them — all from a Streamlit UI.

## Architecture

```
Gmail API ──> email_utils.py ──> app.py (Streamlit UI) ──> ai_utils.py ──> Claude API
   ^                                    |
   └──────────── send / mark-as-read ───┘
```

- `email_utils.py` — all Gmail logic (auth, fetch, parse HTML→text, send, mark read)
- `ai_utils.py` — all Claude logic (system prompt, drafting, error handling)
- `app.py` — UI only, no business logic
- `gmail_reader.py`, `claude_drafter.py`, `gmail_sender.py` — standalone scripts used to test each API in isolation before wiring them together

## Technologies used

Python · Streamlit · Anthropic API (Claude) · Gmail API (OAuth2) · BeautifulSoup

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Anthropic API key**: copy `.env.example` to `.env` and add your key from console.anthropic.com.

3. **Gmail API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/) → create a project → enable the Gmail API.
   - Create OAuth 2.0 credentials (Desktop app), download as `credentials.json`, place it in the project root.
   - First run will open a browser to authorize; it saves a `token.json` for future runs.

4. Test each piece independently (optional but recommended):
   ```bash
   python gmail_reader.py
   python claude_drafter.py
   python gmail_sender.py
   ```

5. Run the app:
   ```bash
   streamlit run app.py
   ```

## Screenshot

_(Add a screenshot of the running Streamlit UI here.)_

## Notes

- `.env`, `credentials.json`, and `token.json` are gitignored — never commit these.
- The tone dropdown (Professional / Casual / Urgent) is passed into Claude's system prompt to control the draft's style.
