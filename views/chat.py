import os
import streamlit as st
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder

load_dotenv()

from core.llm import chat, transcribe_audio
from core.prompts import build_system_prompt
from core import db, voice, rag
from core.ui import section_header, empty_state

if not os.getenv("GROQ_API_KEY"):
    st.error(
        "No Groq API key found. Copy .env.example to .env, add your free "
        "key from console.groq.com, then restart the app."
    )
    st.stop()

USER_AVATAR = "🧓"
ASSISTANT_AVATAR = "❤️"

# ---- Ensure there's an active session ----
if "active_session_id" not in st.session_state:
    sessions = db.get_sessions(limit=1)
    if sessions:
        st.session_state["active_session_id"] = sessions[0][0]
    else:
        st.session_state["active_session_id"] = db.create_session("New conversation")

voice_output_on = st.session_state.get("voice_output_on", True)
speech_lang = st.session_state.get("speech_lang", "auto")  # "auto" | "hi-IN" | "en-IN"
speech_rate = st.session_state.get("speech_rate", 0.9)
reply_language = st.session_state.get("reply_language", "auto")  # "auto" | "hi" | "en" - controls reply text style

# Voice INPUT language hint is deliberately its own setting, not derived
# from reply_language above. Bug this fixes: it used to be tied to the
# *reply* language preference, so choosing "English only" replies also
# silently forced Whisper to assume the user's *spoken* audio was English
# - any Hindi actually spoken while in that mode came out mistranscribed/
# garbled, because Whisper was told to expect English. These are two
# different things (how Saathi replies vs. what language you're speaking),
# so they now have independent settings.
voice_input_lang = st.session_state.get("voice_input_lang", "hi")
whisper_language_hint = None if voice_input_lang == "auto" else voice_input_lang

def try_extract_memory_silently(user_text: str, assistant_text: str):
    """Runs after every exchange, in the background of the request - no
    button needed. Fails silently (memory extraction is a nice-to-have,
    never worth breaking the chat over)."""
    try:
        prompt = (
            f"User said: {user_text}\nAssistant replied: {assistant_text}\n\n"
            "If this exchange reveals ONE specific, durable personal fact "
            "worth remembering (a name, a preference, a health note, an "
            "important date), reply with just that fact in one short "
            "sentence. Otherwise reply with exactly: NONE"
        )
        result = chat([{"role": "user", "content": prompt}], temperature=0.2)
        if result.strip().upper() != "NONE" and len(result.strip()) < 200:
            db.save_fact(result.strip())
    except Exception:
        pass  # memory extraction is best-effort, never blocks the chat

# ---- Sidebar: conversation history ----
with st.sidebar:
    st.markdown("### 💬 Conversations")
    if st.button("➕ New conversation", use_container_width=True):
        st.session_state["active_session_id"] = db.create_session("New conversation")
        st.rerun()

    st.caption("Recent")
    for sid, title, created_at, updated_at in db.get_sessions(limit=15):
        is_active = sid == st.session_state["active_session_id"]
        label = ("🟠 " if is_active else "") + (title or "New conversation")
        if st.button(label, key=f"session_{sid}", use_container_width=True):
            st.session_state["active_session_id"] = sid
            st.rerun()

    fact_count = len(db.get_facts(limit=1000))
    st.divider()
    st.caption(f"🧠 {fact_count} memories saved so far")

# ---- Main chat area ----
section_header("💬", "Chat with Saathi", "Your companion is always ready to listen.")

session_id = st.session_state["active_session_id"]
history = db.get_session_messages(session_id, limit=30)
for i, msg in enumerate(history):
    avatar = USER_AVATAR if msg["role"] == "user" else ASSISTANT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            # "Repeat that" - lets the user re-hear a past reply (e.g. if
            # they missed it, or autoplay was blocked) without having to
            # say anything again to trigger a new response.
            if st.button("🔊 Repeat", key=f"repeat_{session_id}_{i}"):
                spoken_lang = (
                    voice.detect_speech_lang(msg["content"])
                    if speech_lang == "auto" else speech_lang
                )
                voice.speak(msg["content"], lang=spoken_lang, rate=speech_rate)

if not history:
    empty_state("💬", "No conversations yet.", "Say Namaste to Saathi to get started! 🙏")

def handle_user_message(user_text: str):
    with st.chat_message("user", avatar=USER_AVATAR):
        st.write(user_text)
    db.save_message(session_id, "user", user_text)

    # First message in a session becomes its title, so the sidebar list is useful
    if len(history) == 0:
        db.set_session_title(session_id, user_text[:60])

    system_content = build_system_prompt(reply_language)
    # RAG: retrieve only the saved facts/memoir stories relevant to THIS
    # message, instead of always dumping the same fixed list of recent
    # facts regardless of what was asked. Also the first time memoir
    # stories (views/memoir.py) are usable in conversation at all - they
    # were previously saved but never read back into any prompt.
    relevant_context = rag.retrieve_relevant_context(user_text)
    if relevant_context:
        system_content += f"\n\n{relevant_context}"

    messages = [{"role": "system", "content": system_content}]
    messages += db.get_session_messages(session_id, limit=12)

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.spinner("Saathi is typing..."):
            try:
                reply = chat(messages)
            except Exception as e:
                reply = f"Sorry, I had trouble reaching the AI service: {e}"
        st.write(reply)

    db.save_message(session_id, "assistant", reply)
    if voice_output_on and not reply.startswith("Sorry, I had trouble"):
        # Bug fix: previously always spoke with the fixed `speech_lang`
        # Settings value, even though replies switch between Hindi and
        # English turn-to-turn in auto mode - so it regularly spoke the
        # wrong voice for a given reply. Now it detects the language of
        # THIS reply and speaks it correctly, unless the user has forced
        # a specific voice in Settings.
        spoken_lang = voice.detect_speech_lang(reply) if speech_lang == "auto" else speech_lang
        voice.speak(reply, lang=spoken_lang, rate=speech_rate)

    if not reply.startswith("Sorry, I had trouble"):
        try_extract_memory_silently(user_text, reply)

# ---- Voice input ----
with st.container(border=True):
    st.caption("🎙️ Tap the mic and speak, or type your message below.")
    audio = mic_recorder(start_prompt="🎤 Speak to Saathi", stop_prompt="⏹ Stop recording", just_once=True, format="wav", key="mic")

if audio is not None:
    audio_bytes = audio.get("bytes") or b""
    # Bug fix: `if audio and audio.get("bytes")` used to silently do
    # nothing when the recording was empty/too short (e.g. mic denied,
    # or the user tapped stop instantly) - no feedback at all, which
    # just looks like "voice doesn't work". Now every recording attempt
    # gets a clear message, and the mic button is right there to retry.
    if len(audio_bytes) < 1000:
        st.warning(
            "🎙️ That recording seemed empty. Please check your microphone "
            "permission and tap the mic again, speaking for a second or two."
        )
    else:
        with st.spinner("Listening..."):
            try:
                transcribed = transcribe_audio(
                    audio_bytes, filename="recording.wav", language=whisper_language_hint
                )
            except Exception as e:
                transcribed = ""
                st.error(
                    f"Sorry, I couldn't reach the speech service. Please check "
                    f"your internet connection and try again. ({e})"
                )
        if transcribed:
            handle_user_message(transcribed)
            st.rerun()
        else:
            st.warning(
                "🎙️ I didn't catch any words in that recording. Please try "
                "again, speaking a little closer to the mic."
            )

# ---- Text input (always available as a fallback) ----
typed = st.chat_input("Type your message here...")
if typed:
    handle_user_message(typed)
    st.rerun()
