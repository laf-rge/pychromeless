from _typeshed import Incomplete

from ..mixins import FromJsonMixin as FromJsonMixin
from ..mixins import ToJsonMixin as ToJsonMixin

class BatchOperation:
    CREATE: str
    UPDATE: str
    DELETE: str

class FaultError(FromJsonMixin):
    qbo_object_name: str
    Message: str
    code: str
    Detail: str
    element: str
    def __init__(self) -> None: ...

class Fault(FromJsonMixin):
    list_dict: Incomplete
    qbo_object_name: str
    type: str
    original_object: Incomplete
    Error: Incomplete
    def __init__(self) -> None: ...

class BatchItemResponse(FromJsonMixin):
    qbo_object_name: str
    bId: str
    list_dict: Incomplete
    class_dict: Incomplete
    Fault: Incomplete
    def __init__(self) -> None: ...
    def set_object(self, obj) -> None: ...
    def get_object(self): ...

class BatchResponse:
    batch_responses: Incomplete
    original_list: Incomplete
    successes: Incomplete
    faults: Incomplete
    def __init__(self) -> None: ...

class BatchItemRequest(ToJsonMixin):
    class_dict: Incomplete
    list_dict: Incomplete
    qbo_object_name: str
    bId: str
    operation: str
    def __init__(self) -> None: ...
    def set_object(self, obj) -> None: ...
    def get_object(self): ...

class IntuitBatchRequest(ToJsonMixin):
    list_dict: Incomplete
    BatchItemRequest: Incomplete
    def __init__(self) -> None: ...
