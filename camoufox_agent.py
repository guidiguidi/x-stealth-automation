import os
import json
import time
import random
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from camoufox.sync_api import Camoufox

BASE_DIR = Path(__file__).parent
SETTINGS_DIR = BASE_DIR / "settings"
DIALOGS_DIR = BASE_DIR / "dialogs"

CONFIG_FILE = SETTINGS_DIR / "config.json"
TOKEN_PREFS_FILE = SETTINGS_DIR / "token_prefs.json"
DEFAULT_CONFIG_FILE = SETTINGS_DIR / "config.example.json"
USER_IDS_FILE = SETTINGS_DIR / "ids.txt"
MESSAGES_FILE = SETTINGS_DIR / "messages.txt"
GOOD_LOG = DIALOGS_DIR / "good.txt"
BAD_LOG = DIALOGS_DIR / "bad.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CamoufoxAgent")


def parse_proxy(proxy_str: str) -> Optional[Dict[str, str]]:
    """Parses standard proxy URL into Playwright/Camoufox proxy format."""
    if not proxy_str or not proxy_str.strip():
        return None
    p = proxy_str.strip()
    if not p.startswith(("http://", "https://", "socks5://")):
        p = "http://" + p
    parsed = urlparse(p)
    server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    res = {"server": server}
    if parsed.username:
        res["username"] = parsed.username
    if parsed.password:
        res["password"] = parsed.password
    return res


def load_config() -> Dict[str, Any]:
    """Loads JSON configuration with sensible defaults."""
    cfg = {
        "action_delay": 5,
        "headless": False,
        "proxy_enabled": False,
        "proxy": ""
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            logger.warning(f"Error reading config.json: {e}")
    elif DEFAULT_CONFIG_FILE.exists():
        try:
            with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def load_tokens() -> Dict[str, str]:
    """Loads auth_token and ct0 session credentials."""
    if TOKEN_PREFS_FILE.exists():
        try:
            with open(TOKEN_PREFS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"auth_token": "", "ct0": ""}


def human_type(page, locator_selector: str, text: str):
    """
    Simulates human typing cadences with variable WPM,
    realistic pauses, and natural typo self-correction.
    """
    locator = page.locator(locator_selector)
    locator.focus()

    words = text.split(" ")
    for w_idx, word in enumerate(words):
        for c_idx, char in enumerate(word):
            delay = random.uniform(0.04, 0.18)

            # 8% chance of typing typo character and backspacing
            if random.random() < 0.08 and c_idx > 1:
                wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                page.keyboard.type(wrong_char, delay=int(delay * 500))
                time.sleep(random.uniform(0.08, 0.22))
                page.keyboard.press("Backspace")
                time.sleep(random.uniform(0.05, 0.12))

            page.keyboard.type(char, delay=int(delay * 1000))
            time.sleep(delay)

        if w_idx < len(words) - 1:
            page.keyboard.press("Space")
            # Natural pause between words
            time.sleep(random.uniform(0.08, 0.35))
            # 5% chance of thinking pause
            if random.random() < 0.05:
                time.sleep(random.uniform(0.6, 1.4))


def random_actions(page):
    """Executes randomized micro-behaviors to simulate active human presence."""
    try:
        action_type = random.choice(["scroll", "mouse_wiggle", "pause"])
        if action_type == "scroll":
            delta_y = random.randint(-250, 350)
            page.mouse.wheel(0, delta_y)
            time.sleep(random.uniform(0.2, 0.7))
        elif action_type == "mouse_wiggle":
            viewport = page.viewport_size or {"width": 1280, "height": 800}
            target_x = random.randint(100, viewport["width"] - 100)
            target_y = random.randint(100, viewport["height"] - 100)
            page.mouse.move(target_x, target_y, steps=random.randint(5, 15))
        else:
            time.sleep(random.uniform(0.3, 0.9))
    except Exception:
        pass


class CamoufoxTwitterAgent:
    """
    Next-generation anti-detect Twitter/X agent powered by Camoufox.
    Spoofs C++ browser internals, WebGL, Canvas, and TLS fingerprints.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        self.tokens = load_tokens()

    def run(self, target_usernames: List[str], message_templates: List[str]):
        proxy_settings = None
        if self.config.get("proxy_enabled") and self.config.get("proxy"):
            proxy_settings = parse_proxy(self.config["proxy"])
            if proxy_settings:
                logger.info(f"Using Camoufox proxy: {proxy_settings.get('server')}")

        headless = self.config.get("headless", False)
        logger.info(f"Initializing Camoufox browser (headless={headless})...")

        with Camoufox(headless=headless, proxy=proxy_settings, geoip=True if proxy_settings else False) as browser:
            context = browser.new_context()

            # Inject session cookies if available
            auth_token = self.tokens.get("auth_token")
            ct0 = self.tokens.get("ct0")
            if auth_token and ct0:
                logger.info("Injecting saved session cookies (auth_token & ct0)...")
                context.add_cookies([
                    {"name": "auth_token", "value": auth_token, "domain": ".x.com", "path": "/"},
                    {"name": "ct0", "value": ct0, "domain": ".x.com", "path": "/"}
                ])

            page = context.new_page()
            page.goto("https://x.com/home", timeout=45000)
            time.sleep(2)

            if "login" in page.url:
                logger.warning("Session cookie expired or not set. Please log in manually.")
                return

            logger.info("Successfully authenticated on X (Twitter)!")

            for idx, username in enumerate(target_usernames):
                msg = random.choice(message_templates)
                logger.info(f"[{idx+1}/{len(target_usernames)}] Processing @{username}...")

                try:
                    random_actions(page)
                    page.goto("https://x.com/messages/compose", timeout=30000)
                    time.sleep(random.uniform(1.2, 2.5))

                    # Type username in search box
                    search_box = 'input[data-testid="searchPeople"]'
                    page.wait_for_selector(search_box, timeout=15000)
                    human_type(page, search_box, f"@{username}")
                    time.sleep(random.uniform(1.5, 2.5))

                    # Select first user result
                    user_row = f'div[data-testid="UserCell"]'
                    if page.locator(user_row).count() > 0:
                        page.locator(user_row).first.click()
                        time.sleep(random.uniform(0.5, 1.2))

                        # Click Next
                        next_btn = 'button[data-testid="nextButton"]'
                        page.wait_for_selector(next_btn, timeout=10000)
                        page.locator(next_btn).click()
                        time.sleep(random.uniform(1.0, 2.0))

                        # Type message in composer
                        composer = 'div[data-testid="dmComposerTextInput"][contenteditable="true"]'
                        page.wait_for_selector(composer, timeout=10000)
                        human_type(page, composer, msg)
                        time.sleep(random.uniform(0.8, 1.5))

                        # Click send
                        send_btn = 'button[data-testid="dmComposerSendButton"]'
                        page.locator(send_btn).click()
                        time.sleep(random.uniform(1.5, 2.5))

                        logger.info(f"✅ Message sent to @{username}")
                    else:
                        logger.warning(f"User @{username} not found in search.")

                except Exception as e:
                    logger.error(f"Failed to message @{username}: {e}")

                time.sleep(self.config.get("action_delay", 5))

        logger.info("Camoufox batch complete.")


if __name__ == "__main__":
    agent = CamoufoxTwitterAgent()
    print("CamoufoxTwitterAgent module ready.")
