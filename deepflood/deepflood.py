import sys
import os
from curl_cffi import requests
import random
import time
from dotenv import load_dotenv
from telegram.notify import send_tg_notification

load_dotenv()

# Get COOKIE from environment variable, multiple cookies separated by &
cookies = os.environ.get('DEEPFLOOD_COOKIE', '').strip()

if not cookies:
    raise ValueError("Environment variable DEEPFLOOD_COOKIE is not set")
    sys.exit(1)

# Split multiple cookies by & to form a list
cookie_list = cookies.split('&')

# Request headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Origin': 'https://www.deepflood.com',
    'Referer': 'https://www.deepflood.com/board',
    'Content-Type': 'application/json',
}

# Iterate over multiple account cookies for check-in
for idx, cookie in enumerate(cookie_list):

    print(f"Using the {idx+1} account for check-in...", flush=True)
    # Generate a random delay
    random_delay = random.randint(1, 20)
    print(f"The {idx+1} account will wait for {random_delay} seconds...", flush=True)
    time.sleep(random_delay)

    # Add cookie to headers
    headers['Cookie'] = cookie.strip()
    
    try:
        # random=true means get a random bonus
        url = 'https://www.deepflood.com/api/attendance?random=true'
        response = requests.post(url, headers=headers, impersonate="chrome136")
        
        # Output the status code and response content
        print(f"The {idx+1} account's Status Code: {response.status_code}", flush=True)
        print(f"The {idx+1} account's Response Content: {response.text}", flush=True)
        
        # Check if the check-in is successful based on the response content
        if response.status_code == 200:
            success_message = f"DEEPFLOOD account {idx+1} check-in successful"
            print(success_message, flush=True)
            send_tg_notification(success_message)
        else:
            fail_message = f"DEEPFLOOD account {idx+1} check-in failed, response content: {response.text}"
            print(fail_message, flush=True)
            send_tg_notification(fail_message)
            sys.exit(1)
    
    except Exception as e:
        error_message = f"DEEPFLOOD account {idx+1} check-in process error: {e}"
        print(error_message, flush=True)
        send_tg_notification(error_message)
        sys.exit(1)
