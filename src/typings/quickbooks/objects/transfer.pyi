from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class Transfer(
    DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin
):
    class_dict: Incomplete
    qbo_object_name: str
    Amount: int
    TxnDate: Incomplete
    PrivateNote: Incomplete
    TxnSource: Incomplete
    FromAccountRef: Incomplete
    ToAccountRef: Incomplete
    def __init__(self) -> None: ...
