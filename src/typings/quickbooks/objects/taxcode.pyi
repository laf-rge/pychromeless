from _typeshed import Incomplete
from quickbooks.mixins import ListMixin as ListMixin
from quickbooks.mixins import ReadMixin as ReadMixin

from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class TaxRateDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    qbo_object_name: str
    TaxTypeApplicable: str
    TaxOrder: int
    TaxRateRef: Incomplete
    def __init__(self) -> None: ...

class TaxRateList(QuickbooksBaseObject):
    list_dict: Incomplete
    qbo_object_name: str
    TaxRateDetail: Incomplete
    def __init__(self) -> None: ...

class TaxCode(QuickbooksTransactionEntity, QuickbooksBaseObject, ReadMixin, ListMixin):
    class_dict: Incomplete
    qbo_object_name: str
    Name: Incomplete
    Description: Incomplete
    Taxable: Incomplete
    TaxGroup: Incomplete
    Active: bool
    SalesTaxRateList: Incomplete
    PurchaseTaxRateList: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self): ...
