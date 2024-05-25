from ..mixins import DeleteMixin as DeleteMixin
from .base import LinkedTxnMixin as LinkedTxnMixin, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from .detailline import AccountBasedExpenseLine as AccountBasedExpenseLine, DetailLine as DetailLine, ItemBasedExpenseLine as ItemBasedExpenseLine, TDSLine as TDSLine
from _typeshed import Incomplete

class VendorCredit(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    DocNumber: str
    TxnDate: str
    PrivateNote: str
    TotalAmt: int
    ExchangeRate: int
    GlobalTaxCalculation: str
    FromAccountRef: Ref
    ToAccountRef: Ref
    Line: Incomplete
    VendorRef: Ref
    APAccountRef: Ref
    DepartmentRef: Ref | None
    CurrencyRef: Ref
    def __init__(self) -> None: ...
