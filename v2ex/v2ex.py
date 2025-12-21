from curl_cffi import requests
import re
import os
from datetime import datetime, timedelta
import sys
from dotenv import load_dotenv
from telegram.notify import send_tg_notification

load_dotenv()

cookie = os.environ.get('V2EX_COOKIE', '').strip()
# Initial the message time
time = datetime.now() + timedelta(hours=8)
message = time.strftime("%Y/%m/%d %H:%M:%S") + " from V2EX \n"
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "referer": "https://www.v2ex.com/mission/daily",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "cookie": cookie,
}

def get_once() -> tuple[str, bool]:
    """get the once number and whether signed
    
    Returns:
        tuple: the once number and whether signed
    """
    global message
    url = "https://www.v2ex.com/mission/daily"
    res = requests.get(url, headers=headers)
    content = res.text
    
    reg1 = r"需要先登录"
    if re.search(reg1, content):
        message += "The cookie is overdated."
        return None, False
    else:
        reg = r"每日登录奖励已领取"
        if re.search(reg, content):
            message += "You have already signed today.\n"
            return None, True
        else:
            reg = r"redeem\?once=(.*?)'"
            once_match = re.search(reg, content)
            if once_match:
                once = once_match.group(1)
                message += f"Successfully get once {once}\n"
                return once, False
            else:
                message += "Have not signed, but fail to get once\n"
                return None, False

def check_in(once: str) -> bool:
    """check in and return whether success
    
    Args:
        once: the once number
        
    Returns:
        bool: whether success
    """
    global message
    url = f"https://www.v2ex.com/mission/daily/redeem?once={once}"
    res = requests.get(url, headers=headers)
    content = res.text
    
    reg = r"已成功领取每日登录奖励"
    if re.search(reg, content):
        message += "Check in successfully\n"
        send_tg_notification(message)
        return True
    else:
        message += "Fail to check in\n"
        return False

# query the balance
def balance() -> tuple[str, str]:
    """query the balance and return the time and balance
    
    Returns:
        tuple: the time and balance
    """
    url = "https://www.v2ex.com/balance"
    res = requests.get(url, headers=headers)
    content = res.text
    # print(content)
    pattern = r'每日登录奖励.*?<small class="gray">(.*?)</small>.*?<td class="d" style="text-align: right;">.*?</td>.*?<td class="d" style="text-align: right;">(.*?)</td>'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        time = match.group(1).strip()
        balance = match.group(2).strip()
        return time, balance
    else:
        return None, None
        

if __name__ == "__main__":
    try:
        if not cookie:
            raise ValueError("Environment variable V2EX_COOKIE is not set")
        
        # get the once number and whether signed
        once, signed = get_once()

        # check in
        if once and not signed:
            success = check_in(once)
            if not success:
                raise ValueError("Fail to check in")
            time, balance = balance()
            if not time or not balance:
                raise ValueError("Fail to get balance")
        else:
            message += "FAIL.\n"
            send_tg_notification(message)
            raise ValueError("Fail to check in")
    except Exception as err:
        print(err, flush=True)
        sys.exit(1)
