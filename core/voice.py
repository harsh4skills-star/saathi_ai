"""
core/voice.py - Voice OUTPUT only. Voice INPUT is handled by the
streamlit-mic-recorder component directly in each page (it records audio
in the browser and hands us raw bytes, which we send to Groq Whisper via
core.llm.transcribe_audio).

Why speech OUTPUT is done this way:
Python on the server has no access to the elder's speakers - only the
browser does. So "speaking" a reply means running JavaScript in the
USER's browser via the Web Speech API's speechSynthesis object. This is
the same class of approach v2 attempted; the difference here is it is a
single one-way call (Python -> browser: "say this text"), not a fragile
two-way bridge, which keeps it reliable.

Known limitation to tell the user honestly: speechSynthesis voice quality
and available Hindi voices vary by browser/OS. Chrome on Android/Windows
generally has the best Hindi voice support; Safari/iOS is weaker. This is
a browser limitation, not something we can fix in code.

Known bug this version fixes: most browsers block audio that is played
automatically without a direct user action ("autoplay policy"). Because
each reply is rendered in its own fresh iframe (via components.html),
the automatic speak() call can be silently blocked even though no error
is shown anywhere - it just looks like "voice doesn't work". The fix:
always show a visible "Tap to hear this" button too - a real button
click is a genuine user gesture and reliably bypasses autoplay blocking,
even on the browsers/devices where the automatic attempt fails.

Known bug this version ALSO fixes ("Hindi gets read in Spanish"):
pickVoice() used to return null when no voice's `lang` matched "hi-IN"
(or "en-IN") on the device, and the caller did `if (voice) utter.voice =
voice`, i.e. left utter.voice completely unset when nothing matched.
Per spec, setting utter.lang alone SHOULD be enough for the browser to
pick a matching system voice - but in practice, several Chrome/Windows/
Android builds ignore utter.lang when utter.voice is unset and just use
the engine's absolute default voice instead, whatever language that
happens to be (commonly a Spanish or US-English voice, depending on the
OS locale/install) - so Hindi text got read aloud in a completely
unrelated voice with no error shown. The fix: pickVoice() now always
returns a real, explicit voice (exact match -> same-language match ->
name-keyword match -> English as a last resort for Hindi -> the
engine's own flagged default voice), and reports via the status text
whenever it had to fall back, instead of silently guessing.
"""
import json
import re
import streamlit.components.v1 as components

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def detect_speech_lang(text: str) -> str:
    """
    Picks which browser voice (hi-IN or en-IN) a reply should be spoken
    with, based on the script the reply is actually written in.

    Bug this fixes: chat.py used to always speak every reply with a single
    voice fixed once in Settings ("speech_lang"). But the companion's reply
    language changes turn-to-turn (auto/Hinglish mode mixes Hindi and
    English by design - see core/prompts.py), so about half of all replies
    were being read aloud in the wrong voice: English text spoken with the
    Hindi voice (or vice versa) sounds garbled/wrong. This detects the
    actual language of each reply instead of trusting a static setting.

    Why script (Devanagari vs Latin) and not a language-detection library:
    it needs zero new dependencies, is instant, and is reliable here
    specifically because core/prompts.py's LANGUAGE_DIRECTIVES require the
    model to write Hindi in Devanagari script (never Romanized Hindi) - so
    "does this text contain Devanagari characters" is a solid signal in
    this app, even though it wouldn't be a general-purpose approach.
    """
    if not text:
        return "en-IN"
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return "en-IN"
    devanagari_ratio = len(_DEVANAGARI_RE.findall(text)) / len(letters)
    # Low threshold on purpose: en-IN browser voices generally cannot
    # pronounce Devanagari text at all (they skip or garble it), while
    # hi-IN voices handle occasional English loanwords fine. So even a
    # reply that's mostly English with a meaningful Hindi clause is safer
    # spoken with the Hindi voice than the other way around.
    return "hi-IN" if devanagari_ratio > 0.15 else "en-IN"


