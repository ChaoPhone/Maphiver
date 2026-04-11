from typing import Optional


class MaphiverError(Exception):
    def __init__(self, message: str, detail: Optional[dict] = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(self.message)


class DocumentError(MaphiverError):
    pass


class DocumentNotFoundError(DocumentError):
    pass


class DocumentUploadError(DocumentError):
    pass


class ParseError(DocumentError):
    pass


class SessionError(MaphiverError):
    pass


class SessionNotFoundError(SessionError):
    pass


class SessionArchivedError(SessionError):
    pass


class QAError(MaphiverError):
    pass


class AIServiceError(QAError):
    pass


class CardError(MaphiverError):
    pass


class CardNotFoundError(CardError):
    pass