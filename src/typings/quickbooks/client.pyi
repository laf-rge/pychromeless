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
    def __new__(cls, **kwargs): ...
    @property
    def api_url(self): ...
    def validate_webhook_signature(
        self, request_body, signature, verifier_token: Incomplete | None = None
    ): ...
    def get_current_user(self): ...
    def get_report(self, report_type, qs: Incomplete | None = None): ...
    def change_data_capture(self, entity_string, changed_since): ...
    def make_request(
        self,
        request_type,
        url,
        request_body: Incomplete | None = None,
        content_type: str = "application/json",
        params: Incomplete | None = None,
        file_path: Incomplete | None = None,
        request_id: Incomplete | None = None,
    ): ...
    def get(self, *args, **kwargs): ...
    def post(self, *args, **kwargs): ...
    def process_request(
        self, request_type, url, headers: str = "", params: str = "", data: str = ""
    ): ...
    def get_single_object(self, qbbo, pk): ...
    @staticmethod
    def handle_exceptions(results) -> None: ...
    def create_object(
        self,
        qbbo,
        request_body,
        _file_path: Incomplete | None = None,
        request_id: Incomplete | None = None,
        params: Incomplete | None = None,
    ): ...
    def query(self, select, params: Incomplete | None = None): ...
    def isvalid_object_name(self, object_name): ...
    def update_object(
        self,
        qbbo,
        request_body,
        _file_path: Incomplete | None = None,
        request_id: Incomplete | None = None,
        params: Incomplete | None = None,
    ): ...
    def delete_object(
        self,
        qbbo,
        request_body,
        _file_path: Incomplete | None = None,
        request_id: Incomplete | None = None,
    ): ...
    def batch_operation(self, request_body): ...
    def misc_operation(
        self, end_point, request_body, content_type: str = "application/json"
    ): ...
    def download_pdf(self, qbbo, item_id): ...
