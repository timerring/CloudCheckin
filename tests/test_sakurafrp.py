import os
import unittest
from unittest.mock import patch

from sakurafrp.sakurafrp import (
    NatfrpConfig,
    NatfrpError,
    _notify_if_configured,
    main,
)


class ConfigTest(unittest.TestCase):
    def test_reads_credentials(self):
        values = {
            "SAKURAFRP_USERNAME": "user",
            "SAKURAFRP_PASSWORD": "password",
        }
        with patch.dict(os.environ, values, clear=True):
            config = NatfrpConfig.from_env()

        self.assertEqual(config.username, "user")
        self.assertEqual(config.password, "password")

    def test_requires_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(NatfrpError):
                NatfrpConfig.from_env()

class NotificationTest(unittest.TestCase):
    @patch("sakurafrp.sakurafrp.send_source_notification")
    def test_notifications_are_enabled_by_default(self, send_notification):
        values = {"TELEGRAM_TOKEN": "token", "TELEGRAM_CHAT_ID": "chat"}
        with patch.dict(os.environ, values, clear=True):
            _notify_if_configured("test")

        send_notification.assert_called_once_with("SAKURAFRP", "test")

    @patch("sakurafrp.sakurafrp.send_source_notification")
    def test_notifications_can_be_disabled(self, send_notification):
        values = {
            "SAKURAFRP_NOTIFY": "false",
            "TELEGRAM_TOKEN": "token",
            "TELEGRAM_CHAT_ID": "chat",
        }
        with patch.dict(os.environ, values, clear=True):
            _notify_if_configured("test")

        send_notification.assert_not_called()

    @patch("sakurafrp.sakurafrp.send_source_notification")
    @patch("sakurafrp.sakurafrp.check_in", side_effect=RuntimeError("sensitive"))
    def test_unexpected_errors_send_sanitized_notification(
        self, check_in, send_notification
    ):
        values = {
            "SAKURAFRP_USERNAME": "user",
            "SAKURAFRP_PASSWORD": "password",
            "TELEGRAM_TOKEN": "token",
            "TELEGRAM_CHAT_ID": "chat",
        }
        with patch.dict(os.environ, values, clear=True):
            self.assertEqual(main(), 1)

        check_in.assert_called_once()
        send_notification.assert_called_once_with(
            "SAKURAFRP",
            "SakuraFrp check-in failed unexpectedly (RuntimeError)",
        )


if __name__ == "__main__":
    unittest.main()
