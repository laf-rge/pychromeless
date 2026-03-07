"""Unit tests for FDMS statement import handler (async self-invocation)."""

import base64
import json
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock heavy dependencies before importing
_original_modules = {
    key: sys.modules.get(key)
    for key in [
        "quickbooks",
        "quickbooks.helpers",
        "quickbooks.objects",
        "quickbooks.objects.bill",
        "qb",
        "fdms_statement",
        "tips_processing",
    ]
}

sys.modules["quickbooks"] = MagicMock()
sys.modules["quickbooks.helpers"] = MagicMock()
sys.modules["quickbooks.objects"] = MagicMock()
sys.modules["quickbooks.objects.bill"] = MagicMock()

mock_qb = MagicMock()
sys.modules["qb"] = mock_qb

mock_fdms = MagicMock()
sys.modules["fdms_statement"] = mock_fdms

mock_tips = MagicMock()
sys.modules["tips_processing"] = mock_tips

# Need to import after mocking
from lambda_function import (  # noqa: E402
    _fdms_initiate_async,
    _fdms_process_async,
    create_response,
    fdms_statement_import_handler,
)

# Restore original modules
for key, original in _original_modules.items():
    if original is None:
        sys.modules.pop(key, None)
    else:
        sys.modules[key] = original


class TestFdmsInitiateAsync(unittest.TestCase):
    """Tests for Phase 1: _fdms_initiate_async."""

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.boto3")
    @patch("lambda_function.os")
    def test_phase1_stores_in_s3_and_self_invokes(
        self, mock_os, mock_boto3, mock_ws_cls
    ):
        """Phase 1: multipart event -> S3 upload + self-invoke + 202 response."""
        mock_os.environ = {
            "AWS_LAMBDA_FUNCTION_NAME": "fdms-statement-import-prod",
            "S3_BUCKET": "test-bucket",
        }

        # Mock decode_upload
        pdf_bytes = b"%PDF-fake-content"
        with patch("tips_processing.decode_upload", return_value={"file[]": pdf_bytes}):
            mock_s3 = MagicMock()
            mock_lambda = MagicMock()
            mock_boto3.client.side_effect = lambda svc, **kwargs: {
                "s3": mock_s3,
                "lambda": mock_lambda,
            }[svc]

            mock_context = MagicMock()
            mock_context.aws_request_id = "test-task-123"

            result = _fdms_initiate_async({}, mock_context)

        body = json.loads(result["body"])
        self.assertEqual(result["statusCode"], 202)
        self.assertEqual(body["task_id"], "test-task-123")

        # Verify S3 put
        mock_s3.put_object.assert_called_once()
        s3_call = mock_s3.put_object.call_args
        self.assertEqual(s3_call.kwargs["Bucket"], "test-bucket")
        self.assertTrue(s3_call.kwargs["Key"].startswith("tmp/fdms/"))

        # Verify Lambda self-invoke
        mock_lambda.invoke.assert_called_once()
        invoke_call = mock_lambda.invoke.call_args
        self.assertEqual(invoke_call.kwargs["InvocationType"], "Event")
        self.assertEqual(
            invoke_call.kwargs["FunctionName"], "fdms-statement-import-prod"
        )

    @patch("lambda_function.WebSocketManager")
    def test_phase1_no_pdf_files_returns_400(self, mock_ws_cls):
        """Phase 1: no PDF files -> 400 response + 'failed' broadcast."""
        with patch(
            "tips_processing.decode_upload", return_value={"other_field": "value"}
        ):
            result = _fdms_initiate_async({}, None)

        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("No PDF files", body["message"])

        # Verify failed broadcast
        ws = mock_ws_cls.return_value
        ws.broadcast_status.assert_called_once()
        call_kwargs = ws.broadcast_status.call_args.kwargs
        self.assertEqual(call_kwargs["status"], "failed")

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.os")
    def test_phase1_local_dev_calls_phase2_sync(self, mock_os, mock_ws_cls):
        """Local dev: synchronous fallback when not in AWS."""
        mock_os.environ = {}  # No AWS_LAMBDA_FUNCTION_NAME

        pdf_bytes = b"%PDF-fake-content"
        with (
            patch("tips_processing.decode_upload", return_value={"file[]": pdf_bytes}),
            patch("lambda_function._fdms_process_async") as mock_phase2,
        ):
            mock_phase2.return_value = create_response(200, {"success": True})
            _fdms_initiate_async({}, None)

        mock_phase2.assert_called_once()
        # Verify it passed _payload (not s3_key)
        phase2_event = mock_phase2.call_args[0][0]
        self.assertIn("_payload", phase2_event)
        self.assertNotIn("s3_key", phase2_event)


