from typing import Optional


class MaphiverError(Exception):
    """基础异常类"""
    def __init__(self, message: str, detail: Optional[dict] = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(self.message)


class DocumentError(MaphiverError):
    """文档操作基础异常"""
    pass


class DocumentNotFoundError(DocumentError):
    """文档不存在"""
    pass


class DocumentUploadError(DocumentError):
    """文档上传失败"""
    pass


class ParseError(DocumentError):
    """文档解析失败"""
    pass


class SessionError(MaphiverError):
    """会话操作基础异常"""
    pass


class SessionNotFoundError(SessionError):
    """会话不存在"""
    pass


class SessionArchivedError(SessionError):
    """会话已归档，无法修改"""
    pass


class QAError(MaphiverError):
    """问答操作基础异常"""
    pass


class AIServiceError(QAError):
    """AI 服务调用失败"""
    pass


class CardError(MaphiverError):
    """知识卡片操作基础异常"""
    pass


class CardNotFoundError(CardError):
    """卡片不存在"""
    pass