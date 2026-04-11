from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid

from models.schemas import (
    SessionResponse,
    SessionCreateRequest,
    SessionListResponse,
    DocumentResponse,
)

router = APIRouter()

MOCK_SESSIONS = {}


@router.post("/", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    session_id = str(uuid.uuid4())
    now = datetime.now()
    
    MOCK_SESSIONS[session_id] = {
        "id": session_id,
        "document_id": request.document_id,
        "status": "draft",
        "created_at": now,
        "updated_at": now,
    }
    
    return SessionResponse(**MOCK_SESSIONS[session_id])


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    if session_id not in MOCK_SESSIONS:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return SessionResponse(**MOCK_SESSIONS[session_id])


@router.put("/{session_id}/archive", response_model=SessionResponse)
async def archive_session(session_id: str):
    if session_id not in MOCK_SESSIONS:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    MOCK_SESSIONS[session_id]["status"] = "archived"
    MOCK_SESSIONS[session_id]["updated_at"] = datetime.now()
    
    return SessionResponse(**MOCK_SESSIONS[session_id])


@router.get("/", response_model=SessionListResponse)
async def list_sessions(status: str = None):
    sessions = []
    for sess in MOCK_SESSIONS.values():
        if status and sess["status"] != status:
            continue
        sessions.append(SessionResponse(**sess))
    
    return SessionListResponse(
        sessions=sessions,
        total=len(sessions),
    )