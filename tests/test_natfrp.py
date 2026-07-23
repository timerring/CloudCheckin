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
        with patch.dict(os.environ, {"SAKURAFRP_COOKIE": "session=abc"}, clear=True):
            config = NatfrpConfig.from_env()

        self.assertEqual(config.cookie, "session=abc")

    def test_requires_cookie(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(NatfrpError):
                NatfrpConfig.from_env()

class NotificationTest(unittest.TestCase):
    @patch("natfrp.natfrp.send_source_notification")
    def test_notifications_are_enabled_by_default(self, send_notification):
        values = {"TELEGRAM_TOKEN": "token", "TELEGRAM_CHAT_ID": "chat"}
        with patch.dict(os.environ, values, clear=True):
            _notify_if_configured("test")

        send_notification.assert_called_once_with("SAKURAFRP", "test")

    @patch("natfrp.natfrp.send_source_notification")
    def test_notifications_can_be_disabled(self, send_notification):
        values = {
            "SAKURAFRP_NOTIFY": "false",
            "TELEGRAM_TOKEN": "token",
            "TELEGRAM_CHAT_ID": "chat",
        }
        with patch.dict(os.environ, values, clear=True):
            _notify_if_configured("test")

        send_notification.assert_not_called()


if __name__ == "__main__":
    unittest.main()
