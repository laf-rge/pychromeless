from .base import QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksManagedObject as QuickbooksManagedObject, Ref as Ref
from _typeshed import Incomplete

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
