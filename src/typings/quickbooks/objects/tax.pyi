from _typeshed import Incomplete

from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import Ref as Ref

class TaxLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    PercentBased: bool
    TaxPercent: int
    NetAmountTaxable: int
    def __init__(self) -> None: ...

class TaxLine(QuickbooksBaseObject):
    class_dict: Incomplete
    Amount: int
    DetailType: str
    def __init__(self) -> None: ...

class TxnTaxDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    list_dict: Incomplete
    TotalTax: int
    TxnTaxCodeRef: Incomplete
    TaxLine: Incomplete
    def __init__(self) -> None: ...
