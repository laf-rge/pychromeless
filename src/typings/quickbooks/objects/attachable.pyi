from _typeshed import Incomplete

from ..client import QuickBooks as QuickBooks
from ..mixins import DeleteMixin as DeleteMixin
from .base import AttachableRef as AttachableRef
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class Attachable(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    list_dict: Incomplete
    qbo_object_name: str
    AttachableRef: Incomplete
    FileName: Incomplete
    Note: str
    FileAccessUri: Incomplete
    TempDownloadUri: Incomplete
    Size: Incomplete
    ContentType: Incomplete
    Category: Incomplete
    Lat: Incomplete
    Long: Incomplete
    PlaceName: Incomplete
    ThumbnailFileAccessUri: Incomplete
    ThumbnailTempDownloadUri: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self): ...
    Id: Incomplete
    def save(
        self,
        qb: Incomplete | None = None,
        request_id: Incomplete | None = None,
        params: Incomplete | None = None,
    ): ...
