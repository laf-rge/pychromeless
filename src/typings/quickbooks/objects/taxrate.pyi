from _typeshed import Incomplete
from quickbooks.mixins import ListMixin as ListMixin
from quickbooks.mixins import ReadMixin as ReadMixin

from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

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
