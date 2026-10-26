# X (Twitter) Anti-Detect Browser Automation Agent (Camoufox & Playwright)

A next-generation stealth browser automation agent powered by **Camoufox** (C++-modified anti-detect Firefox) and **Playwright**, designed for robust social automation without triggering Cloudflare, Kasada, or platform behavioral heuristics.

## 🚀 Why Camoufox Over Legacy Selenium?

- **True C++ Level Fingerprint Masking:** Unlike Selenium (which injects easily detectable JavaScript overrides), Camoufox modifies browser C++ source code to alter WebGL, Canvas, AudioContext, fonts, and TLS client hello fingerprints natively.
- **Zero Automation Flags:** Native Firefox engine runs without `navigator.webdriver` or Chrome DevTools Protocol automation indicators.
- **Playwright Speed & Stability:** Fast event-driven DOM handling without brittle explicit sleep polling.

## 🛠️ Key Engineering Features

- **Session Cookie Injection:** Direct session initialization using `auth_token` and `ct0` cookies, skipping 2FA and login forms.
- **Human Typing Simulation (`human_type`):**
  - Variable typing speeds (40–180ms per character).
  - Natural micro-pauses between words.
  - Realistic typo generation (~8% probability) with auto-correction via `Backspace`.
- **Randomized Micro-Behaviors (`random_actions`):** Non-linear mouse movements, variable scroll vectors, and organic idle delays.
- **Residential Proxy Integration:** Native support for authenticated proxies (`http://user:pass@host:port` and SOCKS5) with automatic GeoIP alignment.

## ⚙️ Quickstart

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m camoufox fetch
   ```

2. Configure settings:
   ```bash
   cp settings/config.example.json settings/config.json
   cp settings/token_prefs.example.json settings/token_prefs.json
   ```

3. Run the Camoufox agent:
   ```bash
   python camoufox_agent.py
   ```
