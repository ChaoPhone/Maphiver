from fastapi import APIRouter, HTTPException
from datetime import datetime

from models.schemas import (
    SessionResponse,
    SessionCreateRequest,
    SessionListResponse,
    DocumentResponse,
)
from services.session_service import (
    create_session,
    get_session,
    archive_session,
    list_sessions,
    get_session_with_document,
)
from repositories.database import DocumentRepository
from utils.exceptions import SessionNotFoundError, SessionArchivedError

router = APIRouter()


@router.post("/", response_model=SessionResponse)
async def create_session_api(request: SessionCreateRequest):
    document = DocumentRepository.get(request.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    session = create_session(request.document_id)
    
    return SessionResponse(
        id=session.id,
        document_id=session.document_id,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_api(session_id: str):
    try:
        data = get_session_with_document(session_id)
        session = data["session"]
        document = data["document"]
        
        doc_response = None
        if document:
            doc_response = DocumentResponse(
                id=document.id,
                filename=document.filename,
                file_path=document.file_path,
                page_count=document.page_count,
                created_at=document.created_at,
            )
        
        return SessionResponse(
            id=session.id,
            document_id=session.document_id,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            document=doc_response,
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")


@router.put("/{session_id}/archive", response_model=SessionResponse)
async def archive_session_api(session_id: str):
    try:
        session = archive_session(session_id)
        return SessionResponse(
            id=session.id,
            document_id=session.document_id,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except SessionArchivedError:
        raise HTTPException(status_code=400, detail="会话已归档")


@router.get("/", response_model=SessionListResponse)
async def list_sessions_api(status: str = None):
    from models.schemas import SessionStatus
    
    filter_status = None
    if status:
        try:
            filter_status = SessionStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的状态值")
    
    sessions = list_sessions(filter_status)
    
    session_responses = []
    for sess in sessions:
        session_responses.append(SessionResponse(
            id=sess.id,
            document_id=sess.document_id,
            status=sess.status,
            created_at=sess.created_at,
            updated_at=sess.updated_at,
        ))
    
    return SessionListResponse(
        sessions=session_responses,
        total=len(session_responses),
    )