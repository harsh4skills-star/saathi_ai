import streamlit as st
from core.llm import chat
from core import db
from core.ui import require_groq_key, section_header, empty_state, memory_card

require_groq_key()

section_header("🧠", "Memories", "Things Saathi remembers about you, so conversations feel personal over time.")
st.caption(
    "Saathi now saves memories automatically while you chat - the button "
    "below is for a manual sweep, and manual add is always available too."
)

col1, col2 = st.columns([2, 1])
with col1:
    find_clicked = st.button("✨ Find new memories from our recent chat", use_container_width=True)
if find_clicked:
    recent = db.get_recent_messages(limit=20)
    if not recent:
        st.info("Chat with Saathi first, then come back here.")
    else:
        conversation_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
        prompt = (
            "From this conversation, list up to 3 short, specific personal facts "
            "worth remembering long-term (names of family members, hobbies, "
            "preferences, important dates). One fact per line, no numbering, "
            "no extra commentary. If there is nothing worth remembering, reply "
            "with exactly: NONE"
        )
        with st.spinner("Thinking about what to remember..."):
            result = chat([
                {"role": "user", "content": f"{conversation_text}\n\n{prompt}"}
            ])
        if result.strip().upper() == "NONE":
            st.info("Nothing new to save from that conversation.")
        else:
            new_facts = [f.strip("- ").strip() for f in result.split("\n") if f.strip()]
            for fact in new_facts:
                db.save_fact(fact)
            st.success(f"Saved {len(new_facts)} new memories.")
            st.rerun()

with st.expander("➕ Add a memory manually"):
    manual = st.text_input("e.g. Granddaughter's name is Priya", label_visibility="collapsed",
                            placeholder="e.g. Granddaughter's name is Priya")
    if st.button("Save memory") and manual.strip():
        db.save_fact(manual.strip())
        st.success("Saved.")
        st.rerun()

st.write("")
section_header("📌", "Saved memories")
facts = db.get_facts()
if not facts:
    empty_state("🧠", "No memories saved yet.", "Let's create your first memory - chat with Saathi or add one manually above.")
else:
    st.caption(f"{len(facts)} memories saved")
    for fact, created_at in facts:
        memory_card(fact, str(created_at))
