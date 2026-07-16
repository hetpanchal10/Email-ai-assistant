"""Gmail fetching, parsing, and sending — the only file that talks to the Gmail API."""
import os
import base64
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _extract_body(payload) -> str:
    """Recursively walk the payload to find and decode the plain text (or HTML) body."""
    if "parts" in payload:
        # Prefer text/plain, fall back to text/html
        for mime_type in ("text/plain", "text/html"):
            for part in payload["parts"]:
                if part.get("mimeType") == mime_type and part.get("body", {}).get("data"):
                    raw = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    return _strip_html(raw) if mime_type == "text/html" else raw
        # Nested multipart (e.g. multipart/alternative inside multipart/mixed)
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result
    elif payload.get("body", {}).get("data"):
        raw = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        return _strip_html(raw) if payload.get("mimeType") == "text/html" else raw
    return ""


def _strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n").strip()


def get_unread_emails(service, max_results=5):
    results = service.users().messages().list(
        userId="me", labelIds=["UNREAD"], maxResults=max_results
    ).execute()
    messages = results.get("messages", [])
    emails = []
    for msg in messages:
        data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
        emails.append({
            "id": msg["id"],
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", "(unknown)"),
            "body": _extract_body(data["payload"]),
        })
    return emails


def mark_as_read(service, email_id: str):
    service.users().messages().modify(
        userId="me", id=email_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def send_email(service, to: str, subject: str, body: str):
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()
