"""
Gmail API functions for the currently authenticated
Streamlit user.
"""

import base64

from email.mime.text import MIMEText

import streamlit as st

from bs4 import BeautifulSoup

from google.oauth2.credentials import Credentials

from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]


def get_gmail_service():

    if not st.user.is_logged_in:
        raise RuntimeError(
            "User is not logged in with Google."
        )


    access_token = st.user["access"]

    if not access_token:
        raise RuntimeError(
            "Google access token was not available."
        )


    credentials = Credentials(
        token=access_token,
        scopes=SCOPES
    )


    return build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False
    )


def _extract_body(payload):

    if "parts" in payload:

        for mime_type in (
            "text/plain",
            "text/html"
        ):

            for part in payload["parts"]:

                if (
                    part.get("mimeType") == mime_type
                    and part.get("body", {}).get("data")
                ):

                    raw = base64.urlsafe_b64decode(
                        part["body"]["data"]
                    ).decode(
                        "utf-8",
                        errors="ignore"
                    )

                    if mime_type == "text/html":
                        return _strip_html(raw)

                    return raw


        for part in payload["parts"]:

            result = _extract_body(part)

            if result:
                return result


    elif payload.get("body", {}).get("data"):

        raw = base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode(
            "utf-8",
            errors="ignore"
        )


        if payload.get("mimeType") == "text/html":

            return _strip_html(raw)


        return raw


    return ""


def _strip_html(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    return soup.get_text(
        separator="\n"
    ).strip()


def get_unread_emails(
    service,
    max_results=5
):

    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            labelIds=["UNREAD"],
            maxResults=max_results
        )
        .execute()
    )


    messages = results.get(
        "messages",
        []
    )


    emails = []


    for msg in messages:

        data = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg["id"],
                format="full"
            )
            .execute()
        )


        headers = {
            h["name"]: h["value"]
            for h in data["payload"]["headers"]
        }


        emails.append({

            "id": msg["id"],

            "subject": headers.get(
                "Subject",
                "(no subject)"
            ),

            "from": headers.get(
                "From",
                "(unknown)"
            ),

            "body": _extract_body(
                data["payload"]
            )
        })


    return emails


def mark_as_read(
    service,
    email_id
):

    (
        service.users()
        .messages()
        .modify(
            userId="me",
            id=email_id,
            body={
                "removeLabelIds": [
                    "UNREAD"
                ]
            }
        )
        .execute()
    )


def send_email(
    service,
    to,
    subject,
    body
):

    message = MIMEText(body)

    message["to"] = to

    message["subject"] = subject


    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()


    return (
        service.users()
        .messages()
        .send(
            userId="me",
            body={
                "raw": raw
            }
        )
        .execute()
    )