"""
GeeTest v3 验证码解决模块 (纯 HTTP 协议实现)
参考: https://github.com/ladeng07/sakura-signin

实现了 GeeTest v3 click 验证码的完整协议流程:
- gettype: 获取验证码类型
- get (get_c_s): 获取验证码配置 + 加密参数 c, s
- ajax: 第一轮交互 (模拟点击验证按钮)
- get_pic: 获取九宫格/图标验证码图片
- verify: 提交用户点击结果并验证
"""

import hashlib
import json
import math
import random
import time
from urllib.parse import urlencode, urlparse, parse_qsl

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, serialization
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15


class GeeTestCrack:
    def __init__(self, gt: str, challenge: str, mouse_path_file: str = None, referer: str = "https://openid.13a.com/"):
        self.pic_path = None
        self.s = None
        self.c = None
        self.referer = referer
        self.debug = True
        self.last_get_type = None
        self.last_get_c_s = None
        self.last_ajax = None
        self.last_pic = None
        self.last_validate = None
        self.fullpage_host = "https://api.geevisit.com"
        self.type_api_host = "https://api.geetest.com"
        self.static_host = "https://static.geetest.com"
        self.get_php_host = "https://api.geetest.com"
        self.ajax_host = "https://api.geevisit.com"
        self.session = httpx.Client(http2=True, timeout=30.0)
        self.session.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
            ),
            "Referer": self.referer,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Sec-CH-UA": '"Chromium";v="145", "Not:A-Brand";v="99"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"macOS"',
        }
        self.gt = gt
        self.challenge = challenge

        # 生成随机 AES 密钥
        self.aeskey = "".join(
            f"{int((1 + random.random()) * 65536):04x}"[1:] for _ in range(4)
        )

        # GeeTest RSA 公钥 (固定)
        public_key_pem = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDB45NNFhRGWzMFPn9I7k7IexS5
