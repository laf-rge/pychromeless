from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .detailline import DescriptionOnlyLine as DescriptionOnlyLine
from .detailline import DetailLine as DetailLine
from .tax import TxnTaxDetail as TxnTaxDetail

class Entity(QuickbooksBaseObject):
    class_dict: Incomplete
    Type: str
    EntityRef: Incomplete
    def __init__(self) -> None: ...

class JournalEntryLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    PostingType: str
    TaxApplicableOn: str
    TaxAmount: int
    BillableStatus: Incomplete
    Entity: Incomplete
    AccountRef: Incomplete
    ClassRef: Incomplete
    DepartmentRef: Incomplete
    TaxCodeRef: Incomplete
    def __init__(self) -> None: ...

class JournalEntryLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    JournalEntryLineDetail: Incomplete
    def __init__(self) -> None: ...

class JournalEntry(
    DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin
):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    Adjustment: bool
    TxnDate: str
    DocNumber: str
    PrivateNote: str
    TotalAmt: int
    ExchangeRate: int
    Line: Incomplete
    TxnTaxDetail: Incomplete
    CurrencyRef: Incomplete
    def __init__(self) -> None: ...
