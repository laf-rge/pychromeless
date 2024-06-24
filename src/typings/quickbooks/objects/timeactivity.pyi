from ..mixins import DeleteMixin as DeleteMixin
from .base import AttachableRef as AttachableRef, LinkedTxnMixin as LinkedTxnMixin, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

class TimeActivity(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin):
    class_dict: Incomplete
    qbo_object_name: str
    NameOf: str
    TxnDate: Incomplete
    BillableStatus: Incomplete
    Taxable: bool
    HourlyRate: Incomplete
    Hours: Incomplete
    Minutes: Incomplete
    BreakHours: Incomplete
    BreakMinutes: Incomplete
    StartTime: Incomplete
    EndTime: Incomplete
    Description: Incomplete
    VendorRef: Incomplete
    CustomerRef: Incomplete
    DepartmentRef: Incomplete
    EmployeeRef: Incomplete
    ItemRef: Incomplete
    ClassRef: Incomplete
    AttachableRef: Incomplete
    def __init__(self) -> None: ...
