from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class SessionStatus(str, Enum):
    DRAFT = "draft"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


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


class Document(BaseModel):
    id: str
    filename: str
    file_path: str
    page_count: Optional[int] = None
    parsed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Session(BaseModel):
    id: str
    document_id: str
    status: SessionStatus = SessionStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    block_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class KnowledgeCard(BaseModel):
    id: str
    session_id: str
    source_text: str
    annotation: Optional[str] = None
    block_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Footprint(BaseModel):
    id: str
    session_id: str
    message_id: Optional[str] = None
    action_type: str
    context: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ParseResult(BaseModel):
    document_id: str
    blocks: List[ContentBlock] = Field(default_factory=list)
    total_pages: int
    parsed_at: Optional[datetime] = None
    raw_markdown: Optional[str] = None


@dataclass
class StreamChunk:
    type: ChunkType
    content: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    
    def to_dict(self) -> dict:
        result = {"type": self.type.value}
        if self.content:
            result["content"] = self.content
        if self.error_message:
            result["error_message"] = self.error_message
        if self.metadata:
            result["metadata"] = self.metadata
        return result


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


class FootprintResponse(BaseModel):
    id: str
    session_id: str
    message_id: Optional[str] = None
    action_type: str
    context: Optional[dict] = None
    created_at: datetime


class FootprintListResponse(BaseModel):
    footprints: List[FootprintResponse]
    total: int


class FootprintCreateRequest(BaseModel):
    session_id: str
    action_type: str
    context: Optional[dict] = None
    message_id: Optional[str] = None


class CardResponse(BaseModel):
    id: str
    session_id: str
    source_text: str
    annotation: Optional[str] = None
    block_id: Optional[str] = None
    created_at: datetime


class CardListResponse(BaseModel):
    cards: List[CardResponse]
    total: int


class CardCreateRequest(BaseModel):
    session_id: str
    source_text: str
    annotation: Optional[str] = None
    block_id: Optional[str] = None


class CardUpdateRequest(BaseModel):
    annotation: str


class DocumentLink(BaseModel):
    id: str
    source_document_id: str
    target_document_id: str
    link_type: str = "reference"
    context: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class DocumentLinkResponse(BaseModel):
    id: str
    source_document_id: str
    target_document_id: str
    link_type: str
    context: Optional[str] = None
    target_document: Optional[DocumentResponse] = None
    created_at: datetime


class DocumentLinkListResponse(BaseModel):
    links: List[DocumentLinkResponse]
    total: int


class DocumentLinkCreateRequest(BaseModel):
    source_document_id: str
    target_document_id: str
    link_type: str = "reference"
    context: Optional[str] = None


class ExportRequest(BaseModel):
    session_id: str
    format: str = "markdown"
    include_cards: bool = True
    include_qa: bool = True


class ExportResponse(BaseModel):
    content: str
    filename: str
    format: str