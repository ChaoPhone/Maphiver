import uuid
from datetime import datetime
from typing import Optional, List

from models.schemas import KnowledgeCard
from repositories.database import CardRepository
from utils.exceptions import CardNotFoundError


def create_card(
    session_id: str,
    source_text: str,
    annotation: Optional[str] = None,
    block_id: Optional[str] = None,
) -> KnowledgeCard:
    card = KnowledgeCard(
        id=str(uuid.uuid4()),
        session_id=session_id,
        source_text=source_text,
        annotation=annotation,
        block_id=block_id,
        created_at=datetime.now(),
    )
    
    return CardRepository.create(card)


def get_card(card_id: str) -> Optional[KnowledgeCard]:
    return CardRepository.get(card_id)


def get_cards(session_id: Optional[str] = None) -> List[KnowledgeCard]:
    return CardRepository.list_by_session(session_id)


def update_card(card_id: str, annotation: str) -> KnowledgeCard:
    card = get_card(card_id)
    if not card:
        raise CardNotFoundError(f"知识卡片 {card_id} 不存在")
    return CardRepository.update_annotation(card_id, annotation)


def delete_card(card_id: str) -> bool:
    card = get_card(card_id)
    if not card:
        raise CardNotFoundError(f"知识卡片 {card_id} 不存在")
    return CardRepository.delete(card_id)