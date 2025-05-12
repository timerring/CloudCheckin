import os
import re
from datetime import datetime
import requests

# cookies
COOKIES = os.getenv("V2EX_COOKIES")
SESSION = requests.Session()

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,ja;q=0.7,zh-TW;q=0.6",
    "Cookie": COOKIES,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

def get_once():
    url = "https://www.v2ex.com/mission/daily"
    r = SESSION.get(url, headers=HEADERS)

    if "你要查看的页面需要先登录" in r.text:
        raise Exception("登录失败，Cookie 可能已经失效")
    elif "每日登录奖励已领取" in r.text:
        return "", True

    match = re.search(r"once=(\d+)", r.text)
    if match:
        return match.group(1), True
    return "", False

def check_in(once):
    url = "https://www.v2ex.com/mission/daily/redeem?once=" + once
    SESSION.get(url, headers=HEADERS)

def main():
    try:
        once, success = get_once()
        if once:
            check_in(once)
        if success:
            # 确保 logs 目录存在
            os.makedirs('logs', exist_ok=True)
            # 记录成功日志
            with open('logs/v2ex.log', 'a') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d')} v2ex 签到成功\n")
            return
    except Exception as e:
        raise Exception(f"V2EX 签到失败: {str(e)}")

if __name__ == '__main__':
    main()