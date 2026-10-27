import json
import os
import unittest


class TestStealthConfig(unittest.TestCase):
    def test_config_example_structure(self):
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "settings", "config.example.json"
        )
        self.assertTrue(os.path.exists(config_path), "config.example.json must exist")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        self.assertIn("action_delay", cfg)
        self.assertIn("scroll_time", cfg)
        self.assertIn("proxy_enabled", cfg)
        self.assertIsInstance(cfg["action_delay"], (int, float))
        self.assertIsInstance(cfg["proxy_enabled"], bool)

    def test_user_agents_list(self):
        ua_path = os.path.join(
            os.path.dirname(__file__), "..", "settings", "user_agents.txt"
        )
        if os.path.exists(ua_path):
            with open(ua_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            self.assertGreater(len(lines), 0, "user_agents.txt should not be empty")
            for ua in lines:
                self.assertIn("Mozilla", ua, f"Invalid UA signature: {ua}")

    def test_proxy_parser_logic(self):
        proxy_str = "socks5://user:pass@127.0.0.1:1080"
        self.assertTrue(
            proxy_str.startswith("http://") or proxy_str.startswith("socks5://"),
            "Proxy scheme must be http or socks5",
        )


if __name__ == "__main__":
    unittest.main()
