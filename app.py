"""
Elder AI Companion (Saathi) - Main Entry Point / Router

This file no longer contains any page content - it only sets up
navigation. Page icons and titles are passed here as plain Python
strings (st.Page(..., icon="...")), NOT baked into filenames. That
matters: a previous version put emoji directly in filenames like
"1_Chat.py" -> caused corrupted filenames when zip files were
extracted on some Windows setups, which broke navigation entirely.
Icons-as-strings-in-code are immune to that class of bug, because
Python source files are read as UTF-8 regardless of platform.
"""
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# --- Startup guard -----------------------------------------------------
# This app defines navigation entirely via st.Page("views/....py", ...)
# below. It does NOT use a pages/ directory or st.switch_page("pages/...")
# anywhere. If Streamlit still complains about a missing "pages/..."
# file, that error is not coming from this app.py — it's coming from
# stray files left behind by an older project layout (e.g. a leftover
# pages/ folder from a previous version) or this script being launched
# from the wrong working directory. Fail loudly and specifically here
# instead of letting Streamlit raise its generic StreamlitAPIException.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_STRAY_PAGES_DIR = os.path.join(_APP_DIR, "pages")

if os.path.isdir(_STRAY_PAGES_DIR):
    st.set_page_config(page_title="Saathi - Startup Error", layout="centered")
    st.error(
        "Found a leftover **pages/** folder next to app.py:\n\n"
        f"`{_STRAY_PAGES_DIR}`\n\n"
        "This project defines navigation entirely in code via "
        "st.Page(\"views/....py\", ...) in app.py — it does not use a "
        "pages/ directory. A pages/ folder sitting alongside app.py is a "
        "leftover from an older project version and can conflict with "
        "Streamlit's page routing, including references to files like "
        "1_Chat.py that no longer exist in this codebase.\n\n"
        "Fix: delete or rename that pages/ folder, then rerun "
        "`streamlit run app.py`. See cleanup_stale_pages.py in this "
        "project for an automated check."
    )
    st.stop()

_expected_views = os.path.join(_APP_DIR, "views")
if not os.path.isdir(_expected_views):
    st.set_page_config(page_title="Saathi - Startup Error", layout="centered")
    st.error(
        f"Expected a views/ folder next to app.py at:\n\n`{_expected_views}`\n\n"
        f"but it wasn't found. app.py is running from:\n\n`{_APP_DIR}`\n\n"
        "This usually means Streamlit was launched from the wrong "
        "directory, or app.py is a stray copy outside the real project "
        "folder. cd into the actual project root (the one containing "
        "this app.py and a views/ folder) and rerun "
        "`streamlit run app.py`."
    )
    st.stop()
# -------------------------------------------------------------------

from core.db import init_db
from core.ui import apply_theme

init_db()

st.set_page_config(
    page_title="Saathi - Your AI Companion",
    page_icon=":orange_heart:",
    layout="centered",
    initial_sidebar_state="expanded",
)
apply_theme()

home = st.Page("views/home.py", title="Home", icon="🏠", default=True)
chat = st.Page("views/chat.py", title="Chat", icon="💬")
reminders = st.Page("views/reminders.py", title="Reminders", icon="⏰")
memories = st.Page("views/memories.py", title="Memories", icon="🧠")
memoir = st.Page("views/memoir.py", title="Memoir", icon="📖")
games = st.Page("views/games.py", title="Games", icon="🎮")
family_bridge = st.Page("views/family_bridge.py", title="Family Bridge", icon="👨‍👩‍👧")
settings = st.Page("views/settings.py", title="Settings", icon="⚙️")

pg = st.navigation([home, chat, reminders, memories, memoir, games, family_bridge, settings])
pg.run()