class TestFdmsProcessAsync(unittest.TestCase):
    """Tests for Phase 2: _fdms_process_async."""

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.boto3")
    @patch("lambda_function.os")
    def test_phase2_processes_from_s3(self, mock_os, mock_boto3, mock_ws_cls):
        """Phase 2: s3_key event -> S3 download + parse + create bills + broadcast + cleanup."""
        mock_os.environ = {"S3_BUCKET": "test-bucket"}

        pdf_bytes = b"%PDF-fake-content"
        payload = {
            "task_id": "task-456",
            "files": [
                {
                    "filename": "statement_1.pdf",
                    "data": base64.b64encode(pdf_bytes).decode(),
                },
            ],
        }

        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=json.dumps(payload).encode()))
        }
        mock_boto3.client.return_value = mock_s3

        # Mock fdms_statement functions
        mock_data = MagicMock()
        mock_data.store_number = "20358"
        mock_data.statement_month.strftime.side_effect = lambda fmt: (
            "January 2026" if fmt == "%B %Y" else "202601"
        )
        mock_data.interchange_program_fees = 100.0
        mock_data.service_charges = 50.0
        mock_data.total_fees = 25.0
        mock_data.chargebacks = []
        mock_data.adjustments = []

        with (
            patch("fdms_statement.parse_fdms_pdf", return_value=mock_data),
            patch("fdms_statement.create_fdms_bills", return_value=(3, None, None)),
        ):
            result = _fdms_process_async(
                {"s3_key": "tmp/fdms/task-456.json", "task_id": "task-456"}
            )

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertTrue(body["success"])
        self.assertEqual(body["summary"]["bills_created"], 3)

        # Verify S3 cleanup
        mock_s3.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="tmp/fdms/task-456.json"
        )

        # Verify completed broadcast includes full result
        ws = mock_ws_cls.return_value
        completed_calls = [
            c
            for c in ws.broadcast_status.call_args_list
            if c.kwargs.get("status") == "completed"
        ]
        self.assertEqual(len(completed_calls), 1)
        broadcast_result = completed_calls[0].kwargs["result"]
        self.assertIn("results", broadcast_result)
        self.assertIn("summary", broadcast_result)

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.boto3")
    @patch("lambda_function.os")
    def test_phase2_partial_failures(self, mock_os, mock_boto3, mock_ws_cls):
        """Phase 2: partial failures -> 'completed_with_errors' broadcast."""
        mock_os.environ = {"S3_BUCKET": "test-bucket"}

        pdf_bytes = b"%PDF-fake"
        payload = {
            "task_id": "task-789",
            "files": [
                {"filename": "good.pdf", "data": base64.b64encode(pdf_bytes).decode()},
                {"filename": "bad.pdf", "data": base64.b64encode(pdf_bytes).decode()},
            ],
        }

        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=json.dumps(payload).encode()))
        }
        mock_boto3.client.return_value = mock_s3

        mock_data = MagicMock()
        mock_data.store_number = "20358"
        mock_data.statement_month.strftime.side_effect = lambda fmt: (
            "January 2026" if fmt == "%B %Y" else "202601"
        )
        mock_data.interchange_program_fees = 100.0
        mock_data.service_charges = 50.0
        mock_data.total_fees = 25.0
        mock_data.chargebacks = []
        mock_data.adjustments = []

        call_count = 0

        def mock_parse(content):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Parse failed")
            return mock_data

        with (
            patch("fdms_statement.parse_fdms_pdf", side_effect=mock_parse),
            patch("fdms_statement.create_fdms_bills", return_value=(3, None, None)),
            patch("fdms_statement.FDMSParseError", Exception),
        ):
            result = _fdms_process_async(
                {"s3_key": "tmp/fdms/task-789.json", "task_id": "task-789"}
            )

        body = json.loads(result["body"])
        self.assertFalse(body["success"])
        self.assertEqual(body["summary"]["failed"], 1)

        ws = mock_ws_cls.return_value
        final_call = ws.broadcast_status.call_args_list[-1]
        self.assertEqual(final_call.kwargs["status"], "completed_with_errors")

    @patch("lambda_function.WebSocketManager")
    def test_phase2_inline_payload_local_dev(self, mock_ws_cls):
        """Local dev: Phase 2 with inline _payload (no S3)."""
        pdf_bytes = b"%PDF-fake"
        payload = {
            "task_id": "local-test",
            "files": [
                {"filename": "test.pdf", "data": base64.b64encode(pdf_bytes).decode()},
            ],
        }

        mock_data = MagicMock()
        mock_data.store_number = "20400"
        mock_data.statement_month.strftime.side_effect = lambda fmt: (
            "March 2026" if fmt == "%B %Y" else "202603"
        )
        mock_data.interchange_program_fees = 80.0
        mock_data.service_charges = 40.0
        mock_data.total_fees = 20.0
        mock_data.chargebacks = []
        mock_data.adjustments = []

        with (
            patch("fdms_statement.parse_fdms_pdf", return_value=mock_data),
            patch("fdms_statement.create_fdms_bills", return_value=(3, None, None)),
        ):
            result = _fdms_process_async({"task_id": "local-test", "_payload": payload})

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertTrue(body["success"])


class TestFdmsHandlerRouting(unittest.TestCase):
    """Tests for the top-level fdms_statement_import_handler routing."""

    @patch("lambda_function._fdms_process_async")
    def test_routes_to_phase2_when_s3_key_present(self, mock_phase2):
        """Handler routes to Phase 2 when event has s3_key."""
        mock_phase2.return_value = create_response(200, {"success": True})
        event = {"s3_key": "tmp/fdms/task-123.json", "task_id": "task-123"}

        fdms_statement_import_handler(event, None)
        mock_phase2.assert_called_once_with(event)

    @patch("lambda_function._fdms_initiate_async")
    def test_routes_to_phase1_for_http_events(self, mock_phase1):
        """Handler routes to Phase 1 for HTTP (multipart) events."""
        mock_phase1.return_value = create_response(202, {"task_id": "t"})
        event = {"body": "...", "isBase64Encoded": True}
        context = MagicMock()

        fdms_statement_import_handler(event, context)
        mock_phase1.assert_called_once_with(event, context)


if __name__ == "__main__":
    unittest.main()
