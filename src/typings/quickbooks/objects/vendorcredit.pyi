from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .detailline import AccountBasedExpenseLine as AccountBasedExpenseLine
from .detailline import DetailLine as DetailLine
from .detailline import ItemBasedExpenseLine as ItemBasedExpenseLine
from .detailline import TDSLine as TDSLine

class VendorCredit(
    DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin
):
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
