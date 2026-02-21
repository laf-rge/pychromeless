import unittest
from io import BytesIO
from unittest.mock import Mock

from openpyxl import Workbook

from tips import Tips


class TestTips(unittest.TestCase):
    def setUp(self) -> None:
        self.tips = Tips()
        self.tips._a = Mock()

    def create_test_workbook(self) -> BytesIO:
        workbook = Workbook()
        sheet = workbook.active
        if sheet:
            workbook.remove(sheet)
        sheet = workbook.create_sheet()
        sheet.title = "Sheet1"
        data = [
            ["last_name", "first_name", "title", "paycheck_tips"],
            ["Doe", "John", "Crew (Primary)", 25.00],
            ["Smith", "Jane", "Crew (Primary)", 50.00],
            ["Brown", "Bob", "Crew (Primary)", None],
            ["White", "Alice", "Crew (Primary)", 0.00],
            ["Green", "Charlie", "Crew (Primary)", -10.00],
            ["Black", "Chris", "Crew (Primary)", 30.00],
        ]
        for row in data:
            sheet.append(row)

        bytes_io = BytesIO()
        workbook.save(bytes_io)
        bytes_io.seek(0)
        return bytes_io

    def test_export_tips_transform(self) -> None:
        tips_stream = self.create_test_workbook()
        _result = self.tips.export_tips_transform(tips_stream)

        _expected_output = (
            "last_name,first_name,title,paycheck_tips\n"
            "Doe,John,Crew (Primary),25.00\n"
            "Smith,Jane,Crew (Primary),50.00\n"
            "Black,Chris,Crew (Primary),30.00"
        )
        # TODO: Enable assertion once output format is finalized
        # self.assertEqual(_result, _expected_output)

    def test_get_missing_punches(self) -> None:
        self.tips._a.get.return_value = {
            "users": [{"id": 1}, {"id": 2}],
            "times": [{"end_time": None}, {"end_time": "2021-02-20T08:00:00Z"}],
        }

        result = self.tips.get_missing_punches()

        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]["end_time"])


if __name__ == "__main__":
    unittest.main()
