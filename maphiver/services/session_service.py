import uuid
from datetime import datetime
from typing import Optional, List

from models.schemas import Session, SessionStatus
from repositories.database import SessionRepository, DocumentRepository
from utils.exceptions import SessionNotFoundError, SessionArchivedError, DocumentNotFoundError


def create_session(document_id: str) -> Session:
    session = Session(
        id=str(uuid.uuid4()),
        document_id=document_id,
        status=SessionStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return SessionRepository.create(session)


def get_session(session_id: str) -> Optional[Session]:
    return SessionRepository.get(session_id)


def update_session_status(session_id: str, status: SessionStatus) -> Session:
    session = get_session(session_id)
    if not session:
        raise SessionNotFoundError(f"Session {session_id} not found")
    if session.status == SessionStatus.ARCHIVED:
        raise SessionArchivedError(f"Session {session_id} is already archived")
    return SessionRepository.update_status(session_id, status)


def list_sessions(status: Optional[SessionStatus] = None) -> List[Session]:
    return SessionRepository.list_by_status(status)


def archive_session(session_id: str) -> Session:
    return update_session_status(session_id, SessionStatus.ARCHIVED)


def get_session_with_document(session_id: str) -> dict:
    session = get_session(session_id)
    if not session:
        raise SessionNotFoundError(f"Session {session_id} not found")
    
    document = DocumentRepository.get(session.document_id)
    
    return {
        "session": session,
        "document": document,
    }