from fastapi import APIRouter, HTTPException
from datetime import datetime

from models.schemas import (
    CardResponse,
    CardListResponse,
    CardCreateRequest,
    CardUpdateRequest,
)
from services.card_service import (
    create_card,
    get_card,
    get_cards,
    update_card,
    delete_card,
)
from utils.exceptions import CardNotFoundError, SessionNotFoundError

router = APIRouter()


@router.post("/", response_model=CardResponse)
async def create_card_api(request: CardCreateRequest):
    try:
        card = create_card(
            session_id=request.session_id,
            source_text=request.source_text,
            annotation=request.annotation,
            block_id=request.block_id,
        )
        return CardResponse(
            id=card.id,
            session_id=card.session_id,
            source_text=card.source_text,
            annotation=card.annotation,
            block_id=card.block_id,
            created_at=card.created_at,
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")


@router.get("/{card_id}", response_model=CardResponse)
async def get_card_api(card_id: str):
    card = get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="知识卡片不存在")
    return CardResponse(
        id=card.id,
        session_id=card.session_id,
        source_text=card.source_text,
        annotation=card.annotation,
        block_id=card.block_id,
        created_at=card.created_at,
    )


@router.get("/", response_model=CardListResponse)
async def list_cards_api(session_id: str = None):
    cards = get_cards(session_id)
    return CardListResponse(
        cards=[
            CardResponse(
                id=c.id,
                session_id=c.session_id,
                source_text=c.source_text,
                annotation=c.annotation,
                block_id=c.block_id,
                created_at=c.created_at,
            )
            for c in cards
        ],
        total=len(cards),
    )


@router.put("/{card_id}", response_model=CardResponse)
async def update_card_api(card_id: str, request: CardUpdateRequest):
    try:
        card = update_card(card_id, request.annotation)
        return CardResponse(
            id=card.id,
            session_id=card.session_id,
            source_text=card.source_text,
            annotation=card.annotation,
            block_id=card.block_id,
            created_at=card.created_at,
        )
    except CardNotFoundError:
        raise HTTPException(status_code=404, detail="知识卡片不存在")


@router.delete("/{card_id}")
async def delete_card_api(card_id: str):
    try:
        delete_card(card_id)
        return {"status": "deleted", "card_id": card_id}
    except CardNotFoundError:
        raise HTTPException(status_code=404, detail="知识卡片不存在")