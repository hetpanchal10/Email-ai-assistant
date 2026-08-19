import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

def get_gmail_service():
    """Builds the Gmail API service dynamically for the currently logged-in user."""
    if not hasattr(st, "user") or not st.user.is_logged_in:
        raise Exception("User is not logged in.")
    
    try:
        access_token = st.user.tokens["access"]
    except KeyError:
        raise Exception('st.user has no key "access". Verify that expose_tokens = ["id", "access"] is in your Secrets.')
    
    # Use the individual user's active session token
    creds = Credentials(token=access_token)
    return build('gmail', 'v1', credentials=creds)

def get_unread_emails(service, max_results=5):
    """Fetches unread emails strictly from the authenticated user's inbox."""
    results = service.users().messages().list(userId='me', q='is:unread', maxResults=max_results).execute()
    messages = results.get('messages', [])
    
    email_list = []
    for msg in messages:
        txt = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = txt['payload']['headers']
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        body = txt.get('snippet', '')
        
        email_list.append({
            'id': msg['id'],
            'subject': subject,
            'from': sender,
            'body': body
        })
    return email_list

def mark_as_read(service, msg_id):
    service.users().messages().batchModify(
        userId='me',
        body={'ids': [msg_id], 'removeLabelIds': ['UNREAD']}
    ).execute()

def send_email(service, to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()