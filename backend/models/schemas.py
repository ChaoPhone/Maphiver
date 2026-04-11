from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class SessionStatus(str, Enum):
    DRAFT = "draft"
    ARCHIVED = "archived"


class ChunkType(str, Enum):
    TEXT = "text"
    DONE = "done"
    ERROR = "error"


class ContentBlock(BaseModel):
    id: str
    type: str = "text"
    page: Optional[int] = None
    chapter_path: List[str] = Field(default_factory=list)
    content: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    page_count: Optional[int] = None
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str = "uploaded"
    message: str = "文档上传成功"


class ParseProgressChunk(BaseModel):
    type: str
    progress: Optional[int] = None
    stage: Optional[str] = None
    block: Optional[ContentBlock] = None
    total_pages: Optional[int] = None
    raw_markdown: Optional[str] = None
    blocks: Optional[List[ContentBlock]] = None
    error: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    document_id: str
    status: SessionStatus = SessionStatus.DRAFT
    created_at: datetime
    updated_at: datetime
    document: Optional[DocumentResponse] = None


class SessionCreateRequest(BaseModel):
    document_id: str


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


class AskRequest(BaseModel):
    session_id: str
    question: str
    selected_text: str
    block_id: Optional[str] = None
    question_type: Optional[str] = None


class AnswerChunk(BaseModel):
    type: ChunkType
    content: Optional[str] = None
    error: Optional[str] = None


class QAMessage(BaseModel):
    id: str
    session_id: str
    question: str
    selected_text: str
    answer: str
    block_id: Optional[str] = None
    created_at: datetime


class QAHistoryResponse(BaseModel):
    messages: List[QAMessage]


class QuickQuestion(BaseModel):
    type: str
    template: str


class QuickQuestionsResponse(BaseModel):
    questions: List[QuickQuestion]


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)