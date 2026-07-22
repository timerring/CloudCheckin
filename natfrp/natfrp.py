import base64
import io
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass

from dotenv import load_dotenv

from telegram.notify import send_source_notification


TARGET_URL = "https://www.natfrp.com/user/"
SIGNED_TEXT = "今天已经签到过啦"
SIGN_BUTTON_TEXT = "点击这里签到"
GRID_SELECTOR = ".geetest_table_box"
ADULT_CHECK_SELECTOR = ".adult-check"
ADULT_CONFIRM_TEXT = "是，我已满18岁"
CAPTCHA_TIMEOUT_SECONDS = 180


class NatfrpError(RuntimeError):
    """Base error for the SakuraFrp check-in flow."""


class ManualCaptchaRequired(NatfrpError):
    """Raised when GeeTest requires a person in a visible browser."""


@dataclass(frozen=True)
class NatfrpConfig:
    cookie: str = ""
    mimo_apikey: str = ""

    @classmethod
    def from_env(cls) -> "NatfrpConfig":
        cookie = os.environ.get("NATFRP_COOKIE", "").strip()
        if not cookie:
            raise NatfrpError("Environment variable NATFRP_COOKIE is not set")

        mimo_apikey = os.environ.get("NATFRP_MIMO_APIKEY", "").strip()

        return cls(
            cookie=cookie,
            mimo_apikey=mimo_apikey,
        )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _is_visible(locator, timeout: int = 500) -> bool:
    try:
        return locator.is_visible(timeout=timeout)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# AI vision solver (MiMo)
# ---------------------------------------------------------------------------


def _call_mimo_vision(image_bytes: bytes, prompt: str, api_key: str,
                       model: str = "mimo-v2.5") -> str:
    from openai import OpenAI

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.xiaomimimo.com/v1",
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }],
        max_completion_tokens=1024,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return response.choices[0].message.content.strip()


def _call_mimo_text(prompt: str, api_key: str, model: str = "mimo-v2.5") -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.xiaomimimo.com/v1",
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=1024,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return response.choices[0].message.content.strip()


def _safe_parse_json_list(text: str):
    try:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        return json.loads(match.group() if match else text)
    except Exception:
        return None


def _solve_geetest_grid(page, api_key: str) -> bool:
    """Solve the 9-grid GeeTest captcha on natfrp.com using MiMo vision.

    Returns ``True`` if the captcha was solved and submitted successfully.
    """
    grid = page.locator(GRID_SELECTOR).first
    if not grid.is_visible():
        return False

    print("[AI] Solving 9-grid GeeTest captcha ...", flush=True)

    # Step 1: identify the target object from the tip image or text
    target = ""
    tip_img = page.locator(".geetest_tip_img").first
    if tip_img.is_visible():
        target = _call_mimo_vision(
            tip_img.screenshot(), "图中是什么物体？只回答物体名称，不要带标点。", api_key
        )
    else:
        tip_text = page.locator(".geetest_tip_content").first
        if tip_text.is_visible():
            target = tip_text.inner_text()
    target = re.sub(r"[^\w]", "", target)
    print(f"  [Step 1] target = '{target}'", flush=True)

    # Step 2-4: crop the grid into 3 rows, identify each row's 3 cells
    from PIL import Image

    grid_img = Image.open(io.BytesIO(grid.screenshot()))
    w, h = grid_img.size
    row_h = h / 3

    all_descriptions: list[str] = []
    for i in range(3):
        top = int(i * row_h)
        bottom = int((i + 1) * row_h)
        row_crop = grid_img.crop((0, top, w, bottom))
        buf = io.BytesIO()
        row_crop.save(buf, format="PNG")

        prompt = (
            "这是验证码九宫格的第{row}行图片，包含3个格子。"
            "请从左到右识别这3个格子的物体名称，"
            '只返回 JSON 字符串数组，例如：["猫", "狗", "汽车"]。不要有任何解释文字。'
        ).format(row=i + 1)
        res = _call_mimo_vision(buf.getvalue(), prompt, api_key)
        print(f"  [AI] row {i + 1} -> {res}", flush=True)

        parsed = _safe_parse_json_list(res)
        if parsed and isinstance(parsed, list):
            while len(parsed) < 3:
                parsed.append("未知")
            all_descriptions.extend(parsed[:3])
        else:
            all_descriptions.extend(["未知", "未知", "未知"])

    # Step 5: semantic matching
    items_text = "\n".join(
        f"{idx + 1}. {d}" for idx, d in enumerate(all_descriptions)
    )
    match_prompt = (
        f"题目：找出图片中所有的【{target}】。\n"
        f"当前9个格子的识别结果如下：\n{items_text}\n"
        "请判断哪些序号（1-9）最符合【题目】要求。\n"
        "只返回 JSON 数组，如 [1, 3, 5]。没有符合的返回 []。"
    )
    match_res = _call_mimo_text(match_prompt, api_key)
    print(f"  [AI] semantic match -> {match_res}", flush=True)

    click_indices = _safe_parse_json_list(match_res)
    if not click_indices or not isinstance(click_indices, list):
        print("  [AI] no matching cells found, refreshing ...", flush=True)
        refresh = page.locator(".geetest_refresh").first
        if refresh.is_visible():
            refresh.click()
            time.sleep(2)
        return False

    print(f"  [Final] clicking cells: {click_indices}", flush=True)

    # Click matching cells
    box = grid.bounding_box()
    if not box:
        return False
    cell_w, cell_h = box["width"] / 3, box["height"] / 3

    for idx in click_indices:
        try:
            val = int(idx)
            if 1 <= val <= 9:
                r, c = (val - 1) // 3, (val - 1) % 3
                x = box["x"] + c * cell_w + cell_w / 2
                y = box["y"] + r * cell_h + cell_h / 2
                page.mouse.click(x, y)
                time.sleep(random.uniform(0.3, 0.5))
        except (ValueError, TypeError):
            continue

    # Submit
    for sel in [".geetest_commit", "text=确认", ".geetest_submit"]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=1000):
                btn.click()
                break
        except Exception:
            continue

    return True


