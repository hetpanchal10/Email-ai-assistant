"""Standalone test: authenticate with Gmail, print 5 most recent unread emails."""
import os
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


def get_unread_emails(service, max_results=5):
    results = service.users().messages().list(
        userId="me", labelIds=["UNREAD"], maxResults=max_results
    ).execute()
    messages = results.get("messages", [])
    emails = []
    for msg in messages:
        data = service.users().messages().get(userId="me", id=msg["id"], format="metadata",
                                                metadataHeaders=["Subject", "From"]).execute()
        headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
        emails.append({"id": msg["id"], "subject": headers.get("Subject", "(no subject)"),
                        "from": headers.get("From", "(unknown)")})
    return emails


if __name__ == "__main__":
    service = get_gmail_service()
    for e in get_unread_emails(service):
        print(f"From: {e['from']} | Subject: {e['subject']}")
