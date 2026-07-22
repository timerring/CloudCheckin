import unittest
from datetime import datetime, timedelta, timezone

from telegram.notify import format_source_notification


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


if __name__ == "__main__":
    unittest.main()
