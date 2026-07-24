import streamlit as st
from core.family_bridge import build_digest_text, send_digest_email
from core.ui import require_groq_key, section_header

require_groq_key()

section_header("👨‍👩‍👧", "Family Bridge",
               "Send a warm weekly update to your family, without asking them "
               "to install anything - it just arrives in their email.")

st.info(
    "To enable this, set SENDER_EMAIL, SENDER_APP_PASSWORD, and FAMILY_EMAIL "
    "in your .env file. See .env.example for how to get a free Gmail app "
    "password. For a real weekly schedule (not just manual sending), see "
    "scripts/send_weekly_digest.py and the included GitHub Actions workflow."
)

with st.container(border=True):
    st.markdown("**Weekly update**")
    if st.button("✨ Preview this week's update", use_container_width=True):
        with st.spinner("Putting together this week's update..."):
            digest = build_digest_text()
        st.session_state["digest_preview"] = digest

    if "digest_preview" in st.session_state:
        st.text_area("Preview", st.session_state["digest_preview"], height=200)
        if st.button("📧 Send to family now", use_container_width=True):
            success, message = send_digest_email(st.session_state["digest_preview"])
            if success:
                st.success(message)
            else:
                st.error(message)
