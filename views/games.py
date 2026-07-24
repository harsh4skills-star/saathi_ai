import streamlit as st
from core.llm import chat
from core.prompts import TRIVIA_PROMPT
from core import db
from core.ui import require_groq_key, section_header

require_groq_key()

section_header("🎮", "Brain Games", "A gentle way to keep your mind active.")

GAME_NAME = "trivia"

def parse_trivia(raw: str):
    """Parses the strict Q/A/B/C/CORRECT format from TRIVIA_PROMPT."""
    lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
    data = {}
    for line in lines:
        for key in ("Q:", "A:", "B:", "C:", "CORRECT:"):
            if line.startswith(key):
                data[key.rstrip(":")] = line[len(key):].strip()
    if not all(k in data for k in ("Q", "A", "B", "C", "CORRECT")):
        return None
    return data

def new_question():
    with st.spinner("Preparing a question..."):
        raw = chat([{"role": "user", "content": TRIVIA_PROMPT}], temperature=0.9)
    parsed = parse_trivia(raw)
    st.session_state["trivia_q"] = parsed
    st.session_state["trivia_answered"] = False

if "trivia_q" not in st.session_state:
    new_question()

q = st.session_state.get("trivia_q")

with st.container(border=True):
    if not q:
        st.warning("Couldn't prepare a question - try again.")
        if st.button("🔄 Retry", use_container_width=True):
            new_question()
            st.rerun()
    else:
        st.markdown(f"### {q['Q']}")
        choice = st.radio(
            "Your answer:",
            options=["A", "B", "C"],
            format_func=lambda k: f"{k}. {q[k]}",
            index=None,
            key="trivia_choice",
        )

        if not st.session_state.get("trivia_answered") and choice:
            correct = choice == q["CORRECT"]
            db.save_game_result(GAME_NAME, correct)
            st.session_state["trivia_answered"] = True
            if correct:
                st.success(f"Correct! {q[choice]} is right. 🎉")
            else:
                st.error(f"Not quite - the correct answer was {q['CORRECT']}. {q[q['CORRECT']]}")

        if st.session_state.get("trivia_answered"):
            if st.button("➡️ Next question", use_container_width=True):
                new_question()
                st.rerun()

correct, total = db.get_game_stats(GAME_NAME)
if total:
    st.write("")
    st.caption(f"🏆 Score so far: {correct} / {total} correct")
