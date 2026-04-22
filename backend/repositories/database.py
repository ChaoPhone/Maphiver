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
    raw_markdown TEXT,
    parsed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    name TEXT,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'archived')),
    is_pinned INTEGER DEFAULT 0,
    is_starred INTEGER DEFAULT 0,
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
    context TEXT,
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

CREATE TABLE IF NOT EXISTS document_links (
    id TEXT PRIMARY KEY,
    source_document_id TEXT NOT NULL,
    target_document_id TEXT NOT NULL,
    link_type TEXT DEFAULT 'reference',
    context TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_document_id) REFERENCES documents(id),
    FOREIGN KEY (target_document_id) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_links_source ON document_links(source_document_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON document_links(target_document_id);
"""


def init_db():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.executescript(CREATE_TABLES_SQL)
    
    try:
        conn.execute("ALTER TABLE sessions ADD COLUMN name TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE messages ADD COLUMN context TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE sessions ADD COLUMN is_pinned INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE sessions ADD COLUMN is_starred INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE documents ADD COLUMN raw_markdown TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

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
            raw_markdown=row["raw_markdown"],
            parsed_at=_parse_datetime(row["parsed_at"]),
            created_at=_parse_datetime(row["created_at"]) or datetime.now(),
        )

    @staticmethod
    def update_parsed(document_id: str, page_count: int, parsed_at: datetime, raw_markdown: Optional[str] = None) -> Document:
        conn = _get_connection()
        if raw_markdown:
            conn.execute(
                """
                UPDATE documents SET page_count = ?, parsed_at = ?, raw_markdown = ?
                WHERE id = ?
                """,
                (page_count, parsed_at.isoformat(), raw_markdown, document_id),
            )
        else:
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


class DocumentLinkRepository:
    @staticmethod
    def create(link: "DocumentLink") -> "DocumentLink":
        from models.schemas import DocumentLink
        conn = _get_connection()
        conn.execute(
            """
            INSERT INTO document_links (id, source_document_id, target_document_id, link_type, context, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                link.id,
                link.source_document_id,
                link.target_document_id,
                link.link_type,
                link.context,
                link.created_at.isoformat() if link.created_at else datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        return link

    @staticmethod
    def get(link_id: str) -> Optional["DocumentLink"]:
        from models.schemas import DocumentLink
        conn = _get_connection()
        row = conn.execute(
            "SELECT * FROM document_links WHERE id = ?", (link_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return DocumentLink(
            id=row["id"],
            source_document_id=row["source_document_id"],
            target_document_id=row["target_document_id"],
            link_type=row["link_type"],
            context=row["context"],
            created_at=_parse_datetime(row["created_at"]) or datetime.now(),
        )

    @staticmethod
    def list_by_source(source_document_id: str) -> List["DocumentLink"]:
        from models.schemas import DocumentLink
        conn = _get_connection()
        rows = conn.execute(
            "SELECT * FROM document_links WHERE source_document_id = ? ORDER BY created_at DESC",
            (source_document_id,),
        ).fetchall()
        conn.close()
        return [
            DocumentLink(
                id=row["id"],
                source_document_id=row["source_document_id"],
                target_document_id=row["target_document_id"],
                link_type=row["link_type"],
                context=row["context"],
                created_at=_parse_datetime(row["created_at"]) or datetime.now(),
            )
            for row in rows
        ]

    @staticmethod
    def list_by_target(target_document_id: str) -> List["DocumentLink"]:
        from models.schemas import DocumentLink
        conn = _get_connection()
        rows = conn.execute(
            "SELECT * FROM document_links WHERE target_document_id = ? ORDER BY created_at DESC",
            (target_document_id,),
        ).fetchall()
        conn.close()
        return [
            DocumentLink(
                id=row["id"],
                source_document_id=row["source_document_id"],
                target_document_id=row["target_document_id"],
                link_type=row["link_type"],
                context=row["context"],
                created_at=_parse_datetime(row["created_at"]) or datetime.now(),
            )
            for row in rows
        ]

    @staticmethod
    def delete(link_id: str) -> bool:
        conn = _get_connection()
        conn.execute("DELETE FROM document_links WHERE id = ?", (link_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def exists(source_document_id: str, target_document_id: str) -> bool:
        conn = _get_connection()
        row = conn.execute(
            "SELECT id FROM document_links WHERE source_document_id = ? AND target_document_id = ?",
            (source_document_id, target_document_id),
        ).fetchone()
        conn.close()
        return row is not None


class SessionRepository:
    @staticmethod
    def create(session: Session) -> Session:
        conn = _get_connection()
        now = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO sessions (id, document_id, name, status, is_pinned, is_starred, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.document_id,
                session.name,
                session.status.value,
                1 if session.is_pinned else 0,
                1 if session.is_starred else 0,
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
            name=row["name"],
            status=SessionStatus(row["status"]),
            is_pinned=bool(row["is_pinned"]),
            is_starred=bool(row["is_starred"]),
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
    def update(session_id: str, name: Optional[str] = None) -> Session:
        conn = _get_connection()
        if name is not None:
            conn.execute(
                """
                UPDATE sessions SET name = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, datetime.now().isoformat(), session_id),
            )
        conn.commit()
        conn.close()
        return SessionRepository.get(session_id)

    @staticmethod
    def update_pin_star(session_id: str, is_pinned: Optional[bool] = None, is_starred: Optional[bool] = None) -> Session:
        conn = _get_connection()
        updates = []
        params = []
        if is_pinned is not None:
            updates.append("is_pinned = ?")
            params.append(1 if is_pinned else 0)
        if is_starred is not None:
            updates.append("is_starred = ?")
            params.append(1 if is_starred else 0)
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(session_id)
            conn.execute(
                f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
        conn.close()
        return SessionRepository.get(session_id)

    @staticmethod
    def delete(session_id: str) -> bool:
        conn = _get_connection()
        conn.execute("DELETE FROM footprints WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM knowledge_cards WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def list_by_status(status: Optional[SessionStatus] = None) -> List[Session]:
        conn = _get_connection()
        if status:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE status = ? ORDER BY is_pinned DESC, updated_at DESC",
                (status.value,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY is_pinned DESC, updated_at DESC"
            ).fetchall()
        conn.close()
        return [
            Session(
                id=row["id"],
                document_id=row["document_id"],
                name=row["name"],
                status=SessionStatus(row["status"]),
                is_pinned=bool(row["is_pinned"]),
                is_starred=bool(row["is_starred"]),
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
            INSERT INTO messages (id, session_id, role, content, block_id, context, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.session_id,
                message.role.value,
                message.content,
                message.block_id,
                message.context,
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
                context=row["context"],
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