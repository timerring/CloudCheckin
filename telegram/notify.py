import http.client
import html
import urllib.parse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# follow the instructions from https://core.telegram.org/bots/features#botfather and get the bot token
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
# add the bot to your contact and send a message to it
# then check the url https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates to get the chat id
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()

BEIJING_TIMEZONE = timezone(timedelta(hours=8))
NOTIFICATION_SENT_MARKER = "/tmp/cloudcheckin-telegram-notified"
TELEGRAM_MESSAGE_LIMIT = 4000
TRUNCATION_SUFFIX = "\n... [message truncated]"
HTTP_ERROR_DETAIL_LIMIT = 240


def summarize_http_failure(status_code, response_text):
    """Return a compact, notification-safe summary of an HTTP failure."""
    text = str(response_text or "").strip()
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)

    if title_match:
        detail = html.unescape(title_match.group(1))
        detail = re.sub(r"\s+", " ", detail).strip()
    elif text.startswith("<"):
        detail = "HTML error response"
    else:
        detail = re.sub(r"\s+", " ", text).strip()

    if len(detail) > HTTP_ERROR_DETAIL_LIMIT:
        detail = detail[:HTTP_ERROR_DETAIL_LIMIT - 3].rstrip() + "..."

    summary = f"HTTP {status_code}"
    return f"{summary}: {detail}" if detail else summary


def format_source_notification(source, messages, now=None):
    """Format one compact Telegram notification for a platform run."""
    if isinstance(messages, str):
        messages = [messages]

    body = "\n".join(
        str(message).strip()
        for message in messages
        if message is not None and str(message).strip()
    )
    if not body:
        body = "No result was reported."

    timestamp = now or datetime.now(BEIJING_TIMEZONE)
    notification = (
        f"{timestamp.strftime('%Y/%m/%d %H:%M:%S')}\n{source.upper()}\n{body}"
    )
    if len(notification) > TELEGRAM_MESSAGE_LIMIT:
        notification = (
            notification[:TELEGRAM_MESSAGE_LIMIT - len(TRUNCATION_SUFFIX)]
            + TRUNCATION_SUFFIX
        )
    return notification


def send_source_notification(source, messages):
    """Send exactly one formatted notification for a platform run."""
    send_tg_notification(format_source_notification(source, messages))


def send_tg_notification(message):
    """Send Telegram notification
    
    Args:
        message: The message to send
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration is incomplete, cannot send notification", flush=True)
        sys.exit(1)
    
    # build the request parameters
    params = urllib.parse.urlencode({
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    })
    
    # create HTTPS connection
    conn = http.client.HTTPSConnection("api.telegram.org")
    
    try:
        # send GET request
        conn.request(
            "GET", 
            f"/bot{TELEGRAM_TOKEN}/sendMessage?{params}"
        )
        
        # get response
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        
        # parse JSON response
        result = json.loads(data)
        
        # handle response
        if response.status == 200 and result.get('ok'):
            print("Notification sent successfully", flush=True)
            try:
                with open(NOTIFICATION_SENT_MARKER, "a", encoding="utf-8"):
                    pass
            except OSError as marker_error:
                print(
                    f"Could not record notification delivery: {marker_error}",
                    flush=True,
                )
        else:
            print(f"Notification sent failed: {response.status} - {data}", flush=True)
            raise Exception(f"Notification sent failed: {response.status} - {data}")
            
    except Exception as e:
        print(f"Notification sending process error: {str(e)}", flush=True)
        sys.exit(1)
    finally:
        # ensure connection is closed
        conn.close()

if __name__ == "__main__":
    send_source_notification("TELEGRAM", "Action test")
