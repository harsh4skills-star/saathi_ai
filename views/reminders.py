import streamlit as st
from core import db
from core.ui import section_header, empty_state, reminder_card

section_header("⏰", "Reminders", "Never miss a medicine, call, or appointment.")

with st.container(border=True):
    st.markdown("**Add a new reminder**")
    with st.form("add_reminder_form", clear_on_submit=True):
        text = st.text_input(
            "What would you like to be reminded about?",
            placeholder="e.g. Take blood pressure tablet at 9 AM",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("💾 Save Reminder", use_container_width=True)
        if submitted and text.strip():
            db.add_reminder(text.strip())
            st.success("Reminder saved!")

st.write("")
rows = db.get_reminders()

if not rows:
    empty_state("⏰", "No reminders yet.", "Add your first reminder above and Saathi will help you remember.")
else:
    pending = [r for r in rows if not r[3]]
    done = [r for r in rows if r[3]]

    if pending:
        section_header("🔔", "Pending")
        for reminder_id, text, remind_at, is_done, created_at in pending:
            with st.container(border=True):
                reminder_card(text, f"Added {created_at}")
                if st.button("✅ Mark as done", key=f"done_{reminder_id}", use_container_width=True):
                    db.mark_reminder_done(reminder_id)
                    st.rerun()

    if done:
        st.write("")
        with st.expander(f"✅ Completed ({len(done)})"):
            for reminder_id, text, remind_at, is_done, created_at in done:
                st.markdown(f"~~{text}~~")
