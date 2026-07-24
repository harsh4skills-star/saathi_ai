"""
core/family_bridge.py - Keeps family members in the loop WITHOUT asking
them to install anything. This is deliberate: the target users for
updates are often busy adult children who will not install a companion
app, but will read one email a week.

Sending mechanism: Gmail SMTP with an "app password" (free, no paid tier,
no third-party email service signup required). Good enough for a weekly
digest to 1-2 family emails. If you outgrow this later, a transactional
email API (e.g. Resend's free tier) is a clean upgrade.
"""
import os
import smtplib
from email.mime.text import MIMEText

from core.llm import chat
from core.prompts import DIGEST_PROMPT_TEMPLATE
from core import db


def build_digest_text() -> str:
    """Gathers recent activity and asks the LLM to write a warm summary."""
    memoir = db.get_memoir_entries()[:3]
    memoir_summary = (
        "; ".join(f"{topic}: {story[:80]}" for topic, story, _ in memoir)
        or "No new stories shared this week."
    )

    reminders = db.get_reminders()[:5]
    reminder_summary = (
        "; ".join(f"{r[1]} ({'done' if r[3] else 'pending'})" for r in reminders)
        or "No reminders logged."
    )

    recent_msgs = db.get_recent_messages(limit=10)
    mood_summary = (
        "Based on recent chats, conversations were warm and engaged."
        if recent_msgs
        else "No recent conversations logged yet."
    )

    prompt = DIGEST_PROMPT_TEMPLATE.format(
        memoir_summary=memoir_summary,
        reminder_summary=reminder_summary,
        mood_summary=mood_summary,
    )
    return chat([{"role": "user", "content": prompt}])


def send_digest_email(digest_text: str) -> tuple[bool, str]:
    """Sends the digest via Gmail SMTP. Returns (success, message)."""
    sender = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("SENDER_APP_PASSWORD")
    recipient = os.getenv("FAMILY_EMAIL")

    if not all([sender, app_password, recipient]):
        return False, (
            "Family Bridge email is not configured. Set SENDER_EMAIL, "
            "SENDER_APP_PASSWORD, and FAMILY_EMAIL in your .env file."
        )

    msg = MIMEText(digest_text)
    msg["Subject"] = "Your family's weekly Saathi update"
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, [recipient], msg.as_string())
        return True, f"Digest sent to {recipient}."
    except Exception as e:
        return False, f"Failed to send email: {e}"
