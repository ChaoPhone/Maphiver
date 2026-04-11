from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class SessionStatus(Enum):
    DRAFT = "draft"
    ARCHIVED = "archived"


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChunkType(Enum):
    TEXT = "text"
    DONE = "done"
    ERROR = "error"


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


class ContentBlock(BaseModel):
    id: str
    type: str = "text"
    page: Optional[int] = None
    chapter_path: List[str] = Field(default_factory=list)
    content: str


class ParseResult(BaseModel):
    document_id: str
    blocks: List[ContentBlock] = Field(default_factory=list)
    total_pages: int
    parsed_at: Optional[datetime] = None
    raw_markdown: Optional[str] = None


class QuestionContext(BaseModel):
    selected_text: str
    block_id: Optional[str] = None
    page: Optional[int] = None
    chapter_path: List[str] = Field(default_factory=list)


@dataclass
class StreamChunk:
    type: ChunkType
    content: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {"type": self.type.value}
        if self.content:
            result["content"] = self.content
        if self.error_message:
            result["error_message"] = self.error_message
        return result