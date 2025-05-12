import os
import re
import http.client
import urllib.parse
from datetime import datetime
import ssl

# cookies
COOKIES = os.getenv("V2EX_COOKIES")

# 创建 SSL 上下文
SSL_CONTEXT = ssl.create_default_context()

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,ja;q=0.7,zh-TW;q=0.6",
    "Cookie": COOKIES,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

def make_request(method, url, headers=None):
    """发送 HTTP 请求并返回响应内容"""
    parsed_url = urllib.parse.urlparse(url)
    
    if parsed_url.scheme == 'https':
        conn = http.client.HTTPSConnection(parsed_url.netloc, context=SSL_CONTEXT)
    else:
        conn = http.client.HTTPConnection(parsed_url.netloc)
    
    path = parsed_url.path
    if parsed_url.query:
        path += '?' + parsed_url.query
    
    conn.request(method, path, headers=headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    conn.close()
    
    return data

def get_once():
    url = "https://www.v2ex.com/mission/daily"
    response_text = make_request("GET", url, HEADERS)

    if "你要查看的页面需要先登录" in response_text:
        raise Exception("登录失败，Cookie 可能已经失效")
    elif "每日登录奖励已领取" in response_text:
        return "", True

    match = re.search(r"once=(\d+)", response_text)
    if match:
        return match.group(1), True
    return "", False

def check_in(once):
    url = f"https://www.v2ex.com/mission/daily/redeem?once={once}"
    make_request("GET", url, HEADERS)

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
            print("V2EX 签到成功")
            return
        print("V2EX 签到已完成")
    except Exception as e:
        print(f"V2EX 签到失败: {str(e)}")
        raise

if __name__ == '__main__':
    main()