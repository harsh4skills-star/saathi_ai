"""
views/home.py - The dashboard. app.py routes here by default.

All data still comes from core/db.py exactly as before (get_sessions,
get_facts, get_reminders, get_memoir_entries) - only the layout and
styling changed.
"""
import streamlit as st
from datetime import datetime
from core.db import get_sessions, get_facts, get_reminders, get_memoir_entries
from core.ui import hero_section, mood_selector, stat_card, quick_action_card, section_header

hour = datetime.now().hour
greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"

hero_section(
    f"{greeting}! Saathi is here for you.",
    "Helping you stay connected, remember important moments, and enjoy "
    "meaningful conversations every day.",
)

mood_selector()
st.write("")

# ---- Data (unchanged backend calls) ----
sessions = get_sessions(limit=100)
facts = get_facts(limit=1000)
reminders = get_reminders()
pending_reminders = [r for r in reminders if not r[3]]
memoir = get_memoir_entries()

# ---- Stat cards ----
section_header("📊", "Your Saathi at a glance")
c1, c2, c3, c4 = st.columns(4)
with c1:
    stat_card("Conversations", str(len(sessions)), "💬")
with c2:
    stat_card("Memories Saved", str(len(facts)), "🧠")
with c3:
    stat_card("Reminders Due", str(len(pending_reminders)), "⏰")
with c4:
    stat_card("Stories Written", str(len(memoir)), "📖")

st.write("")

# ---- Quick action cards ----
section_header("✨", "Quick actions")

row1 = st.columns(3)
row2 = st.columns(3)

with row1[0]:
    label = f"💬 {sessions[0][1] or 'Continue chat'}" if sessions else "💬 Start chatting"
    if quick_action_card(
        "💬", "Continue Chat",
        "Pick up your last conversation with Saathi." if sessions else "Start your first conversation with Saathi.",
        label, key="qa_chat",
    ):
        if sessions:
            st.session_state["active_session_id"] = sessions[0][0]
        st.switch_page("views/chat.py")

with row1[1]:
    if quick_action_card("🧠", "Memories", "Things Saathi remembers about you.", "Open Memories", key="qa_memories"):
        st.switch_page("views/memories.py")

with row1[2]:
    if quick_action_card("📖", "Life Stories", "Write and revisit your memoir chapters.", "Open Memoir", key="qa_memoir"):
        st.switch_page("views/memoir.py")

with row2[0]:
    reminder_desc = f"{len(pending_reminders)} reminder(s) waiting" if pending_reminders else "You're all caught up."
    if quick_action_card("⏰", "Today's Reminders", reminder_desc, "Open Reminders", key="qa_reminders"):
        st.switch_page("views/reminders.py")

with row2[1]:
    if quick_action_card("🎮", "Brain Games", "A gentle way to keep your mind active.", "Play a Game", key="qa_games"):
        st.switch_page("views/games.py")

with row2[2]:
    if quick_action_card("👨‍👩‍👧", "Family", "Send a warm weekly update to family.", "Open Family Bridge", key="qa_family"):
        st.switch_page("views/family_bridge.py")

st.write("")

# ---- Coming up ----
if pending_reminders:
    section_header("🔔", "Coming up")
    with st.container(border=True):
        for r in pending_reminders[:3]:
            st.markdown(f"⏰ &nbsp; {r[1]}", unsafe_allow_html=True)

st.write("")
st.caption(
    "Use the sidebar to explore Reminders, Memories, Memoir, Games, "
    "Family Bridge, and Settings."
)
