from _typeshed import Incomplete

from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity

class TaxAgency(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    DisplayName: str
    TaxRegistrationNumber: str
    TaxTrackedOnSales: bool
    TaxTrackedOnPurchases: bool
    def __init__(self) -> None: ...
