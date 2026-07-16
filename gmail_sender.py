"""Standalone test: send a hardcoded email to yourself."""
import base64
from email.mime.text import MIMEText
from gmail_reader import get_gmail_service


def send_email(service, to: str, subject: str, body: str):
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


if __name__ == "__main__":
    service = get_gmail_service()
    profile = service.users().getProfile(userId="me").execute()
    my_email = profile["emailAddress"]
    send_email(service, my_email, "Test Email", "This is a test from gmail_sender.py")
    print(f"Sent test email to {my_email}")
