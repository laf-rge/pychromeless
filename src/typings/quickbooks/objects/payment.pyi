from ..client import QuickBooks as QuickBooks
from ..mixins import DeleteMixin as DeleteMixin, VoidMixin as VoidMixin
from .base import LinkedTxn as LinkedTxn, LinkedTxnMixin as LinkedTxnMixin, MetaData as MetaData, QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from .creditcardpayment import CreditCardPayment as CreditCardPayment
from _typeshed import Incomplete

class PaymentLine(QuickbooksBaseObject):
    list_dict: Incomplete
    Amount: int
    LinkedTxn: Incomplete
    def __init__(self) -> None: ...

class Payment(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin, VoidMixin):
    class_dict: Incomplete
    list_dict: Incomplete
    qbo_object_name: str
    PaymentRefNum: Incomplete
    TotalAmt: Incomplete
    UnappliedAmt: Incomplete
    ExchangeRate: Incomplete
    TxnDate: Incomplete
    TxnSource: Incomplete
    PrivateNote: Incomplete
    TxnStatus: Incomplete
    CreditCardPayment: Incomplete
    ARAccountRef: Incomplete
    CustomerRef: Incomplete
    CurrencyRef: Incomplete
    PaymentMethodRef: Incomplete
    DepositToAccountRef: Incomplete
    TaxExemptionRef: Incomplete
    MetaData: Incomplete
    Line: Incomplete
    TransactionLocationType: Incomplete
    def __init__(self) -> None: ...