XviJR3E9Je7L/350x5d9AtwdlFH3ndXRwQwprLaptNb7fQoCebZxnhdyVl8Jr2J3
FZGSIa75GJnK4IwNaG10iyCjYDviMYymvCtZcGWSqSGdC/Bcn2UCOiHSMwgHJSrg
Bm1Zzu+l8nSOqAurgQIDAQAB
-----END PUBLIC KEY-----"""
        self.public_key = serialization.load_pem_public_key(public_key_pem.encode())
        self.enc_key = self.public_key.encrypt(self.aeskey.encode(), PKCS1v15()).hex()

        # 加载鼠标轨迹
        if mouse_path_file:
            with open(mouse_path_file, "r") as f:
                self.mouse_path = json.load(f)
        else:
            self.mouse_path = [
                ["move", 385, 313, 1724572150164, "pointermove"],
                ["move", 385, 315, 1724572150166, "pointermove"],
                ["move", 386, 315, 1724572150174, "pointermove"],
                ["move", 387, 315, 1724572150182, "pointermove"],
                ["move", 387, 316, 1724572150188, "pointermove"],
                ["move", 388, 316, 1724572150204, "pointermove"],
                ["move", 388, 317, 1724572150218, "pointermove"],
                ["down", 388, 317, 1724572150586, "pointerdown"],
                ["focus", 1724572150587],
                ["up", 388, 317, 1724572150632, "pointerup"],
            ]

    # ── 编码工具 ──────────────────────────────────────────────

    @staticmethod
    def encode(input_bytes: list) -> str:
        """GeeTest 自定义 base64 编码"""
        def get_char_from_index(index):
            char_table = (
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()"
            )
            return char_table[index] if 0 <= index < len(char_table) else "."

        def transform_value(value, bit_mask):
            result = 0
            for r in range(23, -1, -1):
                if (bit_mask >> r) & 1:
                    result = (result << 1) + ((value >> r) & 1)
            return result

        encoded_string = ""
        pad = ""
        input_length = len(input_bytes)
        for i in range(0, input_length, 3):
            chunk_length = min(3, input_length - i)
            chunk = input_bytes[i : i + chunk_length]
            if chunk_length == 3:
                value = (chunk[0] << 16) + (chunk[1] << 8) + chunk[2]
                encoded_string += (
                    get_char_from_index(transform_value(value, 7274496))
                    + get_char_from_index(transform_value(value, 9483264))
                    + get_char_from_index(transform_value(value, 19220))
                    + get_char_from_index(transform_value(value, 235))
                )
            elif chunk_length == 2:
                value = (chunk[0] << 16) + (chunk[1] << 8)
                encoded_string += (
                    get_char_from_index(transform_value(value, 7274496))
                    + get_char_from_index(transform_value(value, 9483264))
                    + get_char_from_index(transform_value(value, 19220))
                )
                pad = "."
            elif chunk_length == 1:
                value = chunk[0] << 16
                encoded_string += (
                    get_char_from_index(transform_value(value, 7274496))
                    + get_char_from_index(transform_value(value, 9483264))
                )
                pad = ".."
        return encoded_string + pad

    @staticmethod
    def md5(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    @staticmethod
    def encode_mouse_path(path: list, c: list, s: str) -> str:
        """编码鼠标轨迹为 GeeTest 格式"""

        def preprocess(path: list):
            def BFIQ(e):
                t = 32767
                if not isinstance(e, int):
                    return e
                if t < e:
                    e = t
                elif e < -t:
                    e = -t
                return round(e)

            def BGAB(e):
                t = ""
                n = 0
                while n < len(e) and not t:
                    if e[n]:
                        t = e[n][4]
                    n += 1
                if not t:
                    return e
                r = ""
                i = ["mouse", "touch", "pointer", "MSPointer"]
                for s in range(len(i)):
                    if t.startswith(i[s]):
                        r = i[s]
                _ = list(e)
                for a in range(len(_) - 1, -1, -1):
                    item = _[a]
                    etype = item[0]
                    if etype in ["move", "down", "up"]:
                        value = item[4] or ""
                        if not value.startswith(r):
                            _.pop(a)
                return _

            t = 0
            n = 0
            r = []
            s_val = 0
            if len(path) <= 0:
                return []
            o = None
            _ = None
            a = BGAB(path)
            c_len = len(a)
            for l in range(0 if c_len < 300 else c_len - 300, c_len):
                u = a[l]
                h = u[0]
                if h in ["down", "move", "up", "scroll"]:
                    if not o:
                        o = u
                    _ = u
                    r.append([h, [u[1] - t, u[2] - n], BFIQ(u[3] - s_val if s_val else s_val)])
                    t = u[1]
                    n = u[2]
                    s_val = u[3]
                elif h in ["blur", "focus", "unload"]:
                    r.append([h, BFIQ(u[1] - s_val if s_val else s_val)])
                    s_val = u[1]
            return r

        def process(prepared_path: list):
            h = {
                "move": 0, "down": 1, "up": 2, "scroll": 3,
                "focus": 4, "blur": 5, "unload": 6, "unknown": 7,
            }

            def p(e, t):
                n = bin(e)[2:]
                r = ""
                i = len(n) + 1
                while i <= t:
                    i += 1
                    r += "0"
                return r + n

            def d(e):
                t = []
                n = len(e)
                r = 0
                while r < n:
                    i = e[r]
                    s = 0
                    while True:
                        if s >= 16:
                            break
                        o = r + s + 1
                        if o >= n:
                            break
                        if e[o] != i:
                            break
                        s += 1
                    r += 1 + s
                    _ = h[i]
                    if s != 0:
                        t.append(_ | 8)
                        t.append(s - 1)
                    else:
                        t.append(_)
                a = p(n | 32768, 16)
                c = ""
                for l in range(len(t)):
                    c += p(t[l], 4)
                return a + c

            def g(e, tt):
                def temp1(e1):
                    n = len(e1)
                    r = 0
                    i = []
                    while r < n:
                        s = 1
                        o = e1[r]
                        _ = abs(o)
                        while True:
                            if n <= r + s:
                                break
                            if e1[r + s] != o:
                                break
                            if (_ >= 127) or (s >= 127):
                                break
                            s += 1
                        if s > 1:
                            i.append((49152 if o < 0 else 32768) | s << 7 | _)
                        else:
                            i.append(o)
                        r += s
                    return i

                e = temp1(e)
                r = []
                i = []

                def n(e, t):
                    return 0 if e == 0 else math.log(e) / math.log(t)

                for temp in e:
                    t = math.ceil(n(abs(temp) + 1, 16))
                    if t == 0:
                        t = 1
                    r.append(p(t - 1, 2))
                    i.append(p(abs(temp), t * 4))

                s = "".join(r)
                o = "".join(i)

                def temp2(t):
                    return t != 0 and t >> 15 != 1

                def temp3(e1):
                    n = []
                    for r in range(len(e1)):
                        if temp2(e1[r]):
                            n.append("1" if e1[r] < 0 else "0")
                    return "".join(n)

                if tt:
                    n_str = temp3(e)
                else:
                    n_str = ""
                return p(len(e) | 32768, 16) + s + o + n_str

            def u(e):
                t = ""
                n = len(e) // 6
                charset = "()*,-./0123456789:?@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz~"
                for r in range(n):
                    t += charset[int(e[6 * r : 6 * (r + 1)], 2)]
                return t

            t = []
            n = []
            r = []
            i = []
            for a in range(len(prepared_path)):
                _ = prepared_path[a]
                a_len = len(_)
                t.append(_[0])
                n.append(_[1] if a_len == 2 else _[2])
                if a_len == 3:
                    r.append(_[1][0])
                    i.append(_[1][1])
            c = d(t) + g(n, False) + g(r, True) + g(i, True)
            l = len(c)
            if l % 6 != 0:
                c += p(0, 6 - l % 6)
            return u(c)

        def postprocess(e, t, n):
            i = 0
            s = e
            o = t[0]
            _ = t[2]
            a = t[4]
            while True:
                r = n[i : i + 2]
                if not r:
                    break
                i += 2
                c = int(r, 16)
                l = chr(c)
                u = (o * c * c + _ * c + a) % len(e)
                s = s[:u] + l + s[u:]
            return s

        return postprocess(process(preprocess(path)), c, s)

    def aes_encrypt(self, content: str) -> bytes:
        cipher = Cipher(
            algorithms.AES(self.aeskey.encode()), modes.CBC(b"0000000000000000")
        )
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(content.encode()) + padder.finalize()
        return encryptor.update(padded_data) + encryptor.finalize()

    # ── GeeTest 协议流程 ─────────────────────────────────────

    def get_type(self) -> dict:
        params = {
            "gt": self.gt,
            "callback": "geetest_" + str(int(round(time.time() * 1000))),
        }
        url = self._build_url("https://api.geetest.com/gettype.php", params)
        self._debug_request("get_type", url)
        resp = self.session.get(url)
        parsed = self._parse_jsonp(resp.text)
        self._debug_response("get_type", parsed)
        self.last_get_type = parsed
        return parsed["data"]

    def get_c_s(self):
        """获取验证码配置和加密参数 c, s"""
        o = {
            "gt": self.gt,
            "challenge": self.challenge,
            "offline": False,
            "new_captcha": True,
            "product": "float",
            "width": "100%",
            "https": True,
            "protocol": "https://",
        }
        o.update(self.get_type())
        o.update(
            {
                "cc": 16,
                "ww": True,
                "i": "-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1",
            }
        )
        o = json.dumps(o, separators=(",", ":"))
        ct = self.aes_encrypt(o)
        s = list(ct)
        i = self.encode(s)
        r = self.enc_key
        w = i + r
        params = {
            "gt": self.gt,
            "challenge": self.challenge,
            "lang": "zh-cn",
            "pt": 0,
            "client_type": "web",
            "callback": "geetest_" + str(int(round(time.time() * 1000))),
            "w": w,
        }
        url = self._build_url("https://api.geetest.com/get.php", params)
        self._debug_request("get_c_s", url)
        resp = self.session.get(url).text
        parsed = self._parse_jsonp(resp)
        self._debug_response("get_c_s", parsed)
        if "data" not in parsed:
            raise RuntimeError(f"get_c_s failed: {str(parsed)[:200]}")
        data = parsed["data"]
        self.last_get_c_s = data
        self._apply_geetest_hosts(data)
        self.c = data["c"]
        self.s = data["s"]
        return data["c"], data["s"]

    def _apply_geetest_hosts(self, data) -> None:
        if not isinstance(data, dict):
            return
        api_server = data.get("api_server")
        if isinstance(api_server, str) and api_server:
            api_server = api_server.strip().rstrip("/")
            if not api_server.startswith("http"):
                api_server = f"https://{api_server}"
            self.fullpage_host = api_server
            self.ajax_host = api_server
            self.get_php_host = api_server.replace("api.geevisit.com", "api.geetest.com")

        static_servers = data.get("static_servers")
        if isinstance(static_servers, list) and static_servers:
            server = static_servers[0]
            if isinstance(server, str) and server:
                server = server.rstrip("/")
                if not server.startswith("http"):
                    server = f"https://{server}"
                self.static_host = server

    def ajax(self):
        """第一轮交互: 模拟点击验证按钮"""
        def transform(e, t, n):
            if not t or not n:
                return e
            o = 0
            i = list(e)
            s = t[0]
            a = t[2]
            b = t[4]
            while o < len(n):
                r = n[o : o + 2]
                o += 2
                c = int(r, 16)
                l = chr(c)
                u = (s * c * c + a * c + b) % len(i)
                i.insert(u, l)
            return "".join(i)

        tt = transform(
            self.encode_mouse_path(self.mouse_path, self.c, self.s), self.c, self.s
        )
        rp = self.md5(self.gt + self.challenge + self.s)
        now = int(time.time() * 1000)
        temp1 = (
            """"lang":"zh-cn","type":"fullpage","tt":"%s","light":"DIV_0","s":"c7c3e21112fe4f741921cb3e4ff9f7cb","h":"321f9af1e098233dbd03f250fd2b5e21","hh":"39bd9cad9e425c3a8f51610fd506e3b3","hi":"09eb21b3ae9542a9bc1e8b63b3d9a467","vip_order":-1,"ct":-1,"ep":{"v":"9.1.9-dbjg5z","te":false,"me":true,"ven":"Google Inc. (Intel)","ren":"ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x0000A7A0) Direct3D11 vs_5_0 ps_5_0, D3D11)","fp":["scroll",0,1602,%d,null],"lp":["up",386,217,%d,"pointerup"],"em":{"ph":0,"cp":0,"ek":"11","wd":1,"nt":0,"si":0,"sc":0},"tm":{"a":%d,"b":%d,"c":%d,"d":0,"e":0,"f":%d,"g":%d,"h":%d,"i":%d,"j":%d,"k":%d,"l":%d,"m":%d,"n":%d,"o":%d,"p":%d,"q":%d,"r":%d,"s":%d,"t":%d,"u":%d},"dnf":"dnf","by":0},"passtime":1600,"rp":"%s","""
            % (tt, now - 5000, now - 3000, now - 8000, now - 7970, now - 7960, now - 8000, now - 8000, now - 8000, now - 7990, now - 7880, now - 7990, now - 7880, now - 7970, now - 7968, now - 7950, now - 7400, now - 7400, now - 5000, now - 4000, now - 4000, now - 4000, rp)
        )
        r = "{" + temp1 + '"captcha_token":"1198034057","du6o":"eyjf7nne"}'
        ct = self.aes_encrypt(r)
        s = [byte for byte in ct]
        w = self.encode(s)
        params = {
            "gt": self.gt,
            "challenge": self.challenge,
            "lang": "zh-cn",
            "pt": 0,
            "client_type": "web",
            "callback": "geetest_" + str(int(round(time.time() * 1000))),
            "w": w,
        }
        url = self._build_url(f"{self.ajax_host}/ajax.php", params)
        self._debug_request("ajax", url)
        resp = self.session.get(url).text
        parsed = self._parse_jsonp(resp)
        self._debug_response("ajax", parsed)
        if "data" not in parsed:
            raise RuntimeError(f"ajax failed: {str(parsed)[:200]}")
        self.last_ajax = parsed["data"]
        self.last_validate = parsed["data"].get("validate")
        return parsed["data"]

    def _build_url(self, base_url: str, params: dict) -> str:
        normalized = {}
        for key, value in params.items():
            if isinstance(value, bool):
                normalized[key] = "true" if value else "false"
            else:
                normalized[key] = value
        return f"{base_url}?{urlencode(normalized)}"

    def _debug_request(self, label: str, url: str) -> None:
        if not self.debug:
            return
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query))
        redacted = {}
        for key, value in query.items():
            if key == "w":
                redacted[key] = f"{value[:32]}...({len(value)})"
            else:
                redacted[key] = value
        print(f"[GeeTest:{label}] request {parsed.scheme}://{parsed.netloc}{parsed.path}")
        print(f"[GeeTest:{label}] params {json.dumps(redacted, ensure_ascii=False)}")

    def _debug_response(self, label: str, parsed: dict) -> None:
        if not self.debug:
            return
        if isinstance(parsed, dict):
            keys = sorted(parsed.keys())
            print(f"[GeeTest:{label}] response keys {keys}")
            if "status" in parsed:
                print(f"[GeeTest:{label}] status {parsed.get('status')}")
            if "error_code" in parsed or "error" in parsed:
                print(f"[GeeTest:{label}] error {json.dumps({k: parsed.get(k) for k in ['error', 'error_code', 'user_error'] if k in parsed}, ensure_ascii=False)}")
            if "data" in parsed and isinstance(parsed['data'], dict):
                print(f"[GeeTest:{label}] data keys {sorted(parsed['data'].keys())}")

    @staticmethod
    def _parse_jsonp(text: str) -> dict:
        """解析 JSONP 响应，提取 JSON 对象"""
        # JSONP 格式: callback({...})
        left = text.find("(")
        right = text.rfind(")")
        if left != -1 and right != -1:
            return json.loads(text[left + 1 : right])
        return json.loads(text)

    def get_pic(self, retry: int = 0):
        """获取验证码图片，返回 (类型, 图片URL)"""
        params = {
            "type": "click",
            "gt": self.gt,
            "challenge": self.challenge,
            "lang": "zh-cn",
            "callback": "geetest_" + str(int(round(time.time() * 1000))),
        }
        if retry == 0:
            url = f"{self.get_php_host}/get.php"
            params.update(
                {
                    "is_next": "true",
                    "https": True,
                    "protocol": "https://",
                    "offline": False,
                    "product": "float",
                    "api_server": self.ajax_host.removeprefix("https://"),
                    "isPC": True,
                    "autoReset": True,
                    "width": "100%",
                }
            )
        else:
            url = "https://api.geetest.com/refresh.php"
        request_url = self._build_url(url, params)
        self._debug_request(f"get_pic[{retry}]", request_url)
        resp = self.session.get(request_url).text
        parsed = self._parse_jsonp(resp)
        self._debug_response(f"get_pic[{retry}]", parsed)
        self.last_pic = parsed
        if "data" not in parsed:
            if "pic" in parsed:
                data = parsed
            else:
                raise RuntimeError(f"get_pic unexpected response: {str(parsed)[:300]}")
        else:
            data = parsed["data"]
        self._apply_geetest_hosts(data)
        self.pic_path = data["pic"]
        pic_url = "https://" + data["image_servers"][0][:-1] + data["pic"]
        return data["pic_type"], pic_url

    def verify(self, points: list) -> dict:
        """
        提交验证码点击结果
        points: 格式为 ["1_1", "2_3"] 的列表 (col_row)
        返回验证结果 dict
        """
        u = self.enc_key
        now = int(time.time() * 1000)
        o = {
            "lang": "zh-cn",
            "passtime": 1600,
            "a": ",".join(points),
            "pic": self.pic_path,
            "tt": self.encode_mouse_path(self.mouse_path, self.c, self.s),
            "ep": {
                "ca": [
                    {"x": 524, "y": 209, "t": 0, "dt": 1819},
                    {"x": 558, "y": 299, "t": 0, "dt": 428},
                    {"x": 563, "y": 95, "t": 0, "dt": 952},
                    {"x": 670, "y": 407, "t": 3, "dt": 892},
                ],
                "v": "3.1.2",
                "$_FG": False,
                "me": True,
                "tm": {
                    "a": now - 5000,
                    "b": 0, "c": 0, "d": 0, "e": 0,
                    "f": now - 4994, "g": now - 4994, "h": now - 4994,
                    "i": now - 4994, "j": now - 4992,
                    "k": 0,
                    "l": now - 4990, "m": now - 4959, "n": now - 4958,
                    "o": now - 4952, "p": now - 4905, "q": now - 2598,
                    "r": now - 2598, "s": now - 1509, "t": now - 1509, "u": now - 1509,
                },
            },
            "h9s9": "1816378497",
        }
        o["rp"] = self.md5(self.gt + self.challenge + str(o["passtime"]))
        o = json.dumps(o, separators=(",", ":"))
        ct = self.aes_encrypt(o)
        s = [byte for byte in ct]
        p = self.encode(s)
        w = p + u
        params = {
            "gt": self.gt,
            "challenge": self.challenge,
            "lang": "zh-cn",
            "pt": 0,
            "client_type": "web",
            "w": w,
        }
        resp = self.session.get(self._build_url(f"{self.ajax_host}/ajax.php", params)).text
        return self._parse_jsonp(resp)

    def close(self):
        self.session.close()
