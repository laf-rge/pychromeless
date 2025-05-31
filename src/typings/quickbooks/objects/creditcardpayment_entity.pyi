from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import MetaData as MetaData
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class CreditCardPayment(
    DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin
):
    class_dict: Incomplete
    qbo_object_name: str
    qbo_json_object_name: str
    TxnDate: Incomplete
    Amount: int
    PrivateNote: Incomplete
    Memo: Incomplete
    PrintStatus: Incomplete
    CheckNum: Incomplete
    BankAccountRef: Incomplete
    CreditCardAccountRef: Incomplete
    VendorRef: Incomplete
    MetaData: Incomplete
    def __init__(self) -> None: ...
