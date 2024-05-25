from .base import QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity
from _typeshed import Incomplete

class TaxAgency(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    DisplayName: str
    TaxRegistrationNumber: str
    TaxTrackedOnSales: bool
    TaxTrackedOnPurchases: bool
    def __init__(self) -> None: ...
