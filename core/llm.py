"""
core/llm.py

Thin wrapper around the Groq SDK. Deliberately NOT using LangChain -
this is the entire chat + transcription integration in ~40 lines,
and every line here is something you can read, run, and modify.
"""
import os
import time
from groq import Groq

_client = None


def get_client() -> Groq:
    """Lazily create a single shared Groq client for the app session."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Copy .env.example to .env and add your "
                "free key from https://console.groq.com"
            )
        _client = Groq(api_key=api_key)
    return _client


def chat(
    messages: list[dict],
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
    max_retries: int = 2,
) -> str:
    """
    messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
    Returns the assistant's reply text as a plain string.

    Retries on transient failures (network blips, rate limits, 5xx from
    Groq) up to `max_retries` times with a short backoff, before giving up.
    Bug this fixes: previously a single dropped connection surfaced
    straight to the user as "Sorry, I had trouble reaching the AI
    service" - for elderly users on flaky wifi/mobile data, that meant
    conversations failing on transient issues that a simple retry would
    have recovered from silently. Does NOT retry on non-transient errors
    (bad API key, invalid request) - those fail immediately since retrying
    won't help.
    """
    client = get_client()
    delay = 1.0
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            status_code = getattr(e, "status_code", None)
            # Don't retry auth/bad-request errors (401/400/404) - a retry
            # will just fail the same way. Do retry everything else
            # (network errors have no status_code at all, rate limits are
            # 429, server errors are 5xx).
            if status_code is not None and status_code < 429:
                raise
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise last_error


def transcribe_audio(audio_bytes: bytes, filename: str = "recording.wav", language: str | None = None) -> str:
    """
    Sends recorded audio to Groq's hosted Whisper model for speech-to-text.
    This is what makes voice INPUT work: the browser only ever records audio
    (via streamlit-mic-recorder) - all transcription happens here, server-side,
    via Groq's free-tier Whisper endpoint. No local speech-recognition
    libraries or microphone access from Python are needed.

    language: optional ISO-639-1 hint ("hi" or "en"). Without this, Whisper
    auto-detects the spoken language, which is where a lot of "Hindi speech
    coming out garbled/wrong" reports come from - auto-detect occasionally
    mis-guesses the language on short or accented clips. Passing an explicit
    hint (set from the user's language preference in Settings) fixes that
    for the common case; leave it None to keep the old auto-detect behavior.
    """
    client = get_client()
    kwargs = {
        "file": (filename, audio_bytes),
        "model": "whisper-large-v3-turbo",
        "response_format": "text",
    }
    if language:
        kwargs["language"] = language
    result = client.audio.transcriptions.create(**kwargs)
    return str(result).strip()
