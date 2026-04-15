from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime

from models.schemas import (
    DocumentLink,
    DocumentLinkResponse,
    DocumentLinkListResponse,
    DocumentLinkCreateRequest,
    DocumentResponse,
)
from repositories.database import DocumentLinkRepository, DocumentRepository

router = APIRouter(prefix="/document-links", tags=["document-links"])


def _build_link_response(link: DocumentLink) -> DocumentLinkResponse:
    target_doc = DocumentRepository.get(link.target_document_id)
    target_doc_response = None
    if target_doc:
        target_doc_response = DocumentResponse(
            id=target_doc.id,
            filename=target_doc.filename,
            file_path=target_doc.file_path,
            page_count=target_doc.page_count,
            created_at=target_doc.created_at,
        )
    return DocumentLinkResponse(
        id=link.id,
        source_document_id=link.source_document_id,
        target_document_id=link.target_document_id,
        link_type=link.link_type,
        context=link.context,
        target_document=target_doc_response,
        created_at=link.created_at,
    )


@router.post("/", response_model=DocumentLinkResponse)
def create_link(request: DocumentLinkCreateRequest):
    source_doc = DocumentRepository.get(request.source_document_id)
    if not source_doc:
        raise HTTPException(status_code=404, detail="源文档不存在")
    
    target_doc = DocumentRepository.get(request.target_document_id)
    if not target_doc:
        raise HTTPException(status_code=404, detail="目标文档不存在")
    
    if request.source_document_id == request.target_document_id:
        raise HTTPException(status_code=400, detail="不能关联同一文档")
    
    if DocumentLinkRepository.exists(request.source_document_id, request.target_document_id):
        raise HTTPException(status_code=400, detail="文档关联已存在")
    
    link = DocumentLink(
        id=str(uuid.uuid4()),
        source_document_id=request.source_document_id,
        target_document_id=request.target_document_id,
        link_type=request.link_type,
        context=request.context,
        created_at=datetime.now(),
    )
    created_link = DocumentLinkRepository.create(link)
    return _build_link_response(created_link)


@router.get("/source/{document_id}", response_model=DocumentLinkListResponse)
def get_links_by_source(document_id: str):
    doc = DocumentRepository.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    links = DocumentLinkRepository.list_by_source(document_id)
    link_responses = [_build_link_response(link) for link in links]
    return DocumentLinkListResponse(links=link_responses, total=len(link_responses))


@router.get("/target/{document_id}", response_model=DocumentLinkListResponse)
def get_links_by_target(document_id: str):
    doc = DocumentRepository.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    links = DocumentLinkRepository.list_by_target(document_id)
    link_responses = [_build_link_response(link) for link in links]
    return DocumentLinkListResponse(links=link_responses, total=len(link_responses))


@router.delete("/{link_id}")
def delete_link(link_id: str):
    link = DocumentLinkRepository.get(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="关联不存在")
    
    DocumentLinkRepository.delete(link_id)
    return {"message": "关联已删除"}