# ---------------------------------------------------------------------------
# check-in flow
# ---------------------------------------------------------------------------


def check_in(config: NatfrpConfig) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise NatfrpError(
            "Playwright is not installed; run `pip install -r requirements.txt` "
            "and `playwright install chromium`"
        ) from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.set_viewport_size({"width": 1280, "height": 900})

            cookies = []
            for pair in config.cookie.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    name, value = pair.split("=", 1)
                    cookies.append({
                        "name": name.strip(),
                        "value": value.strip(),
                        "domain": ".natfrp.com",
                        "path": "/",
                    })
            if not cookies:
                raise NatfrpError("NATFRP_COOKIE does not contain valid cookie pairs")
            context.add_cookies(cookies)

            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60_000)

            if "login" in page.url or _is_visible(page.locator("#username"), timeout=500):
                raise NatfrpError(
                    "NATFRP_COOKIE is expired or does not authenticate the account"
                )

            # Dismiss age gate
            try:
                confirm = (
                    page.locator(ADULT_CHECK_SELECTOR)
                    .get_by_text(ADULT_CONFIRM_TEXT, exact=True)
                    .first
                )
                if confirm.is_visible(timeout=3_000):
                    confirm.click()
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(1_000)
                    print("Dismissed age confirmation dialog", flush=True)
            except Exception:
                pass

            # Already signed?
            if _is_visible(page.get_by_text(SIGNED_TEXT, exact=True), timeout=2_000):
                print("SakuraFrp has already been checked in today", flush=True)
                return True

            # Click sign-in button
            sign_button = page.locator(
                f"button:has-text('{SIGN_BUTTON_TEXT}')"
            ).first
            if not _is_visible(sign_button, timeout=5_000):
                if _is_visible(page.locator("#username"), timeout=500):
                    raise NatfrpError(
                        "NATFRP_COOKIE is expired or does not authenticate the account"
                    )
                raise NatfrpError("Could not find the SakuraFrp check-in button")

            sign_button.click()
            page.wait_for_timeout(1_000)

            # Wait for result (captcha solve loop)
            deadline = time.monotonic() + CAPTCHA_TIMEOUT_SECONDS
            last_captcha_attempt = 0.0
            captcha_failures = 0

            while time.monotonic() < deadline:
                if _is_visible(page.get_by_text(SIGNED_TEXT, exact=True), timeout=500):
                    print("SakuraFrp check-in successful", flush=True)
                    return True

                if _is_visible(page.locator(GRID_SELECTOR).first, timeout=500):
                    if config.mimo_apikey and captcha_failures < 3:
                        now = time.monotonic()
                        if now - last_captcha_attempt < 5:
                            page.wait_for_timeout(500)
                            continue
                        last_captcha_attempt = now
                        captcha_failures += 1
                        print(f"  [AI] captcha attempt {captcha_failures}/3", flush=True)
                        try:
                            if _solve_geetest_grid(page, config.mimo_apikey):
                                time.sleep(3)
                                continue
                        except Exception as exc:
                            print(
                                f"AI captcha solver error: {exc}; "
                                f"falling back to manual",
                                flush=True,
                            )
                        print("  [AI] captcha not solved, will retry ...", flush=True)
                        page.wait_for_timeout(1500)
                        continue

                    raise ManualCaptchaRequired(
                        "SakuraFrp requested GeeTest verification but the AI captcha "
                        "solver is unavailable or could not solve it"
                    )

                page.wait_for_timeout(500)

            raise NatfrpError(
                f"SakuraFrp check-in did not complete within "
                f"{CAPTCHA_TIMEOUT_SECONDS} seconds"
            )
        finally:
            browser.close()


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def _notify_if_configured(message: str) -> None:
    enabled = os.environ.get("NATFRP_NOTIFY", "true").strip().lower() in {
        "1", "true", "yes", "on",
    }
    if (
        enabled
        and os.environ.get("TELEGRAM_TOKEN")
        and os.environ.get("TELEGRAM_CHAT_ID")
    ):
        send_source_notification("SAKURAFRP", message)


def main() -> int:
    load_dotenv()
    try:
        if check_in(NatfrpConfig.from_env()):
            message = "SakuraFrp check-in successful"
            print(message, flush=True)
            _notify_if_configured(message)
            return 0
    except NatfrpError as exc:
        message = f"SakuraFrp check-in failed: {exc}"
        print(message, file=sys.stderr, flush=True)
        _notify_if_configured(message)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
