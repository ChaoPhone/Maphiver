from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from models.schemas import ExportRequest, ExportResponse
from repositories.database import (
    SessionRepository,
    DocumentRepository,
    CardRepository,
    MessageRepository,
)

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/", response_model=ExportResponse)
def export_session(request: ExportRequest):
    session = SessionRepository.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    document = DocumentRepository.get(session.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    content = _build_export_content(
        session_id=request.session_id,
        document=document,
        include_cards=request.include_cards,
        include_qa=request.include_qa,
        format=request.format,
    )
    
    filename = _generate_filename(document.filename, request.format)
    
    return ExportResponse(
        content=content,
        filename=filename,
        format=request.format,
    )


def _build_export_content(
    session_id: str,
    document,
    include_cards: bool,
    include_qa: bool,
    format: str,
) -> str:
    content_lines = []
    
    content_lines.append(f"# {document.filename}")
    content_lines.append("")
    content_lines.append("---")
    content_lines.append("")
    content_lines.append("## 文档信息")
    content_lines.append("")
    content_lines.append(f"- 文件名: {document.filename}")
    content_lines.append(f"- 页数: {document.page_count or '未知'}")
    content_lines.append(f"- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content_lines.append("")
    content_lines.append("---")
    content_lines.append("")
    
    if include_cards:
        cards = CardRepository.list_by_session(session_id)
        if cards:
            content_lines.append("## 知识卡片")
            content_lines.append("")
            for i, card in enumerate(cards, 1):
                content_lines.append(f"### 卡片 {i}")
                content_lines.append("")
                content_lines.append("**摘录内容：**")
                content_lines.append("")
                content_lines.append(card.source_text)
                content_lines.append("")
                if card.annotation:
                    content_lines.append(f"**批注：** {card.annotation}")
                    content_lines.append("")
                content_lines.append("---")
                content_lines.append("")
    
    if include_qa:
        messages = MessageRepository.list_by_session(session_id)
        qa_pairs = _group_messages_by_qa(messages)
        if qa_pairs:
            content_lines.append("## 问答记录")
            content_lines.append("")
            for i, (question, answer) in enumerate(qa_pairs, 1):
                content_lines.append(f"### 问答 {i}")
                content_lines.append("")
                content_lines.append(f"**问题：** {question}")
                content_lines.append("")
                content_lines.append(f"**回答：**")
                content_lines.append("")
                content_lines.append(answer)
                content_lines.append("")
                content_lines.append("---")
                content_lines.append("")
    
    return "\n".join(content_lines)


def _group_messages_by_qa(messages: List) -> List:
    pairs = []
    current_question = None
    
    for msg in messages:
        if msg.role.value == "user":
            current_question = msg.content
        elif msg.role.value == "assistant" and current_question:
            pairs.append((current_question, msg.content))
            current_question = None
    
    return pairs


def _generate_filename(original_filename: str, format: str) -> str:
    base_name = original_filename.replace(".pdf", "").replace(".md", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = "md" if format == "markdown" else format
    return f"{base_name}_export_{timestamp}.{extension}"