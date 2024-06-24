from ..mixins import DeleteMixin as DeleteMixin
from .base import LinkedTxnMixin as LinkedTxnMixin, MetaData as MetaData, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

class CreditCardPayment(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin):
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
