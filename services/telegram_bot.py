import os

import requests


def send_msg(text: str) -> None:
    """Send a plain-text message to a Telegram chat.

    Reads ``TELEGRAM_TOKEN`` and ``TELEGRAM_CHAT_ID`` from the environment.
    Silently logs a warning if either variable is missing or the request fails,
    so that a misconfigured Telegram integration never crashes the bot.

    Parameters
    ----------
    text:
        Message body to deliver.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[WARN] TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set — skipping notification")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        print(f"[WARN] Failed to send Telegram message: {exc}")
