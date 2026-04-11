from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
import json

from models.schemas import (
    AskRequest,
    AnswerChunk,
    ChunkType,
    QAMessage,
    QAHistoryResponse,
    QuickQuestion,
    QuickQuestionsResponse,
    MessageRole,
)
from services.qa_service import (
    stream_answer,
    get_messages,
    get_quick_question,
    get_context_blocks,
)
from repositories.database import DocumentRepository, SessionRepository
from utils.exceptions import SessionNotFoundError

router = APIRouter()


@router.post("/ask")
async def ask_question_api(request: AskRequest):
    async def generate():
        try:
            session = SessionRepository.get(request.session_id)
            if not session:
                yield f"data: {json.dumps({'type': 'error', 'error': '会话不存在'})}\n\n"
                return
            
            document = DocumentRepository.get(session.document_id)
            if not document:
                yield f"data: {json.dumps({'type': 'error', 'error': '文档不存在'})}\n\n"
                return
            
            blocks = []
            if document.parsed_at:
                from services.document_service import parse_document
                result = parse_document(document.id, use_ai_format=False)
                blocks = result.blocks
            
            context_text = get_context_blocks(
                blocks=blocks,
                selected_block_id=request.block_id,
                selected_text=request.selected_text,
            )
            
            for chunk in stream_answer(
                session_id=request.session_id,
                question=request.question,
                selected_text=request.selected_text,
                context_text=context_text,
                block_id=request.block_id,
            ):
                if chunk.type.value == "text":
                    answer_chunk = AnswerChunk(
                        type=ChunkType.TEXT,
                        content=chunk.content,
                    )
                    yield f"data: {json.dumps(answer_chunk.model_dump())}\n\n"
                elif chunk.type.value == "done":
                    done_chunk = AnswerChunk(type=ChunkType.DONE)
                    yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"
                elif chunk.type.value == "error":
                    error_chunk = AnswerChunk(
                        type=ChunkType.ERROR,
                        error=chunk.error_message,
                    )
                    yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"
                    
        except Exception as e:
            error_chunk = AnswerChunk(type=ChunkType.ERROR, error=str(e))
            yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history/{session_id}", response_model=QAHistoryResponse)
async def get_qa_history_api(session_id: str):
    messages = get_messages(session_id)
    
    qa_messages = []
    user_messages = [m for m in messages if m.role == MessageRole.USER]
    assistant_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
    
    for i, user_msg in enumerate(user_messages):
        if i < len(assistant_messages):
            assistant_msg = assistant_messages[i]
            qa_messages.append(QAMessage(
                id=user_msg.id,
                session_id=user_msg.session_id,
                question=user_msg.content,
                selected_text=user_msg.block_id or "",
                answer=assistant_msg.content,
                block_id=user_msg.block_id,
                created_at=user_msg.created_at,
            ))
    
    return QAHistoryResponse(messages=qa_messages)


@router.get("/quick-questions", response_model=QuickQuestionsResponse)
async def get_quick_questions_api():
    return QuickQuestionsResponse(
        questions=[
            QuickQuestion(type="详细", template="请详细解释这段内容"),
            QuickQuestion(type="简化", template="请用通俗的语言简化这段内容"),
            QuickQuestion(type="类比", template="请用一个类比来解释这段内容"),
            QuickQuestion(type="举例", template="请举一个具体的例子来说明这段内容"),
        ]
    )