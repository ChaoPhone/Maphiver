from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import uuid

from models.schemas import (
    AskRequest,
    AnswerChunk,
    ChunkType,
    QAMessage,
    QAHistoryResponse,
    QuickQuestion,
    QuickQuestionsResponse,
)

router = APIRouter()

MOCK_QA_HISTORY = {}


@router.post("/ask")
async def ask_question(request: AskRequest):
    async def generate():
        mock_answer = "这是一个模拟的 AI 回答。在实际实现中，这里会调用 DeepSeek API 进行流式生成。"
        
        for char in mock_answer[:20]:
            chunk = AnswerChunk(
                type=ChunkType.TEXT,
                content=char,
            )
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        
        done_chunk = AnswerChunk(type=ChunkType.DONE)
        yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"
        
        message_id = str(uuid.uuid4())
        MOCK_QA_HISTORY[message_id] = {
            "id": message_id,
            "session_id": request.session_id,
            "question": request.question,
            "selected_text": request.selected_text,
            "answer": mock_answer,
            "block_id": request.block_id,
            "created_at": datetime.now(),
        }
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history/{session_id}", response_model=QAHistoryResponse)
async def get_qa_history(session_id: str):
    messages = []
    for msg in MOCK_QA_HISTORY.values():
        if msg["session_id"] == session_id:
            messages.append(QAMessage(**msg))
    
    return QAHistoryResponse(messages=messages)


@router.get("/quick-questions", response_model=QuickQuestionsResponse)
async def get_quick_questions():
    return QuickQuestionsResponse(
        questions=[
            QuickQuestion(type="详细", template="请详细解释这段内容"),
            QuickQuestion(type="简化", template="请用通俗的语言简化这段内容"),
            QuickQuestion(type="类比", template="请用一个类比来解释这段内容"),
            QuickQuestion(type="举例", template="请举一个具体的例子来说明这段内容"),
        ]
    )