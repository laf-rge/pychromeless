from _typeshed import Incomplete

class QuickbooksException(Exception):
    error_code: Incomplete
    detail: Incomplete
    message: Incomplete
    def __init__(self, message, error_code: int = 0, detail: str = '') -> None: ...
    def __iter__(self): ...

class AuthorizationException(QuickbooksException): ...
class UnsupportedException(QuickbooksException): ...
class GeneralException(QuickbooksException): ...
class ValidationException(QuickbooksException): ...
class SevereException(QuickbooksException): ...
class ObjectNotFoundException(QuickbooksException): ...
