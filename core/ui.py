"""
core/ui.py - Shared visual design system for Saathi.

Everything here is presentation-only. No page in this file talks to the
database, the LLM, or any other backend service - it only renders things
that other pages hand it (numbers, strings, callbacks). That separation is
intentional: it means the redesign could be swapped out again later without
touching a single line of business logic in core/db.py, core/llm.py, etc.

Design tokens (colors, radii, shadows) live in one place (`apply_theme`)
so every card, button and chat bubble stays visually consistent.
"""
import os
import html as _html
import streamlit as st

# ---------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------
COLORS = {
    "bg": "#F8FAFC",
    "primary": "#FF8C42",
    "primary_dark": "#E96F1F",
    "secondary": "#4F9DA6",
    "success": "#4CAF50",
    "warning": "#F9C74F",
    "danger": "#EF5350",
    "card": "#FFFFFF",
    "text": "#1F2937",
    "subtext": "#6B7280",
}


def require_groq_key():
    """
    Call at the top of any page that talks to the LLM. Without this,
    a missing key produces a raw Python traceback instead of a message
    the user can actually act on.
    """
    if not os.getenv("GROQ_API_KEY"):
        st.error(
            "No Groq API key found. Copy .env.example to .env, add your "
            "free key from console.groq.com, then restart the app."
        )
        st.stop()


def _esc(s: str) -> str:
    """Escape text that gets interpolated into raw HTML strings below."""
    return _html.escape(str(s), quote=True)


