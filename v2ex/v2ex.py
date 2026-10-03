from curl_cffi import requests
import re
import os
import sys
from dotenv import load_dotenv
from telegram.notify import send_source_notification

load_dotenv()

cookie = os.environ.get('V2EX_COOKIE', '').strip()
message = ""
# Let curl_cffi supply a consistent browser fingerprint and headers: hand-written
# sec-ch-ua/user-agent values that disagree with the TLS fingerprint get a
# Cloudflare challenge (403) on /mission/daily.
IMPERSONATE = "chrome"
headers = {
    "referer": "https://www.v2ex.com/mission/daily",
    "cookie": cookie,
}

def get_once() -> tuple[str, bool]:
    """get the once number and whether signed
    
    Returns:
        tuple: the once number and whether signed
    """
    global message
    url = "https://www.v2ex.com/mission/daily"
    res = requests.get(url, headers=headers, impersonate=IMPERSONATE)
    content = res.text
    
    reg1 = r"需要先登录"
    if re.search(reg1, content):
        message += "The cookie is expired.\n"
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
                message += "Check-in token acquired.\n"
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
    res = requests.get(url, headers=headers, impersonate=IMPERSONATE)
    content = res.text
    
    reg = r"已成功领取每日登录奖励"
    if re.search(reg, content):
        message += "Check in successfully\n"
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
    res = requests.get(url, headers=headers, impersonate=IMPERSONATE)
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
    exit_code = 0
    try:
        if not cookie:
            raise ValueError("Environment variable V2EX_COOKIE is not set")
        
        # get the once number and whether signed
        once, signed = get_once()

        # check in
        if signed:
            reward_time, current_balance = balance()
            if reward_time and current_balance:
                message += f"Latest reward: {reward_time}\nBalance: {current_balance}\n"
        elif once:
            success = check_in(once)
            if not success:
                raise ValueError("Fail to check in")
            reward_time, current_balance = balance()
            if not reward_time or not current_balance:
                raise ValueError("Fail to get balance")
            message += f"Latest reward: {reward_time}\nBalance: {current_balance}\n"
        else:
            raise ValueError("Fail to check in")
    except Exception as err:
        print(err, flush=True)
        message += f"Error: {err}\n"
        exit_code = 1
    finally:
        send_source_notification("V2EX", message)

    sys.exit(exit_code)