def speak(text: str, lang: str = "hi-IN", rate: float = 0.9):
    """
    Speaks `text` aloud in the user's browser, and always shows a manual
    "Tap to hear this" button as a reliable fallback (see module docstring
    for why the automatic attempt alone is not trustworthy).
    lang: BCP-47 language tag - "hi-IN" for Hindi, "en-IN" for Indian English.
    rate: speaking speed, 0.6 (slow) - 1.3 (fast). Configurable from
    Settings, since a comfortable pace varies a lot person to person.
    """
    rate = max(0.5, min(1.5, float(rate)))
    safe_text = json.dumps(text)
    components.html(
        f"""
        <div style="font-family:sans-serif;">
          <button id="speakBtn" onclick="speakNow()"
            style="background:#D97706;color:white;border:none;border-radius:8px;
                   padding:8px 16px;font-size:15px;cursor:pointer;">
            🔊 Tap to hear this
          </button>
          <span id="speakStatus" style="margin-left:8px;color:#888;font-size:13px;"></span>
        </div>
        <script>
        const TEXT = {safe_text};
        const LANG = "{lang}";
        const RATE = {rate};

        function pickVoice() {{
            const voices = window.speechSynthesis.getVoices();
            const target = LANG.toLowerCase();          // e.g. "hi-in"
            const prefix = target.split("-")[0];        // e.g. "hi"

            // 1. Exact BCP-47 match ("hi-IN")
            let voice = voices.find(v => v.lang.toLowerCase() === target);
            if (voice) return {{ voice, note: null }};

            // 2. Same language, any region ("hi-*" or just "hi")
            voice = voices.find(v => v.lang.toLowerCase().startsWith(prefix));
            if (voice) return {{ voice, note: null }};

            // 3. Name-based match - some engines mislabel `lang` but the
            // voice's name says the language clearly (e.g. "Google हिन्दी",
            // "Microsoft Heera - Hindi (India)").
            const nameKeywords = prefix === "hi"
                ? ["hindi", "हिन्द"]
                : ["india", "indian"];
            voice = voices.find(v => nameKeywords.some(k => v.name.toLowerCase().includes(k)));
            if (voice) return {{ voice, note: null }};

            // 4. For Hindi specifically: never silently fall through to
            // whatever the engine's default happens to be (that's the
            // "reads as Spanish" bug) - prefer an English voice instead,
            // since it's at least a known, predictable fallback, and say
            // so out loud in the status line.
            if (prefix === "hi") {{
                voice = voices.find(v => v.lang.toLowerCase().startsWith("en"));
                if (voice) return {{ voice, note: "Hindi voice not installed on this device - using " + voice.name + " instead." }};
            }}

            // 5. Absolute last resort: the engine's own flagged default
            // voice (or simply the first one) - always explicit, never
            // left for the browser to silently decide on its own.
            voice = voices.find(v => v.default) || voices[0] || null;
            if (voice) {{
                return {{ voice, note: "No " + LANG + " voice found - using " + voice.name + " instead." }};
            }}
            return {{ voice: null, note: "No voices available on this device." }};
        }}

        function speakNow() {{
            const status = document.getElementById("speakStatus");
            try {{
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(TEXT);
                utter.lang = LANG;
                utter.rate = RATE;
                const {{ voice, note }} = pickVoice();
                if (voice) utter.voice = voice;  // always explicit - never left unset
                utter.onerror = (e) => {{ status.innerText = "Could not play audio."; }};
                utter.onstart = () => {{ status.innerText = note || "Speaking..."; }};
                utter.onend = () => {{ status.innerText = ""; }};
                window.speechSynthesis.speak(utter);
            }} catch (e) {{
                status.innerText = "Voice not supported in this browser.";
            }}
        }}

        // Try automatically once voices are ready (works on some browsers/
        // devices; the button above is the guaranteed path on the rest).
        if (window.speechSynthesis.getVoices().length > 0) {{
            speakNow();
        }} else {{
            window.speechSynthesis.onvoiceschanged = () => speakNow();
        }}
        </script>
        """,
        height=45,
    )
