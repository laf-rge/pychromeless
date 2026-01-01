from typing import Any, Iterator, Self

from _typeshed import Incomplete

from .client import QuickBooks as QuickBooks
from .exceptions import QuickbooksException as QuickbooksException
from .utils import build_choose_clause as build_choose_clause
from .utils import build_where_clause as build_where_clause

class ToJsonMixin:
    def to_json(self) -> str: ...
    def json_filter(self) -> dict[str, Any]: ...

class FromJsonMixin:
    class_dict: Incomplete
    list_dict: Incomplete
    @classmethod
    def from_json(cls, json_data: dict[str, Any]) -> Self: ...

def to_dict(obj: Any, classkey: Incomplete | None = None) -> dict[str, Any]: ...

class ToDictMixin:
    def to_dict(self) -> dict[str, Any]: ...

class ReadMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    @classmethod
    def get(cls, id: str | int, qb: Incomplete | None = None) -> Self: ...

class SendMixin:
    def send(
        self, qb: Incomplete | None = None, send_to: Incomplete | None = None
    ) -> Self: ...

class VoidMixin:
    def get_void_params(self) -> dict[str, Any]: ...
    def get_void_data(self) -> dict[str, Any]: ...
    def void(self, qb: Incomplete | None = None) -> Self: ...

class UpdateMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    Id: Incomplete
    def save(
        self,
        qb: Incomplete | None = None,
        request_id: Incomplete | None = None,
        params: Incomplete | None = None,
    ) -> Self: ...

class UpdateNoIdMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    def save(
        self, qb: Incomplete | None = None, request_id: Incomplete | None = None
    ) -> Self: ...

class DeleteMixin:
    qbo_object_name: str
    def delete(
        self, qb: Incomplete | None = None, request_id: Incomplete | None = None
    ) -> dict[str, Any]: ...

class DeleteNoIdMixin:
    qbo_object_name: str
    def delete(
        self, qb: Incomplete | None = None, request_id: Incomplete | None = None
    ) -> dict[str, Any]: ...

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
    ) -> list[Self]: ...
    @classmethod
    def filter(
        cls,
        order_by: str = "",
        start_position: int | str = "",
        max_results: int | str = "",
        qb: Incomplete | None = None,
        **kwargs: Any,
    ) -> list[Self]: ...
    @classmethod
    def choose(
        cls, choices: list[Any], field: str = "Id", qb: Incomplete | None = None
    ) -> list[Self]: ...
    @classmethod
    def where(
        cls,
        where_clause: str = "",
        order_by: str = "",
        start_position: int | str = "",
        max_results: int | str = "",
        qb: Incomplete | None = None,
    ) -> list[Self]: ...
    @classmethod
    def query(cls, select: str, qb: Incomplete | None = None) -> list[Self]: ...
    @classmethod
    def count(cls, where_clause: str = "", qb: Incomplete | None = None) -> int: ...

class QuickbooksPdfDownloadable:
    qbo_object_name: str
    def download_pdf(self, qb: Incomplete | None = None) -> bytes: ...

class ObjectListMixin:
    qbo_object_name: str
    def __iter__(self) -> Iterator[Any]: ...
    def __len__(self) -> int: ...
    def __contains__(self, item: Any) -> bool: ...
    def __getitem__(self, key: int) -> Any: ...
    def __setitem__(self, key: int, value: Any) -> None: ...
    def __delitem__(self, key: int) -> None: ...
    def __reversed__(self) -> Iterator[Any]: ...
    def append(self, value: Any) -> None: ...
    def pop(self, *args: Any, **kwargs: Any) -> Any: ...

class PrefMixin:
    qbo_object_name: str
    qbo_json_object_name: str
    @classmethod
    def get(cls, qb: Incomplete | None = None) -> Self: ...
