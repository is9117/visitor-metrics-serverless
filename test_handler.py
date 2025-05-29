import json
import unittest
from unittest.mock import patch

from handler import lambda_handler, get_visitor_stats


class TestVisitorTracker(unittest.TestCase):

    @patch("handler.log_table")
    @patch("handler.count_table")
    def test_lambda_handler_new_visit(self, mock_count_table, mock_log_table):
        mock_log_table.get_item.return_value = {}
        mock_count_table.update_item.return_value = {}

        event = {
            "body": json.dumps({
                "path": "/test",
                "visitor_id": "abc-123",
                "date": "2025-05-29"
            })
        }

        response = lambda_handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Unique visit counted", body["message"])

        mock_log_table.put_item.assert_called_once()
        self.assertEqual(mock_count_table.update_item.call_count, 2)

    @patch("handler.log_table")
    @patch("handler.count_table")
    def test_lambda_handler_duplicate_visit(self, mock_count_table, mock_log_table):
        mock_log_table.get_item.return_value = {"Item": {"visit_id": "/test#2025-05-29"}}

        event = {
            "body": json.dumps({
                "path": "/test",
                "visitor_id": "abc-123",
                "date": "2025-05-29"
            })
        }

        response = lambda_handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Already counted", body["message"])
        mock_log_table.put_item.assert_not_called()
        mock_count_table.update_item.assert_not_called()

    @patch("handler.count_table")
    def test_get_visitor_stats(self, mock_count_table):
        mock_count_table.get_item.side_effect = [
            {"Item": {"visits": 100}},  # total count
            {"Item": {"visits": 25}},   # path count
        ]

        event = {
            "queryStringParameters": {"path": "/test"}
        }

        response = get_visitor_stats(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["path"], "/test")
        self.assertEqual(body["path_visits"], 25)
        self.assertEqual(body["total_visits"], 100)


if __name__ == "__main__":
    unittest.main()
