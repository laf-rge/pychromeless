import unittest
from datetime import date, datetime

from email_templates import (
    AttendanceRecord,
    DailyJournalData,
    MealPeriodViolation,
    MissingPunch,
    StoreCard,
    render_alert_email,
    render_daily_journal,
    render_tips_email,
)


def _make_sample_data() -> DailyJournalData:
    """Build sample DailyJournalData matching the B3 mockup structure."""
    cards = [
        StoreCard(
            store_id="20358",
            store_name="S Santa Rosa",
            drawer_opens=4,
            attendance=[
                AttendanceRecord(
                    store="20358",
                    name="Weeks, Evin",
                    shift_time=datetime(2026, 2, 15, 11, 0),
                    clock_in_time=None,
                    minutes_diff=None,
                    record_type="no show on shift",
                ),
                AttendanceRecord(
                    store="20358",
                    name="Ballard-Albini, Justin",
                    shift_time=datetime(2026, 2, 15, 8, 0),
                    clock_in_time=datetime(2026, 2, 15, 10, 10),
                    minutes_diff=-131,
                    record_type="late",
                ),
            ],
            missing_punches=[
                MissingPunch(
                    store="20358",
                    name="Garcia, Maria",
                    start_time=datetime(2026, 2, 15, 14, 30),
                ),
            ],
        ),
        StoreCard(
            store_id="20400",
            store_name="N Santa Rosa",
            drawer_opens=2,
            attendance=[
                AttendanceRecord(
                    store="20400",
                    name="Mead, Lucas",
                    shift_time=datetime(2026, 2, 15, 7, 30),
                    clock_in_time=datetime(2026, 2, 15, 7, 9),
                    minutes_diff=20,
                    record_type="early",
                ),
            ],
            mpvs=[
                MealPeriodViolation(
                    store="20400",
                    name="Lee, Jordan",
                    day=date(2026, 2, 15),
                    shift_start=datetime(2026, 2, 15, 7, 30),
                ),
            ],
        ),
    ]
    return DailyJournalData(
        report_date=date(2026, 2, 15),
        store_cards=cards,
        total_no_shows=1,
        total_late=1,
        total_early=1,
        total_mpvs=1,
        total_drawer_opens=6,
    )


class TestRenderDailyJournal(unittest.TestCase):
    def setUp(self) -> None:
        self.data = _make_sample_data()
        self.html = render_daily_journal(self.data)

    def test_returns_complete_html_document(self) -> None:
        self.assertIn("<!DOCTYPE html>", self.html)
        self.assertIn("</html>", self.html)

    def test_header_contains_branding(self) -> None:
        self.assertIn("WMC", self.html)
        self.assertIn("Wagoner Management Corp.", self.html)
        self.assertIn("Daily Journal Report", self.html)

    def test_header_contains_formatted_date(self) -> None:
        self.assertIn("Sunday, February 15, 2026", self.html)

    def test_summary_strip_values(self) -> None:
        # Check that the summary strip renders the totals
        self.assertIn("Drawer Opens", self.html)
        self.assertIn("No Shows", self.html)
        self.assertIn("Meal Violations", self.html)

    def test_store_cards_present(self) -> None:
        self.assertIn("20358", self.html)
        self.assertIn("S Santa Rosa", self.html)
        self.assertIn("20400", self.html)
        self.assertIn("N Santa Rosa", self.html)

    def test_drawer_open_label_pluralization(self) -> None:
        self.assertIn("4 drawer opens", self.html)
        self.assertIn("2 drawer opens", self.html)

    def test_no_show_row_rendering(self) -> None:
        self.assertIn("Weeks, Evin", self.html)
        self.assertIn("no show", self.html)
        # Red background color for no-show rows
        self.assertIn("#FEF2F2", self.html)

    def test_late_row_rendering(self) -> None:
        self.assertIn("Ballard-Albini, Justin", self.html)
        self.assertIn("131 min late", self.html)
        # Yellow background for late rows
        self.assertIn("#FFFBEB", self.html)

    def test_early_row_rendering(self) -> None:
        self.assertIn("Mead, Lucas", self.html)
        self.assertIn("20 min early", self.html)
        # Green background for early rows
        self.assertIn("#F0FDF4", self.html)

    def test_missing_punch_rendering(self) -> None:
        self.assertIn("Missing Punches", self.html)
        self.assertIn("Garcia, Maria", self.html)
        self.assertIn("clocked in 2:30 PM", self.html)

    def test_mpv_rendering(self) -> None:
        self.assertIn("Meal Period Violation", self.html)
        self.assertIn("Lee, Jordan", self.html)
        self.assertIn("Shift 7:30 AM", self.html)

    def test_footer(self) -> None:
        self.assertIn("Josiah", self.html)

    def test_html_escape_on_names(self) -> None:
        """Verify that user-provided names are escaped."""
        self.data.store_cards[0].attendance[0].name = '<script>alert("xss")</script>'
        result = render_daily_journal(self.data)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)


class TestEmptySectionsOmitted(unittest.TestCase):
    def test_no_attendance_section_when_empty(self) -> None:
        card = StoreCard(
            store_id="20407",
            store_name="Cotati",
            drawer_opens=1,
        )
        data = DailyJournalData(
            report_date=date(2026, 2, 15),
            store_cards=[card],
            total_no_shows=0,
            total_late=0,
            total_early=0,
            total_mpvs=0,
            total_drawer_opens=1,
        )
        html = render_daily_journal(data)
        self.assertIn("20407", html)
        self.assertIn("Cotati", html)
        self.assertNotIn("Attendance", html)
        self.assertNotIn("Missing Punches", html)
        self.assertNotIn("Meal Period", html)

    def test_single_drawer_open_not_pluralized(self) -> None:
        card = StoreCard(store_id="20407", store_name="Cotati", drawer_opens=1)
        data = DailyJournalData(
            report_date=date(2026, 2, 15),
            store_cards=[card],
            total_no_shows=0, total_late=0, total_early=0, total_mpvs=0,
            total_drawer_opens=1,
        )
        html = render_daily_journal(data)
        self.assertIn("1 drawer open", html)
        self.assertNotIn("1 drawer opens", html)


class TestRenderAlertEmail(unittest.TestCase):
    def test_alert_email_wrapping(self) -> None:
        html = render_alert_email(
            "Missing Deposit Alert",
            date(2026, 2, 15),
            "<strong>20358</strong> is missing a deposit.",
        )
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Missing Deposit Alert", html)
        self.assertIn("WMC", html)
        self.assertIn("20358", html)
        self.assertIn("Josiah", html)

    def test_alert_date_formatted(self) -> None:
        html = render_alert_email("Test", date(2026, 2, 15), "body")
        self.assertIn("Sunday, February 15, 2026", html)


class TestRenderTipsEmail(unittest.TestCase):
    def test_tips_email_body(self) -> None:
        html = render_tips_email("Tip Spreadsheet for 02/2026 pp 1", date(2026, 2, 15))
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Tip Spreadsheet for 02/2026 pp 1", html)
        self.assertIn("Attached is the tip spreadsheet", html)
        self.assertIn("Josiah", html)


if __name__ == "__main__":
    unittest.main()
