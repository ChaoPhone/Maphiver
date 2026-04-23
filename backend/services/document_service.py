import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Generator

from config import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB
from models.schemas import Document, ParseResult, ContentBlock, StreamChunk, ChunkType
from repositories.database import DocumentRepository
from utils.exceptions import DocumentUploadError, DocumentNotFoundError, ParseError
from utils.document_parser import extract_text_from_document
from services.ai_service import format_text_with_ai, format_text_stream


ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx']


def upload_document(file_bytes: bytes, filename: str) -> Document:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentUploadError(f"仅支持 PDF、DOC、DOCX 文件")
    
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_SIZE_MB:
        raise DocumentUploadError(f"文件大小超过限制 ({MAX_UPLOAD_SIZE_MB}MB)")
    
    doc_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{doc_id}_{filename}"
    
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        raise DocumentUploadError(f"保存文件失败: {str(e)}")
    
    document = Document(
        id=doc_id,
        filename=filename,
        file_path=str(file_path),
        page_count=None,
        parsed_at=None,
        created_at=datetime.now(),
    )
    
    return DocumentRepository.create(document)


def parse_document(document_id: str, use_ai_format: bool = True, update_db: bool = True) -> ParseResult:
    document = get_document(document_id)
    if not document:
        raise DocumentNotFoundError(f"文档 {document_id} 不存在")
    
    try:
        raw_text, total_pages, blocks = extract_text_from_document(document.file_path)
        
        if use_ai_format and raw_text.strip():
            formatted_markdown = format_text_with_ai(raw_text)
        else:
            formatted_markdown = raw_text
        
        if update_db:
            DocumentRepository.update_parsed(
                document_id,
                page_count=total_pages,
                parsed_at=datetime.now(),
                raw_markdown=formatted_markdown,
            )

        return ParseResult(
            document_id=document_id,
            blocks=blocks,
            total_pages=total_pages,
            raw_markdown=formatted_markdown,
        )
        
    except Exception as e:
        raise ParseError(f"解析文档失败: {str(e)}")


def parse_document_stream(document_id: str, use_ai_format: bool = True) -> Generator[StreamChunk, None, None]:
    document = get_document(document_id)
    if not document:
        yield StreamChunk(type=ChunkType.ERROR, error_message=f"文档 {document_id} 不存在")
        return
    
    try:
        yield StreamChunk(type=ChunkType.TEXT, content="", metadata={"stage": "extracting"})
        
        raw_text, total_pages, blocks = extract_text_from_document(document.file_path)
        
        yield StreamChunk(
            type=ChunkType.TEXT,
            content="",
            metadata={"stage": "extracted", "total_pages": total_pages, "block_count": len(blocks)}
        )
        
        if use_ai_format and raw_text.strip():
            yield StreamChunk(type=ChunkType.TEXT, content="", metadata={"stage": "formatting"})
            
            formatted_chunks: List[str] = []
            for chunk in format_text_stream(raw_text):
                if chunk.type == ChunkType.TEXT:
                    formatted_chunks.append(chunk.content or "")
                    yield StreamChunk(
                        type=ChunkType.TEXT,
                        content=chunk.content,
                        metadata={"stage": "streaming"}
                    )
                elif chunk.type == ChunkType.ERROR:
                    yield chunk
                    return
        else:
            formatted_chunks = [raw_text]
        
        DocumentRepository.update_parsed(
            document_id,
            page_count=total_pages,
            parsed_at=datetime.now(),
            raw_markdown="".join(formatted_chunks),
        )

        yield StreamChunk(
            type=ChunkType.DONE,
            metadata={
                "document_id": document_id,
                "total_pages": total_pages,
                "blocks": [b.model_dump() for b in blocks],
                "raw_markdown": "".join(formatted_chunks),
            }
        )
        
    except Exception as e:
        yield StreamChunk(type=ChunkType.ERROR, error_message=f"解析文档失败: {str(e)}")


def get_document(document_id: str) -> Optional[Document]:
    return DocumentRepository.get(document_id)


def delete_document(document_id: str) -> bool:
    document = get_document(document_id)
    if not document:
        raise DocumentNotFoundError(f"文档 {document_id} 不存在")
    
    file_path = Path(document.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except:
            pass
    
    return DocumentRepository.delete(document_id)


def list_documents() -> List[Document]:
    return DocumentRepository.list_all()