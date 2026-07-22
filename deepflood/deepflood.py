import os
from curl_cffi import requests
import random
import time
from dotenv import load_dotenv
from telegram.notify import send_source_notification

load_dotenv()

# Get COOKIE from environment variable, multiple cookies separated by &
cookies = os.environ.get('DEEPFLOOD_COOKIE', '').strip()

# Split multiple cookies by & to form a list
cookie_list = cookies.split('&')

# Request headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Origin': 'https://www.deepflood.com',
    'Referer': 'https://www.deepflood.com/board',
    'Content-Type': 'application/json',
}


def main():
    results = []
    failed = False

    if not cookies:
        results.append("Configuration error: DEEPFLOOD_COOKIE is not set")
        send_source_notification("DEEPFLOOD", results)
        return 1

    for idx, cookie in enumerate(cookie_list):
        account = idx + 1
        print(f"Using account {account} for check-in...", flush=True)
        random_delay = random.randint(1, 20)
        print(f"Account {account} will wait for {random_delay} seconds...", flush=True)
        time.sleep(random_delay)
        headers['Cookie'] = cookie.strip()

        try:
            url = 'https://www.deepflood.com/api/attendance?random=true'
            response = requests.post(url, headers=headers, impersonate="chrome136")
            print(f"Account {account} status code: {response.status_code}", flush=True)
            print(f"Account {account} response: {response.text}", flush=True)

            if response.status_code == 200:
                result = f"Account {account}: check-in successful"
            else:
                result = f"Account {account}: check-in failed — {response.text}"
                failed = True
        except Exception as exc:
            result = f"Account {account}: check-in error — {exc}"
            failed = True

        print(result, flush=True)
        results.append(result)

    send_source_notification("DEEPFLOOD", results)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
