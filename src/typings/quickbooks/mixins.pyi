from _typeshed import Incomplete

from .client import QuickBooks as QuickBooks
from .exceptions import QuickbooksException as QuickbooksException
from .utils import build_choose_clause as build_choose_clause
from .utils import build_where_clause as build_where_clause

class ToJsonMixin:
    def to_json(self): ...
    def json_filter(self): ...

class FromJsonMixin:
    class_dict: Incomplete
    list_dict: Incomplete
    @classmethod
    def from_json(cls, json_data): ...

def to_dict(obj, classkey: Incomplete | None = None): ...

class ToDictMixin:
    def to_dict(self): ...

class ReadMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    @classmethod
    def get(cls, id, qb: Incomplete | None = None): ...

class SendMixin:
    def send(self, qb: Incomplete | None = None, send_to: Incomplete | None = None): ...

class VoidMixin:
    def get_void_params(self): ...
    def get_void_data(self): ...
    def void(self, qb: Incomplete | None = None): ...

class UpdateMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    Id: Incomplete
    def save(
        self,
        qb: Incomplete | None = None,
        request_id: Incomplete | None = None,
        params: Incomplete | None = None,
    ): ...

class UpdateNoIdMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    def save(
        self, qb: Incomplete | None = None, request_id: Incomplete | None = None
    ): ...

class DeleteMixin:
    qbo_object_name: str
    def delete(
        self, qb: Incomplete | None = None, request_id: Incomplete | None = None
    ): ...

class DeleteNoIdMixin:
    qbo_object_name: str
    def delete(
        self, qb: Incomplete | None = None, request_id: Incomplete | None = None
    ): ...

class ListMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    @classmethod
    def all(
        cls,
        order_by: str = "",
        start_position: int | str = "",
        max_results: int = 100,
        qb: Incomplete | None = None,
    ): ...
    @classmethod
    def filter(
        cls,
        order_by: str = "",
        start_position: int | str = "",
        max_results: int | str = "",
        qb: Incomplete | None = None,
        **kwargs,
    ): ...
    @classmethod
    def choose(cls, choices, field: str = "Id", qb: Incomplete | None = None): ...
    @classmethod
    def where(
        cls,
        where_clause: str = "",
        order_by: str = "",
        start_position: int | str = "",
        max_results: int | str = "",
        qb: Incomplete | None = None,
    ): ...
    @classmethod
    def query(cls, select, qb: Incomplete | None = None): ...
    @classmethod
    def count(cls, where_clause: str = "", qb: Incomplete | None = None): ...

class QuickbooksPdfDownloadable:
    qbo_object_name: str
    def download_pdf(self, qb: Incomplete | None = None): ...

class ObjectListMixin:
    qbo_object_name: str
    def __iter__(self): ...
    def __len__(self) -> int: ...
    def __contains__(self, item) -> bool: ...
    def __getitem__(self, key): ...
    def __setitem__(self, key, value) -> None: ...
    def __delitem__(self, key) -> None: ...
    def __reversed__(self): ...
    def append(self, value) -> None: ...
    def pop(self, *args, **kwargs): ...

class PrefMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    @classmethod
    def get(cls, qb: Incomplete | None = None): ...
