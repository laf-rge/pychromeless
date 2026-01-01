from typing import Any

from _typeshed import Incomplete

from . import exceptions as exceptions

to_bytes: Incomplete

class Environments:
    SANDBOX: str
    PRODUCTION: str

class QuickBooks:
    company_id: int
    session: Incomplete
    auth_client: Incomplete
    sandbox: bool
    minorversion: Incomplete
    verifier_token: Incomplete
    invoice_link: bool
    sandbox_api_url_v3: str
    api_url_v3: str
    current_user_url: str
    def __new__(cls, **kwargs: Any) -> QuickBooks: ...
    @property
    def api_url(self) -> str: ...
    def validate_webhook_signature(
        self,
        request_body: Any,
        signature: str,
        verifier_token: Incomplete | None = None,
    ) -> bool: ...
    def get_current_user(self) -> dict[str, Any]: ...
    def get_report(
        self, report_type: str, qs: Incomplete | None = None
    ) -> dict[str, Any]: ...
    def change_data_capture(
        self, entity_string: str, changed_since: str
    ) -> dict[str, Any]: ...
    def make_request(
        self,
        request_type: str,
        url: str,
        request_body: Incomplete | None = None,
        content_type: str = "application/json",
        params: Incomplete | None = None,
        file_path: Incomplete | None = None,
        request_id: Incomplete | None = None,
    ) -> dict[str, Any]: ...
    def get(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...
    def post(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...
    def process_request(
        self,
        request_type: str,
        url: str,
        headers: str = "",
        params: str = "",
        data: str = "",
    ) -> Any: ...
    def get_single_object(self, qbbo: str, pk: str | int) -> dict[str, Any]: ...
    @staticmethod
    def handle_exceptions(results: dict[str, Any]) -> None: ...
    def create_object(
        self,
        qbbo: str,
        request_body: dict[str, Any],
        _file_path: Incomplete | None = None,
        request_id: Incomplete | None = None,
        params: Incomplete | None = None,
    ) -> dict[str, Any]: ...
    def query(
        self, select: str, params: Incomplete | None = None
    ) -> list[dict[str, Any]]: ...
    def isvalid_object_name(self, object_name: str) -> bool: ...
    def update_object(
        self,
        qbbo: str,
        request_body: dict[str, Any],
        _file_path: Incomplete | None = None,
        request_id: Incomplete | None = None,
        params: Incomplete | None = None,
    ) -> dict[str, Any]: ...
    def delete_object(
        self,
        qbbo: str,
        request_body: dict[str, Any],
        _file_path: Incomplete | None = None,
        request_id: Incomplete | None = None,
    ) -> dict[str, Any]: ...
    def batch_operation(self, request_body: dict[str, Any]) -> dict[str, Any]: ...
    def misc_operation(
        self,
        end_point: str,
        request_body: dict[str, Any],
        content_type: str = "application/json",
    ) -> dict[str, Any]: ...
    def download_pdf(self, qbbo: str, item_id: str | int) -> bytes: ...
