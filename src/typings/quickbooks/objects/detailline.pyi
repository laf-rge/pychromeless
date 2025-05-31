from decimal import Decimal

from _typeshed import Incomplete

from .base import CustomField as CustomField
from .base import LinkedTxn as LinkedTxn
from .base import MarkupInfo as MarkupInfo
from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import Ref as Ref

class DetailLine(QuickbooksBaseObject):
    list_dict: Incomplete
    Id: Incomplete
    LineNum: int
    Description: Incomplete
    Amount: Decimal
    DetailType: str
    LinkedTxn: Incomplete
    CustomField: Incomplete
    def __init__(self) -> None: ...

class DiscountOverride(QuickbooksBaseObject):
    class_dict: Incomplete
    qbo_object_name: str
    PercentBased: bool
    DiscountPercent: int
    DiscountRef: Incomplete
    DiscountAccountRef: Incomplete
    def __init__(self) -> None: ...

class DiscountLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    Discount: Incomplete
    ClassRef: Incomplete
    TaxCodeRef: Incomplete
    DiscountAccountRef: Incomplete
    PercentBased: bool
    DiscountPercent: int
    def __init__(self) -> None: ...

class DiscountLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    DiscountLineDetail: Incomplete
    def __init__(self) -> None: ...

class SubtotalLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    ItemRef: Incomplete
    def __init__(self) -> None: ...

class SubtotalLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    SubtotalLineDetail: Incomplete
    def __init__(self) -> None: ...

class DescriptionLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    ServiceDate: str
    TaxCodeRef: Incomplete
    def __init__(self) -> None: ...

class SalesItemLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    UnitPrice: int
    Qty: int
    ServiceDate: str
    TaxInclusiveAmt: int
    MarkupInfo: Incomplete
    ItemRef: Incomplete
    ItemAccountRef: Incomplete
    ClassRef: Incomplete
    TaxCodeRef: Incomplete
    PriceLevelRef: Incomplete
    def __init__(self) -> None: ...

class SalesItemLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    SalesItemLineDetail: Incomplete
    def __init__(self) -> None: ...

class GroupLineDetail(QuickbooksBaseObject): ...

class GroupLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    GroupLineDetail: Incomplete
    def __init__(self) -> None: ...

class DescriptionOnlyLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    DescriptionLineDetail: Incomplete
    def __init__(self) -> None: ...

class AccountBasedExpenseLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    BillableStatus: Incomplete
    TaxInclusiveAmt: int
    CustomerRef: Incomplete
    AccountRef: Incomplete
    TaxCodeRef: Incomplete
    ClassRef: Incomplete
    MarkupInfo: Incomplete
    def __init__(self) -> None: ...

class AccountBasedExpenseLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    AccountBasedExpenseLineDetail: Incomplete
    def __init__(self) -> None: ...

class TDSLineDetail(QuickbooksBaseObject):
    TDSSectionTypeId: Incomplete
    def __init__(self) -> None: ...

class TDSLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    TDSLineDetail: Incomplete
    def __init__(self) -> None: ...

class ItemBasedExpenseLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    BillableStatus: Incomplete
    UnitPrice: int
    Qty: int
    TaxInclusiveAmt: int
    ItemRef: Incomplete
    ClassRef: Incomplete
    PriceLevelRef: Incomplete
    TaxCodeRef: Incomplete
    MarkupInfo: Incomplete
    CustomerRef: Incomplete
    def __init__(self) -> None: ...

class ItemBasedExpenseLine(DetailLine):
    class_dict: Incomplete
    DetailType: str
    ItemBasedExpenseLineDetail: Incomplete
    def __init__(self) -> None: ...
