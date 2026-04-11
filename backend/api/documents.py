from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import aiofiles

from models.schemas import (
    DocumentResponse,
    DocumentUploadResponse,
    ContentBlock,
    ParseProgressChunk,
)
from services.document_service import (
    upload_document,
    get_document,
    delete_document,
    list_documents,
    parse_document_stream,
)
from utils.exceptions import DocumentNotFoundError, DocumentUploadError, ParseError

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document_api(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")
    
    try:
        file_bytes = await file.read()
        document = upload_document(file_bytes, file.filename)
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            status="uploaded",
            message="文档上传成功",
        )
    except DocumentUploadError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_api(document_id: str):
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_path=document.file_path,
        page_count=document.page_count,
        created_at=document.created_at,
    )


@router.delete("/{document_id}")
async def delete_document_api(document_id: str):
    try:
        delete_document(document_id)
        return {"status": "deleted", "document_id": document_id}
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="文档不存在")


@router.get("/", response_model=list[DocumentResponse])
async def list_documents_api():
    documents = list_documents()
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_path=doc.file_path,
            page_count=doc.page_count,
            created_at=doc.created_at,
        )
        for doc in documents
    ]


@router.post("/{document_id}/parse")
async def parse_document_api(document_id: str):
    async def generate():
        try:
            for chunk in parse_document_stream(document_id):
                if chunk.type.value == "text":
                    if chunk.metadata:
                        progress_chunk = ParseProgressChunk(
                            type="progress",
                            stage=chunk.metadata.get("stage"),
                            progress=_get_progress(chunk.metadata.get("stage")),
                        )
                        yield f"data: {json.dumps(progress_chunk.model_dump())}\n\n"
                    
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'text', 'content': chunk.content})}\n\n"
                
                elif chunk.type.value == "done":
                    metadata = chunk.metadata or {}
                    blocks_data = metadata.get("blocks", [])
                    blocks = [ContentBlock(**b) for b in blocks_data] if blocks_data else []
                    
                    done_chunk = ParseProgressChunk(
                        type="done",
                        total_pages=metadata.get("total_pages"),
                        blocks=blocks,
                        raw_markdown=metadata.get("raw_markdown"),
                    )
                    yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"
                
                elif chunk.type.value == "error":
                    error_chunk = ParseProgressChunk(
                        type="error",
                        error=chunk.error_message,
                    )
                    yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"
                    
        except Exception as e:
            error_chunk = ParseProgressChunk(type="error", error=str(e))
            yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


def _get_progress(stage: str) -> int:
    progress_map = {
        "extracting": 10,
        "extracted": 30,
        "formatting": 50,
        "streaming": 70,
    }
    return progress_map.get(stage, 0)