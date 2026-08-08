import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from telegram.notify import format_source_notification, send_tg_notification


class FormatSourceNotificationTest(unittest.TestCase):
    def test_formats_single_message(self):
        now = datetime(2026, 7, 22, 10, 1, 9, tzinfo=timezone(timedelta(hours=8)))

        result = format_source_notification("v2ex", "Check-in successful", now=now)

        self.assertEqual(
            result,
            "2026/07/22 10:01:09\nV2EX\nCheck-in successful",
        )

    def test_combines_account_results(self):
        now = datetime(2026, 7, 22, 10, 1, 9, tzinfo=timezone(timedelta(hours=8)))

        result = format_source_notification(
            "deepflood",
            ["Account 1: successful", "Account 2: failed"],
            now=now,
        )

        self.assertEqual(
            result,
            "2026/07/22 10:01:09\nDEEPFLOOD\n"
            "Account 1: successful\nAccount 2: failed",
        )


class SendTelegramNotificationTest(unittest.TestCase):
    @patch("telegram.notify.http.client.HTTPSConnection")
    def test_records_successful_delivery_for_ci_fallback(self, connection):
        response = Mock(status=200)
        response.read.return_value = b'{"ok": true}'
        connection.return_value.getresponse.return_value = response

        with TemporaryDirectory() as temp_dir:
            marker = f"{temp_dir}/notification-sent"
            with patch("telegram.notify.TELEGRAM_TOKEN", "token"), patch(
                "telegram.notify.TELEGRAM_CHAT_ID", "chat"
            ), patch("telegram.notify.NOTIFICATION_SENT_MARKER", marker):
                send_tg_notification("test")

            with open(marker, encoding="utf-8") as marker_file:
                self.assertEqual(marker_file.read(), "")


if __name__ == "__main__":
    unittest.main()
