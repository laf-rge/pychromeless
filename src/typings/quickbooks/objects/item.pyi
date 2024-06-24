from .base import QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

class Item(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Name: str
    Description: str
    Active: bool
    SubItem: bool
    FullyQualifiedName: str
    Taxable: bool
    SalesTaxIncluded: Incomplete
    UnitPrice: int
    Type: str
    Level: Incomplete
    PurchaseDesc: Incomplete
    PurchaseTaxIncluded: Incomplete
    PurchaseCost: Incomplete
    TrackQtyOnHand: bool
    QtyOnHand: Incomplete
    InvStartDate: Incomplete
    AssetAccountRef: Incomplete
    ExpenseAccountRef: Incomplete
    IncomeAccountRef: Incomplete
    SalesTaxCodeRef: Incomplete
    ParentRef: Incomplete
    PurchaseTaxCodeRef: Incomplete
    AbatementRate: Incomplete
    ReverseChargeRate: Incomplete
    ServiceType: Incomplete
    ItemCategoryType: Incomplete
    Sku: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self): ...
