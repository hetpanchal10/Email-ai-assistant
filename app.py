"""Streamlit UI only. All logic lives in email_utils.py and ai_utils.py."""
import streamlit as st
from email_utils import get_gmail_service, get_unread_emails, mark_as_read, send_email
from ai_utils import draft_reply

st.set_page_config(page_title="AI Email Assistant", layout="wide")
st.title("📧 AI Email Assistant")

# --- Connect to Gmail (cached across reruns) ---
try:
    if "service" not in st.session_state:
        st.session_state.service = get_gmail_service()
except Exception as e:
    st.error(f"Could not connect to Gmail: {e}")
    st.stop()

service = st.session_state.service

# --- Load unread emails once, keep in session_state ---
if "emails" not in st.session_state:
    try:
        st.session_state.emails = get_unread_emails(service, max_results=5)
    except Exception as e:
        st.error(f"Could not fetch emails: {e}")
        st.session_state.emails = []

if not st.session_state.emails:
    st.info("No unread emails found.")
    st.stop()

# --- Pick which email to work on ---
subjects = [f"{e['subject']} — {e['from']}" for e in st.session_state.emails]
selected_idx = st.selectbox("Select an email", range(len(subjects)), format_func=lambda i: subjects[i])
current_email = st.session_state.emails[selected_idx]

tone = st.selectbox("Reply tone", ["Professional", "Casual", "Urgent"])

# --- Generate draft the first time this email is selected, or on demand ---
draft_key = f"draft_{current_email['id']}"

def generate_draft():
    try:
        with st.spinner("Claude is drafting a reply..."):
            new_draft = draft_reply(current_email["body"], tone)
            st.session_state[draft_key] = new_draft
            # Update the widget's own state key too — Streamlit ignores value=
            # on rerun once a widget with this key already exists.
            st.session_state[f"editor_{current_email['id']}"] = new_draft
    except Exception as e:
        st.error(f"Failed to generate draft: {e}")

if draft_key not in st.session_state:
    generate_draft()

# --- Two-column layout ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Original Email")
    st.text_area("From / Subject", value=f"From: {current_email['from']}\nSubject: {current_email['subject']}", height=70, disabled=True)
    st.text_area("Body", value=current_email["body"], height=350, disabled=True)

with col2:
    st.subheader("AI Draft (editable)")
    edited_reply = st.text_area("Draft reply", value=st.session_state.get(draft_key, ""), height=350, key=f"editor_{current_email['id']}")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        # on_click runs BEFORE the script reruns and recreates the widget,
        # so updating session_state here is safe (unlike doing it after the button check).
        st.button("🔄 Regenerate", use_container_width=True, on_click=generate_draft)
    with btn_col2:
        if st.button("✉️ Send", type="primary", use_container_width=True):
            try:
                to_address = current_email["from"]
                send_email(service, to_address, f"Re: {current_email['subject']}", edited_reply)
                mark_as_read(service, current_email["id"])
                st.success("Sent and marked as read!")
                # Remove from local list so it disappears from the dropdown
                st.session_state.emails.pop(selected_idx)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to send: {e}")