# ---------------------------------------------------------------------
# Global theme (fonts, colors, buttons, cards, chat, sidebar, animation)
# ---------------------------------------------------------------------
def apply_theme():
    c = COLORS
    large_text = st.session_state.get("large_text", False)
    scale = 1.18 if large_text else 1.0
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

        :root {{
            --saathi-bg: {c['bg']};
            --saathi-primary: {c['primary']};
            --saathi-primary-dark: {c['primary_dark']};
            --saathi-secondary: {c['secondary']};
            --saathi-success: {c['success']};
            --saathi-warning: {c['warning']};
            --saathi-danger: {c['danger']};
            --saathi-card: {c['card']};
            --saathi-text: {c['text']};
            --saathi-subtext: {c['subtext']};
            --saathi-radius: 20px;
            --saathi-shadow: 0 2px 10px rgba(31,41,55,0.06), 0 8px 24px rgba(31,41,55,0.05);
            --saathi-shadow-hover: 0 12px 28px rgba(255,140,66,0.20);
        }}

        html, body, [class*="css"], .stApp {{
            font-family: 'Inter', -apple-system, sans-serif;
            color: var(--saathi-text);
        }}
        .stApp {{ background: var(--saathi-bg); }}

        h1, h2, h3, .saathi-heading {{
            font-family: 'Poppins', 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em;
            color: var(--saathi-text) !important;
        }}
        h1 {{ font-size: {2.1 * scale:.2f}rem !important; }}
        h2 {{ font-size: {1.5 * scale:.2f}rem !important; }}
        h3 {{ font-size: {1.2 * scale:.2f}rem !important; }}
        .stMarkdown, .stText, p, li {{ font-size: {17 * scale:.0f}px !important; line-height: 1.55; }}
        [data-testid="stCaptionContainer"] {{ color: var(--saathi-subtext) !important; font-size: {15 * scale:.0f}px !important; }}

        /* Hide default Streamlit chrome that doesn't fit a premium feel */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        .block-container {{ padding-top: 2rem !important; max-width: 900px; }}

        /* ---------------- Buttons ---------------- */
        .stButton > button, .stFormSubmitButton > button {{
            font-family: 'Inter', sans-serif;
            font-size: {16 * scale:.0f}px !important;
            font-weight: 700 !important;
            padding: 0.7rem 1.4rem !important;
            border-radius: 16px !important;
            min-height: 56px;
            border: none !important;
            background: linear-gradient(135deg, var(--saathi-primary), var(--saathi-primary-dark)) !important;
            color: white !important;
            box-shadow: 0 6px 16px rgba(255,140,66,0.28);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--saathi-shadow-hover);
            color: white !important;
        }}
        .stButton > button:active {{ transform: translateY(0px); }}
        .stButton > button[kind="secondary"], button[data-testid="stBaseButton-secondary"] {{
            background: white !important;
            color: var(--saathi-primary-dark) !important;
            border: 2px solid #FFE1C7 !important;
            box-shadow: var(--saathi-shadow);
        }}
        [data-testid="stSidebar"] .stButton > button {{
            font-size: 15px !important;
            min-height: 44px;
            padding: 0.4rem 0.9rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
            background: transparent !important;
            color: var(--saathi-text) !important;
            box-shadow: none !important;
            border: none !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            background: #FFF1E5 !important;
            color: var(--saathi-primary-dark) !important;
            transform: none;
        }}

        /* ---------------- Inputs ---------------- */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
            font-size: {17 * scale:.0f}px !important;
            border-radius: 14px !important;
        }}
        [data-testid="stChatInput"] {{ border-radius: 20px !important; }}
        [data-testid="stChatInput"] textarea {{ font-size: {17 * scale:.0f}px !important; }}

        /* ---------------- Cards: any st.container(border=True) ---------------- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: var(--saathi-radius) !important;
            border: 1px solid #EEF2F6 !important;
            background: var(--saathi-card);
            box-shadow: var(--saathi-shadow);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            animation: saathiFadeUp 0.35s ease;
        }}
        [data-testid="stVerticalBlockBorderWrapper"]:hover {{
            transform: translateY(-3px);
            box-shadow: var(--saathi-shadow-hover);
        }}

        @keyframes saathiFadeUp {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}

        /* ---------------- Chat ---------------- */
        [data-testid="stChatMessage"] {{
            font-size: {18 * scale:.0f}px !important;
            border-radius: 20px !important;
            padding: 0.9rem 1.1rem !important;
            box-shadow: var(--saathi-shadow);
            animation: saathiFadeUp 0.25s ease;
            border: 1px solid #F1F5F9;
        }}
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
            background: #FFF3E8;
        }}
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            background: #EAF6F6;
        }}

        /* ---------------- Sidebar ---------------- */
        [data-testid="stSidebar"] {{
            background: #FFFFFF;
            font-size: 15px !important;
            border-right: 1px solid #EEF2F6;
        }}
        [data-testid="stSidebarNav"] a {{
            font-size: 16px !important;
            font-weight: 600;
            padding: 0.6rem 0.9rem !important;
            border-radius: 14px !important;
            margin: 2px 6px;
        }}
        [data-testid="stSidebarNav"] a:hover {{
            background: #FFF1E5 !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: linear-gradient(135deg, var(--saathi-primary), var(--saathi-primary-dark)) !important;
            color: white !important;
            box-shadow: 0 4px 10px rgba(255,140,66,0.3);
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] span {{ color: white !important; }}

        /* ---------------- Misc ---------------- */
        [data-testid="stAlert"] {{ border-radius: 16px !important; }}
        hr {{ border-color: #EEF2F6 !important; }}

        .saathi-pill {{
            display: inline-block;
            padding: 0.2rem 0.7rem;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Reusable visual components
# ---------------------------------------------------------------------
def hero_section(greeting: str, subtitle: str):
    """Warm welcome banner used at the top of the Home dashboard."""
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#FFF3E8,#EAF6F6);
                    border-radius:24px;padding:2.2rem 2rem;margin-bottom:1.5rem;
                    text-align:center;box-shadow:0 8px 24px rgba(31,41,55,0.06);
                    animation: saathiFadeUp 0.4s ease;">
            <div style="font-size:2.6rem;">❤️</div>
            <div style="font-family:'Poppins',sans-serif;font-weight:700;
                        font-size:2rem;color:{COLORS['text']};margin-top:0.3rem;">
                {_esc(greeting)}
            </div>
            <div style="font-size:1.15rem;color:{COLORS['subtext']};
                        max-width:520px;margin:0.5rem auto 0;">
                {_esc(subtitle)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


MOOD_OPTIONS = [("😊", "Great"), ("🙂", "Okay"), ("😐", "Fine"), ("😔", "Not good")]


def mood_selector():
    """
    'How are you feeling today?' - four large mood buttons. Purely a
    frontend touchpoint (there's no mood table in core/db.py), so the
    choice is only reflected back to the user for this session rather
    than persisted - nothing here reaches into the database.
    """
    st.markdown(
        "<div class='saathi-heading' style='font-size:1.3rem;margin-bottom:0.5rem;'>"
        "How are you feeling today?</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for col, (emoji, label) in zip(cols, MOOD_OPTIONS):
        with col:
            if st.button(f"{emoji}\n\n{label}", key=f"mood_{label}", use_container_width=True):
                st.session_state["last_mood"] = label
                st.toast(f"Thanks for sharing - noted that you're feeling {label.lower()} today.", icon=emoji)
    if st.session_state.get("last_mood"):
        st.caption(f"Today's mood: {st.session_state['last_mood']}")


def stat_card(label: str, value: str, icon: str = "", trend: str | None = None):
    """
    Dashboard summary card. Signature kept backward compatible with the
    original (label, value, icon) call sites; `trend` is new and optional.
    """
    trend_html = ""
    if trend:
        trend_html = (
            f"<div class='saathi-pill' style='background:#E9F7EF;color:{COLORS['success']};"
            f"margin-top:0.4rem;'>{_esc(trend)}</div>"
        )
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="text-align:center;padding:0.3rem 0;">
                <div style="font-size:1.9rem;">{icon}</div>
                <div style="font-size:1.7rem;font-weight:700;font-family:'Poppins',sans-serif;
                            color:{COLORS['primary_dark']};margin-top:0.1rem;">{_esc(value)}</div>
                <div style="font-size:0.95rem;color:{COLORS['subtext']};">{_esc(label)}</div>
                {trend_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def quick_action_card(icon: str, title: str, desc: str, button_label: str, key: str) -> bool:
    """A big tappable dashboard card. Returns True on the run a click happened."""
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="padding:0.2rem 0 0.6rem 0;">
                <div style="font-size:2rem;">{icon}</div>
                <div style="font-family:'Poppins',sans-serif;font-weight:700;
                            font-size:1.15rem;margin-top:0.3rem;">{_esc(title)}</div>
                <div style="color:{COLORS['subtext']};font-size:0.95rem;margin-top:0.2rem;">
                    {_esc(desc)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return st.button(button_label, key=key, use_container_width=True)


def section_header(icon: str, title: str, subtitle: str | None = None):
    sub = (
        f"<div style='color:{COLORS['subtext']};font-size:0.98rem;margin-top:0.1rem;'>{_esc(subtitle)}</div>"
        if subtitle else ""
    )
    st.markdown(
        f"""
        <div style="margin:0.4rem 0 0.9rem 0;">
            <div style="font-family:'Poppins',sans-serif;font-weight:700;font-size:1.5rem;">
                {icon} {_esc(title)}
            </div>
            {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div style="text-align:center;padding:2.5rem 1.5rem;background:white;
                    border-radius:var(--saathi-radius);border:1px dashed #F1D9BF;
                    box-shadow:var(--saathi-shadow);">
            <div style="font-size:2.4rem;">{icon}</div>
            <div style="font-family:'Poppins',sans-serif;font-weight:700;
                        font-size:1.2rem;margin-top:0.5rem;">{_esc(title)}</div>
            <div style="color:{COLORS['subtext']};margin-top:0.2rem;">{_esc(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


_PRIORITY_COLORS = {
    "high": COLORS["danger"],
    "normal": COLORS["primary"],
    "low": COLORS["secondary"],
}


def reminder_card(text: str, meta: str, priority: str = "normal"):
    """Renders the visual shell of a reminder; caller adds action buttons
    right after (inside the same st.container) so backend calls stay put."""
    border = _PRIORITY_COLORS.get(priority, COLORS["primary"])
    st.markdown(
        f"""
        <div style="display:flex;gap:0.8rem;align-items:flex-start;
                    border-left:5px solid {border};border-radius:14px;
                    background:#FFFDF9;padding:0.9rem 1rem;margin-bottom:-0.4rem;">
            <div style="font-size:1.4rem;">⏰</div>
            <div>
                <div style="font-weight:700;font-size:1.05rem;">{_esc(text)}</div>
                <div style="color:{COLORS['subtext']};font-size:0.9rem;">{_esc(meta)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def memory_card(fact: str, created_at: str):
    st.markdown(
        f"""
        <div style="display:flex;gap:0.8rem;align-items:flex-start;
                    background:white;border-radius:16px;padding:1rem 1.1rem;
                    box-shadow:var(--saathi-shadow);margin-bottom:0.7rem;
                    border:1px solid #F1F5F9;">
            <div style="font-size:1.3rem;">📌</div>
            <div>
                <div style="font-size:1.02rem;">{_esc(fact)}</div>
                <div style="color:{COLORS['subtext']};font-size:0.85rem;margin-top:0.2rem;">
                    {_esc(created_at)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str = "primary") -> str:
    color = COLORS.get(kind, COLORS["primary"])
    bg = {
        "primary": "#FFF1E5", "secondary": "#E9F5F6", "success": "#E9F7EF",
        "warning": "#FEF7E0", "danger": "#FDECEC",
    }.get(kind, "#FFF1E5")
    return f"<span class='saathi-pill' style='background:{bg};color:{color};'>{_esc(text)}</span>"
