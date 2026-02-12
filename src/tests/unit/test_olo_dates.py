import datetime

from flexepos import last_sunday_of_month


class TestLastSundayOfMonth:
    def test_dec_2025(self):
        assert last_sunday_of_month(2025, 12) == datetime.date(2025, 12, 28)

    def test_jan_2026(self):
        assert last_sunday_of_month(2026, 1) == datetime.date(2026, 1, 25)

    def test_feb_2026(self):
        assert last_sunday_of_month(2026, 2) == datetime.date(2026, 2, 22)

    def test_nov_2025_month_ends_on_sunday(self):
        assert last_sunday_of_month(2025, 11) == datetime.date(2025, 11, 30)

    def test_aug_2025_last_day_is_sunday(self):
        assert last_sunday_of_month(2025, 8) == datetime.date(2025, 8, 31)

    def test_feb_2028_leap_year(self):
        assert last_sunday_of_month(2028, 2) == datetime.date(2028, 2, 27)


class TestOloPeriodStart:
    """Verify the period start logic used in getOnlinePayments."""

    @staticmethod
    def _period_start(year: int, month: int) -> datetime.date:
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        return last_sunday_of_month(prev_year, prev_month) + datetime.timedelta(days=1)

    def test_dec_2025_start(self):
        assert self._period_start(2025, 12) == datetime.date(2025, 12, 1)

    def test_jan_2026_start(self):
        assert self._period_start(2026, 1) == datetime.date(2025, 12, 29)

    def test_feb_2026_start(self):
        assert self._period_start(2026, 2) == datetime.date(2026, 1, 26)

    def test_nov_2025_start(self):
        assert self._period_start(2025, 11) == datetime.date(2025, 10, 27)

    def test_aug_2025_start(self):
        assert self._period_start(2025, 8) == datetime.date(2025, 7, 28)

    def test_feb_2028_start(self):
        assert self._period_start(2028, 2) == datetime.date(2028, 1, 31)
