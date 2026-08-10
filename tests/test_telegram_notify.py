import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from telegram.notify import (
    TELEGRAM_MESSAGE_LIMIT,
    TRUNCATION_SUFFIX,
    format_source_notification,
    send_tg_notification,
    summarize_http_failure,
)


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

    def test_truncates_oversized_platform_response(self):
        now = datetime(2026, 8, 10, 10, 1, 9, tzinfo=timezone(timedelta(hours=8)))

        result = format_source_notification(
            "deepflood",
            f"Account 1: check-in failed — {'x' * 5000}",
            now=now,
        )

        self.assertEqual(len(result), TELEGRAM_MESSAGE_LIMIT)
        self.assertTrue(result.startswith("2026/08/10 10:01:09\nDEEPFLOOD\n"))
        self.assertTrue(result.endswith(TRUNCATION_SUFFIX))


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


class SummarizeHttpFailureTest(unittest.TestCase):
    def test_extracts_cloudflare_error_title(self):
        response = """
            <!DOCTYPE html>
            <html><head><title>deepflood.com | 522: Connection timed out</title></head></html>
        """

        result = summarize_http_failure(522, response)

        self.assertEqual(
            result,
            "HTTP 522: deepflood.com | 522: Connection timed out",
        )

    def test_keeps_short_plain_text_error(self):
        result = summarize_http_failure(403, '{"error": "cookie expired"}')

        self.assertEqual(result, 'HTTP 403: {"error": "cookie expired"}')


if __name__ == "__main__":
    unittest.main()
