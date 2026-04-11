from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import uuid

from models.schemas import (
    DocumentResponse,
    DocumentUploadResponse,
    ContentBlock,
    ParseProgressChunk,
)

router = APIRouter()

MOCK_DOCUMENTS = {}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")
    
    doc_id = str(uuid.uuid4())
    MOCK_DOCUMENTS[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "file_path": f"/data/uploads/{doc_id}_{file.filename}",
        "page_count": None,
        "created_at": datetime.now(),
    }
    
    return DocumentUploadResponse(
        id=doc_id,
        filename=file.filename,
        status="uploaded",
        message="文档上传成功",
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    if document_id not in MOCK_DOCUMENTS:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return DocumentResponse(**MOCK_DOCUMENTS[document_id])


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    if document_id not in MOCK_DOCUMENTS:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    del MOCK_DOCUMENTS[document_id]
    return {"status": "deleted", "document_id": document_id}


@router.get("/", response_model=list[DocumentResponse])
async def list_documents():
    return [DocumentResponse(**doc) for doc in MOCK_DOCUMENTS.values()]


@router.post("/{document_id}/parse")
async def parse_document(document_id: str):
    if document_id not in MOCK_DOCUMENTS:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    async def generate():
        stages = [
            ("extracting", 10),
            ("extracted", 30),
            ("formatting", 50),
            ("streaming", 70),
        ]
        
        for stage, progress in stages:
            chunk = ParseProgressChunk(
                type="progress",
                progress=progress,
                stage=stage,
            )
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        
        mock_blocks = [
            ContentBlock(
                id=str(uuid.uuid4()),
                type="text",
                page=1,
                chapter_path=["第一章"],
                content="这是第一个段落的内容示例。",
            ),
            ContentBlock(
                id=str(uuid.uuid4()),
                type="text",
                page=1,
                chapter_path=["第一章", "1.1节"],
                content="这是第二个段落的内容示例。",
            ),
        ]
        
        for block in mock_blocks:
            chunk = ParseProgressChunk(
                type="block",
                block=block,
            )
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        
        done_chunk = ParseProgressChunk(
            type="done",
            total_pages=1,
            blocks=mock_blocks,
            raw_markdown="# 第一章\n\n这是第一个段落的内容示例。\n\n## 1.1节\n\n这是第二个段落的内容示例。",
        )
        yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")