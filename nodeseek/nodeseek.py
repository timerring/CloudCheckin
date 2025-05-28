import sys
import os
from curl_cffi import requests
import random
import time
from telegram.notify import send_tg_notification

# Get COOKIE from environment variable, multiple cookies separated by &
cookies = os.environ.get('NODESEEK_COOKIE').strip()

if not cookies:
    raise ValueError("Environment variable NODESEEK_COOKIE is not set")
    sys.exit(1)

# Split multiple cookies by & to form a list
cookie_list = cookies.split('&')

# Request headers
headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Content-Length': '0',
    'Origin': 'https://www.nodeseek.com',
    'Referer': 'https://www.nodeseek.com/board',
    'Sec-CH-UA': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'Sec-CH-UA-Mobile': '?0',
    'Sec-CH-UA-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
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
        url = 'https://www.nodeseek.com/api/attendance?random=true'
        response = requests.post(url, headers=headers, impersonate="chrome110")
        
        # Output the status code and response content
        print(f"The {idx+1} account's Status Code: {response.status_code}", flush=True)
        print(f"The {idx+1} account's Response Content: {response.text}", flush=True)
        
        # Check if the check-in is successful based on the response content
        if response.status_code == 200:
            success_message = f"NODESEEK account {idx+1} check-in successful"
            print(success_message, flush=True)
            send_tg_notification(success_message)
        else:
            fail_message = f"NODESEEK account {idx+1} check-in failed, response content: {response.text}"
            print(fail_message, flush=True)
            send_tg_notification(fail_message)
            sys.exit(1)
    
    except Exception as e:
        error_message = f"NODESEEK account {idx+1} check-in process error: {e}"
        print(error_message, flush=True)
        send_tg_notification(error_message)
        sys.exit(1)