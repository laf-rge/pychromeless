from .base import QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete
from quickbooks.mixins import ListMixin as ListMixin, ReadMixin as ReadMixin

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
