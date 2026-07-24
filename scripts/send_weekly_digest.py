"""
scripts/send_weekly_digest.py

Why this file exists: Streamlit Community Cloud only runs your app when
someone visits it - it cannot run a background job on a schedule by
itself. This script is meant to be triggered on a schedule by GitHub
Actions (free, see ../.github/workflows/weekly_digest.yml) so the family
digest goes out even if nobody opens the app that week.

It reuses the exact same core/ code as the app - no duplicated logic.
Run manually with: python scripts/send_weekly_digest.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from core.family_bridge import build_digest_text, send_digest_email

if __name__ == "__main__":
    digest = build_digest_text()
    success, message = send_digest_email(digest)
    print(message)
    if not success:
        sys.exit(1)
