import streamlit as st
from core import voice
from core.ui import section_header

section_header("⚙️", "Settings", "Make Saathi work the way you like.")

# ---------------- Reply language (what Saathi types back) ----------------
with st.container(border=True):
    st.markdown("**🗣️ Reply Language**")
    st.caption("Saathi only speaks Hindi and English - choose how replies should sound.")
    reply_language = st.radio(
        "How should Saathi reply?",
        options=["auto", "hi", "en"],
        format_func=lambda x: {
            "auto": "Hinglish (Hindi + English mix) - default",
            "hi": "Hindi only",
            "en": "English only",
        }[x],
        index=["auto", "hi", "en"].index(st.session_state.get("reply_language", "auto")),
        label_visibility="collapsed",
    )
    st.session_state["reply_language"] = reply_language

st.write("")

# ---------------- Voice (speech output + input hint) ----------------
with st.container(border=True):
    st.markdown("**🔊 Voice**")
    voice_on = st.checkbox(
        "Speak Saathi's replies aloud",
        value=st.session_state.get("voice_output_on", True),
    )
    st.session_state["voice_output_on"] = voice_on

    lang = st.selectbox(
        "Spoken reply language (text-to-speech)",
        options=["auto", "hi-IN", "en-IN"],
        format_func=lambda x: {
            "auto": "Auto (match each reply - recommended)",
            "hi-IN": "Always Hindi voice",
            "en-IN": "Always Indian English voice",
        }[x],
        index=["auto", "hi-IN", "en-IN"].index(st.session_state.get("speech_lang", "auto")),
    )
    st.session_state["speech_lang"] = lang
    st.caption(
        "\"Auto\" listens to what each reply actually says and picks the "
        "matching voice, so Hindi and English replies both sound right "
        "even in Hinglish conversations. Only switch this to a fixed "
        "voice if auto-detection sounds wrong on your device."
    )

    rate = st.slider(
        "Speaking speed",
        min_value=0.6, max_value=1.3,
        value=float(st.session_state.get("speech_rate", 0.9)),
        step=0.1,
    )
    st.session_state["speech_rate"] = rate
    speed_label = "Slower" if rate < 0.85 else ("Faster" if rate > 1.0 else "Normal")
    st.caption(f"Current: {speed_label} ({rate:.1f}x)")

    if st.button("▶️ Test voice", use_container_width=True):
        test_lang = "hi-IN" if lang == "en-IN" else "en-IN" if lang == "hi-IN" else "hi-IN"
        sample = "नमस्ते! मैं साथी हूं।" if test_lang == "hi-IN" else "Hello! This is Saathi speaking."
        voice.speak(sample, lang=test_lang, rate=rate)

    st.caption(
        "Note: available voices depend on your browser. Chrome generally has "
        "the best Hindi voice support."
    )

st.write("")

# ---------------- Voice input language ----------------
with st.container(border=True):
    st.markdown("**🎤 Voice Input**")
    st.caption(
        "What language do you usually speak in when using the mic? This "
        "helps Saathi transcribe your voice more accurately - it's "
        "separate from the reply language above."
    )
    voice_input_lang = st.radio(
        "Voice input language",
        options=["hi", "en", "auto"],
        format_func=lambda x: {
            "hi": "I mostly speak Hindi (recommended)",
            "en": "I mostly speak English",
            "auto": "Auto-detect (can misjudge short recordings)",
        }[x],
        index=["hi", "en", "auto"].index(st.session_state.get("voice_input_lang", "hi")),
        label_visibility="collapsed",
    )
    st.session_state["voice_input_lang"] = voice_input_lang

st.write("")

# ---------------- Display / accessibility ----------------
with st.container(border=True):
    st.markdown("**🔠 Display**")
    large_text = st.checkbox(
        "Large text mode (bigger fonts everywhere)",
        value=st.session_state.get("large_text", False),
    )
    st.session_state["large_text"] = large_text
    st.caption("Turn this on for extra-large, easy-to-read text across the whole app.")

st.write("")

# ---------------- About ----------------
with st.container(border=True):
    st.markdown("**ℹ️ About**")
    st.write(
        "Saathi is a companion, not a substitute for real medical care or "
        "family connection. In an emergency, please contact a family member, "
        "caregiver, or local emergency services directly."
    )
    st.caption("Saathi currently understands and speaks Hindi and English only.")
