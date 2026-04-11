import uuid
from datetime import datetime
from typing import Optional, List

from models.schemas import Footprint
from repositories.database import FootprintRepository


def record_footprint(
    session_id: str,
    action_type: str,
    context: Optional[dict] = None,
    message_id: Optional[str] = None,
) -> Footprint:
    footprint = Footprint(
        id=str(uuid.uuid4()),
        session_id=session_id,
        message_id=message_id,
        action_type=action_type,
        context=context,
        created_at=datetime.now(),
    )
    
    return FootprintRepository.create(footprint)


def get_footprints(session_id: str) -> List[Footprint]:
    return FootprintRepository.list_by_session(session_id)