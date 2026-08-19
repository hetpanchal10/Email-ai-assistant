import streamlit as st
from email_utils import (
    get_gmail_service,
    get_unread_emails,
    mark_as_read,
    send_email,
)
from ai_utils import draft_reply

st.set_page_config(
    page_title="AI Email Assistant",
    layout="wide"
)

st.title("📧 AI Email Assistant")

# --------------------------------------------------
# Multi-User Login Check
# --------------------------------------------------
if not st.user.is_logged_in:
    st.info("👋 Welcome! Please connect your Google account to manage your personal inbox.")
    if st.button("Connect Your Gmail", type="primary"):
        st.login()
    st.stop()

# Show who is currently logged in via sidebar
st.sidebar.markdown(f"**Logged in as:**\n`{st.user.email}`")
if st.sidebar.button("Switch Account / Log out"):
    st.logout()

# --------------------------------------------------
# Connect to Gmail API for THIS user
# --------------------------------------------------
try:
    with st.spinner("Connecting to your Gmail inbox..."):
        service = get_gmail_service()
except Exception as e:
    st.error(f"Could not connect to Gmail: {e}")
    st.stop()

# --------------------------------------------------
# Fetch Unread Emails
# --------------------------------------------------
if "emails" not in st.session_state:
    try:
        st.session_state.emails = get_unread_emails(service, max_results=5)
    except Exception as e:
        st.error(f"Could not fetch emails: {e}")
        st.session_state.emails = []

if not st.session_state.emails:
    st.success("🎉 You have no unread emails in your inbox!")
    st.stop()

# Email Selector & Interface Layout
subjects = [f"{e['subject']} — {e['from']}" for e in st.session_state.emails]
selected_idx = st.selectbox("Select an email to reply to", range(len(subjects)), format_func=lambda i: subjects[i])
current_email = st.session_state.emails[selected_idx]

tone = st.selectbox("Select Reply Tone", ["Professional", "Casual", "Urgent"])
draft_key = f"draft_{current_email['id']}"

def generate_draft():
    try:
        with st.spinner("AI is drafting a reply..."):
            new_draft = draft_reply(current_email["body"], tone)
            st.session_state[draft_key] = new_draft
            st.session_state[f"editor_{current_email['id']}"] = new_draft
    except Exception as e:
        st.error(f"Failed to generate draft: {e}")

if draft_key not in st.session_state:
    generate_draft()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Original Email")
    st.text_area("From / Subject", value=f"From: {current_email['from']}\nSubject: {current_email['subject']}", height=70, disabled=True)
    st.text_area("Body", value=current_email["body"], height=350, disabled=True)

with col2:
    st.subheader("AI Draft Response")
    edited_reply = st.text_area("Edit your reply", value=st.session_state.get(draft_key, ""), height=350, key=f"editor_{current_email['id']}")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.button("🔄 Regenerate", use_container_width=True, on_click=generate_draft)
    with btn_col2:
        if st.button("✉️ Send Reply", type="primary", use_container_width=True):
            try:
                send_email(service, current_email["from"], f"Re: {current_email['subject']}", edited_reply)
                mark_as_read(service, current_email["id"])
                st.success("Email sent and marked as read!")
                st.session_state.emails.pop(selected_idx)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to send email: {e}")