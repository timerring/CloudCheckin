import os
import unittest
from unittest.mock import patch

from natfrp.natfrp import (
    NatfrpConfig,
    NatfrpError,
    _notify_if_configured,
)


class ConfigTest(unittest.TestCase):
    def test_reads_cookie_defaults(self):
        with patch.dict(os.environ, {"NATFRP_COOKIE": "session=abc"}, clear=True):
            config = NatfrpConfig.from_env()

        self.assertTrue(config.headless)
        self.assertEqual(config.captcha_timeout_seconds, 180)

    def test_requires_cookie(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(NatfrpError):
                NatfrpConfig.from_env()

    def test_reads_headless_and_timeout_options(self):
        values = {
            "NATFRP_COOKIE": "session=abc",
            "NATFRP_HEADLESS": "true",
            "NATFRP_CAPTCHA_TIMEOUT_SECONDS": "30",
        }
        with patch.dict(os.environ, values, clear=True):
            config = NatfrpConfig.from_env()

        self.assertTrue(config.headless)
        self.assertEqual(config.captcha_timeout_seconds, 30)


class NotificationTest(unittest.TestCase):
    @patch("natfrp.natfrp.send_source_notification")
    def test_notifications_are_opt_in(self, send_notification):
        values = {"TELEGRAM_TOKEN": "token", "TELEGRAM_CHAT_ID": "chat"}
        with patch.dict(os.environ, values, clear=True):
            _notify_if_configured("test")

        send_notification.assert_not_called()

    @patch("natfrp.natfrp.send_source_notification")
    def test_sends_notification_when_enabled(self, send_notification):
        values = {
            "NATFRP_NOTIFY": "true",
            "TELEGRAM_TOKEN": "token",
            "TELEGRAM_CHAT_ID": "chat",
        }
        with patch.dict(os.environ, values, clear=True):
            _notify_if_configured("test")

        send_notification.assert_called_once_with("SAKURAFRP", "test")


if __name__ == "__main__":
    unittest.main()
