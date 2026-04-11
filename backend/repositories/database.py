import sqlite3
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from config import DATABASE_PATH
from models.schemas import (
    Document,
    Session,
    SessionStatus,
    Message,
    MessageRole,
    KnowledgeCard,
    Footprint,
)
from utils.exceptions import (
    DocumentNotFoundError,
    SessionNotFoundError,
    CardNotFoundError,
)


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    page_count INTEGER,
    parsed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'archived')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    block_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS knowledge_cards (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    source_text TEXT NOT NULL,
    annotation TEXT,
    block_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS footprints (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    message_id TEXT,
    action_type TEXT NOT NULL,
    context TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_document ON sessions(document_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_cards_session ON knowledge_cards(session_id);
CREATE INDEX IF NOT EXISTS idx_footprints_session ON footprints(session_id);
"""


def init_db():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.executescript(CREATE_TABLES_SQL)
    conn.commit()
    conn.close()


def _get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except:
        return None


class DocumentRepository:
    @staticmethod
    def create(doc: Document) -> Document:
        conn = _get_connection()
        conn.execute(
            """
            INSERT INTO documents (id, filename, file_path, page_count, parsed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                doc.id,
                doc.filename,
                doc.file_path,
                doc.page_count,
                doc.parsed_at.isoformat() if doc.parsed_at else None,
                doc.created_at.isoformat() if doc.created_at else datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        return doc

    @staticmethod
    def get(document_id: str) -> Optional[Document]:
        conn = _get_connection()
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return Document(
            id=row["id"],
            filename=row["filename"],
            file_path=row["file_path"],
            page_count=row["page_count"],
            parsed_at=_parse_datetime(row["parsed_at"]),
            created_at=_parse_datetime(row["created_at"]) or datetime.now(),
        )

    @staticmethod
    def update_parsed(document_id: str, page_count: int, parsed_at: datetime) -> Document:
        conn = _get_connection()
        conn.execute(
            """
            UPDATE documents SET page_count = ?, parsed_at = ?
            WHERE id = ?
            """,
            (page_count, parsed_at.isoformat(), document_id),
        )
        conn.commit()
        conn.close()
        return DocumentRepository.get(document_id)

    @staticmethod
    def delete(document_id: str) -> bool:
        conn = _get_connection()
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def list_all() -> List[Document]:
        conn = _get_connection()
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [
            Document(
                id=row["id"],
                filename=row["filename"],
                file_path=row["file_path"],
                page_count=row["page_count"],
                parsed_at=_parse_datetime(row["parsed_at"]),
                created_at=_parse_datetime(row["created_at"]) or datetime.now(),
            )
            for row in rows
        ]


class SessionRepository:
    @staticmethod
    def create(session: Session) -> Session:
        conn = _get_connection()
        now = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO sessions (id, document_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.document_id,
                session.status.value,
                session.created_at.isoformat() if session.created_at else now,
                session.updated_at.isoformat() if session.updated_at else now,
            ),
        )
        conn.commit()
        conn.close()
        return session

    @staticmethod
    def get(session_id: str) -> Optional[Session]:
        conn = _get_connection()
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return Session(
            id=row["id"],
            document_id=row["document_id"],
            status=SessionStatus(row["status"]),
            created_at=_parse_datetime(row["created_at"]) or datetime.now(),
            updated_at=_parse_datetime(row["updated_at"]) or datetime.now(),
        )

    @staticmethod
    def update_status(session_id: str, status: SessionStatus) -> Session:
        conn = _get_connection()
        conn.execute(
            """
            UPDATE sessions SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, datetime.now().isoformat(), session_id),
        )
        conn.commit()
        conn.close()
        return SessionRepository.get(session_id)

    @staticmethod
    def list_by_status(status: Optional[SessionStatus] = None) -> List[Session]:
        conn = _get_connection()
        if status:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC",
                (status.value,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        conn.close()
        return [
            Session(
                id=row["id"],
                document_id=row["document_id"],
                status=SessionStatus(row["status"]),
                created_at=_parse_datetime(row["created_at"]) or datetime.now(),
                updated_at=_parse_datetime(row["updated_at"]) or datetime.now(),
            )
            for row in rows
        ]


class MessageRepository:
    @staticmethod
    def create(message: Message) -> Message:
        conn = _get_connection()
        conn.execute(
            """
            INSERT INTO messages (id, session_id, role, content, block_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.session_id,
                message.role.value,
                message.content,
                message.block_id,
                message.created_at.isoformat() if message.created_at else datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        return message

    @staticmethod
    def list_by_session(session_id: str) -> List[Message]:
        conn = _get_connection()
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
        conn.close()
        return [
            Message(
                id=row["id"],
                session_id=row["session_id"],
                role=MessageRole(row["role"]),
                content=row["content"],
                block_id=row["block_id"],
                created_at=_parse_datetime(row["created_at"]) or datetime.now(),
            )
            for row in rows
        ]


class CardRepository:
    @staticmethod
    def create(card: KnowledgeCard) -> KnowledgeCard:
        conn = _get_connection()
        conn.execute(
            """
            INSERT INTO knowledge_cards (id, session_id, source_text, annotation, block_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                card.id,
                card.session_id,
                card.source_text,
                card.annotation,
                card.block_id,
                card.created_at.isoformat() if card.created_at else datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        return card

    @staticmethod
    def get(card_id: str) -> Optional[KnowledgeCard]:
        conn = _get_connection()
        row = conn.execute(
            "SELECT * FROM knowledge_cards WHERE id = ?", (card_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return KnowledgeCard(
            id=row["id"],
            session_id=row["session_id"],
            source_text=row["source_text"],
            annotation=row["annotation"],
            block_id=row["block_id"],
            created_at=_parse_datetime(row["created_at"]) or datetime.now(),
        )

    @staticmethod
    def list_by_session(session_id: Optional[str] = None) -> List[KnowledgeCard]:
        conn = _get_connection()
        if session_id:
            rows = conn.execute(
                "SELECT * FROM knowledge_cards WHERE session_id = ? ORDER BY created_at DESC",
                (session_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM knowledge_cards ORDER BY created_at DESC"
            ).fetchall()
        conn.close()
        return [
            KnowledgeCard(
                id=row["id"],
                session_id=row["session_id"],
                source_text=row["source_text"],
                annotation=row["annotation"],
                block_id=row["block_id"],
                created_at=_parse_datetime(row["created_at"]) or datetime.now(),
            )
            for row in rows
        ]

    @staticmethod
    def update_annotation(card_id: str, annotation: str) -> KnowledgeCard:
        conn = _get_connection()
        conn.execute(
            "UPDATE knowledge_cards SET annotation = ? WHERE id = ?",
            (annotation, card_id),
        )
        conn.commit()
        conn.close()
        return CardRepository.get(card_id)

    @staticmethod
    def delete(card_id: str) -> bool:
        conn = _get_connection()
        conn.execute("DELETE FROM knowledge_cards WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()
        return True


class FootprintRepository:
    @staticmethod
    def create(footprint: Footprint) -> Footprint:
        conn = _get_connection()
        conn.execute(
            """
            INSERT INTO footprints (id, session_id, message_id, action_type, context, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                footprint.id,
                footprint.session_id,
                footprint.message_id,
                footprint.action_type,
                json.dumps(footprint.context) if footprint.context else None,
                footprint.created_at.isoformat() if footprint.created_at else datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        return footprint

    @staticmethod
    def list_by_session(session_id: str) -> List[Footprint]:
        conn = _get_connection()
        rows = conn.execute(
            "SELECT * FROM footprints WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
        conn.close()
        return [
            Footprint(
                id=row["id"],
                session_id=row["session_id"],
                message_id=row["message_id"],
                action_type=row["action_type"],
                context=json.loads(row["context"]) if row["context"] else None,
                created_at=_parse_datetime(row["created_at"]) or datetime.now(),
            )
            for row in rows
        ]