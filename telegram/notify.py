import http.client
import urllib.parse
import json
import os
import sys

# follow the instructions from https://core.telegram.org/bots/features#botfather and get the bot token
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN').strip()
# add the bot to your contact and send a message to it
# then check the url https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates to get the chat id
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID').strip()

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
    send_tg_notification("Action test")