from ..mixins import FromJsonMixin as FromJsonMixin
from ..mixins import ObjectListMixin as ObjectListMixin

class CDCResponse(FromJsonMixin):
    qbo_object_name: str
    def __init__(self) -> None: ...

class QueryResponse(FromJsonMixin, ObjectListMixin):
    qbo_object_name: str
    def __init__(self) -> None: ...
