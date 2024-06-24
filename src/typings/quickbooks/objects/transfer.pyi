from ..mixins import DeleteMixin as DeleteMixin
from .base import LinkedTxnMixin as LinkedTxnMixin, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

class Transfer(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin):
    class_dict: Incomplete
    qbo_object_name: str
    Amount: int
    TxnDate: Incomplete
    PrivateNote: Incomplete
    TxnSource: Incomplete
    FromAccountRef: Incomplete
    ToAccountRef: Incomplete
    def __init__(self) -> None: ...
