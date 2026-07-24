import streamlit as st
from core.llm import chat
from core.prompts import MEMOIR_PROMPT_TEMPLATE, MEMOIR_REFLECTION_TEMPLATE
from core import db
from core.ui import require_groq_key, section_header, empty_state

require_groq_key()

section_header("📖", "Memoir - Your Life Stories",
               "These stories are saved for your family, in your own words. "
               "Pick a topic for inspiration, or write about anything you like.")

SUGGESTED_TOPICS = [
    "Your childhood home",
    "How you met your spouse",
    "A festival you remember fondly",
    "Your first job",
    "A lesson you want to pass on",
    "Something you're proud of",
]

with st.container(border=True):
    st.markdown("**Choose how you'd like to start**")
    topic_mode = st.radio(
        "Topic source",
        options=["suggested", "own"],
        format_func=lambda x: "📚 Pick a suggested topic" if x == "suggested" else "✍️ Write my own topic",
        horizontal=True,
        label_visibility="collapsed",
    )

    if topic_mode == "suggested":
        topic = st.selectbox("Choose a topic to write about", SUGGESTED_TOPICS)
    else:
        topic = st.text_input(
            "Your own topic title",
            placeholder="e.g. The day my grandson was born, My favourite recipe...",
        )

    can_get_question = bool(topic and topic.strip())
    if st.button("💡 Get a question about this topic", use_container_width=True, disabled=not can_get_question):
        prompt = MEMOIR_PROMPT_TEMPLATE.format(topic=topic.strip())
        with st.spinner("Thinking of a good question..."):
            question = chat([{"role": "user", "content": prompt}])
        st.session_state["memoir_question"] = question

    if "memoir_question" in st.session_state:
        st.info(st.session_state["memoir_question"])

    story = st.text_area(
        "Write your story here (or answer the question above)",
        height=180,
        placeholder="Start writing, or speak it aloud and type what you said...",
    )

    word_count = len(story.split())
    if story.strip():
        st.caption(f"📝 {word_count} words so far")

    save_disabled = not (topic and topic.strip() and story.strip())
    if st.button("💾 Save this story", use_container_width=True, disabled=save_disabled):
        db.save_memoir_entry(topic.strip(), story.strip())
        reflection_prompt = MEMOIR_REFLECTION_TEMPLATE.format(story=story.strip())
        try:
            reflection = chat([{"role": "user", "content": reflection_prompt}])
            st.success(reflection)
        except Exception:
            st.success("Story saved. Thank you for sharing it.")
        st.session_state.pop("memoir_question", None)
        st.rerun()

st.write("")

# ---------------- Saved stories: search, sort, browse ----------------
entries = db.get_memoir_entries()  # (topic, story, created_at), newest first - unchanged backend call

if not entries:
    empty_state("📖", "No stories saved yet.", "Choose a topic above and write your first chapter.")
else:
    section_header("📚", "Stories saved so far", f"{len(entries)} chapter(s) in your memoir")

    filter_col, sort_col = st.columns([2, 1])
    with filter_col:
        query = st.text_input(
            "Search your stories",
            placeholder="🔍 Search by topic or word...",
            label_visibility="collapsed",
        )
    with sort_col:
        order = st.selectbox(
            "Order", options=["Newest first", "Oldest first"], label_visibility="collapsed"
        )

    visible = entries
    if query.strip():
        q = query.strip().lower()
        visible = [e for e in visible if q in e[0].lower() or q in e[1].lower()]
    if order == "Oldest first":
        visible = list(reversed(visible))

    if not visible:
        st.info("No stories match your search.")
    else:
        for topic_saved, story_text, created_at in visible:
            with st.container(border=True):
                st.markdown(f"**📖 {topic_saved}**")
                st.caption(f"Last edited {created_at} • {len(story_text.split())} words")
                with st.expander("Read this chapter"):
                    st.write(story_text)
