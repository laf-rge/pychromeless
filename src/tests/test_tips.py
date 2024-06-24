import unittest
from decimal import Decimal
from io import BytesIO
from unittest.mock import Mock, patch

from openpyxl import Workbook
from tips import Tips  # Assuming your class is in tips_module.py


class TestTips(unittest.TestCase):
    def setUp(self):
        self.tips = Tips()
        self.tips._a = Mock()

    def create_test_workbook(self):
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

    def test_exportTipsTransform(self):
        tips_stream = self.create_test_workbook()
        result = self.tips.exportTipsTransform(tips_stream)

        expected_output = (
            "last_name,first_name,title,paycheck_tips\n"
            "Doe,John,Crew (Primary),25.00\n"
            "Smith,Jane,Crew (Primary),50.00\n"
            "Black,Chris,Crew (Primary),30.00"
        )
        # self.assertEqual(result, expected_output)

    def test_getMissingPunches(self):
        self.tips._a.get.return_value = {  # type:ignore
            "users": [{"id": 1}, {"id": 2}],
            "times": [{"end_time": None}, {"end_time": "2021-02-20T08:00:00Z"}],
        }

        result = self.tips.getMissingPunches()

        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]["end_time"])


if __name__ == "__main__":
    unittest.main()
