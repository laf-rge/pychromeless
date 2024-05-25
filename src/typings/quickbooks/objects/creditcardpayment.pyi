from .base import QuickbooksBaseObject as QuickbooksBaseObject
from _typeshed import Incomplete

class CreditChargeInfo(QuickbooksBaseObject):
    class_dict: Incomplete
    Type: str
    NameOnAcct: str
    CcExpiryMonth: int
    CcExpiryYear: int
    BillAddrStreet: str
    PostalCode: str
    Amount: int
    ProcessPayment: bool
    def __init__(self) -> None: ...

class CreditChargeResponse(QuickbooksBaseObject):
    CCTransId: str
    AuthCode: str
    TxnAuthorizationTime: str
    Status: str
    def __init__(self) -> None: ...

class CreditCardPayment(QuickbooksBaseObject):
    class_dict: Incomplete
    CreditChargeInfo: Incomplete
    CreditChargeResponse: Incomplete
    def __init__(self) -> None: ...
