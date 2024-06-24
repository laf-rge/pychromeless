from .base import QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete
from quickbooks.mixins import ListMixin as ListMixin, ReadMixin as ReadMixin

class TaxRate(QuickbooksTransactionEntity, QuickbooksBaseObject, ReadMixin, ListMixin):
    class_dict: Incomplete
    qbo_object_name: str
    Name: str
    Description: str
    RateValue: int
    SpecialTaxType: str
    Active: bool
    DisplayType: str
    EffectiveTaxRate: str
    AgencyRef: Incomplete
    TaxReturnLineRef: Incomplete
    def __init__(self) -> None: ...
