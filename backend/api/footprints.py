from fastapi import APIRouter, HTTPException
from datetime import datetime

from models.schemas import FootprintResponse, FootprintListResponse, FootprintCreateRequest
from services.footprint_service import record_footprint, get_footprints
from utils.exceptions import SessionNotFoundError

router = APIRouter()


@router.post("/", response_model=FootprintResponse)
async def create_footprint_api(request: FootprintCreateRequest):
    try:
        footprint = record_footprint(
            session_id=request.session_id,
            action_type=request.action_type,
            context=request.context,
            message_id=request.message_id,
        )
        return FootprintResponse(
            id=footprint.id,
            session_id=footprint.session_id,
            message_id=footprint.message_id,
            action_type=footprint.action_type,
            context=footprint.context,
            created_at=footprint.created_at,
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")


@router.get("/{session_id}", response_model=FootprintListResponse)
async def get_footprints_api(session_id: str):
    footprints = get_footprints(session_id)
    return FootprintListResponse(
        footprints=[
            FootprintResponse(
                id=fp.id,
                session_id=fp.session_id,
                message_id=fp.message_id,
                action_type=fp.action_type,
                context=fp.context,
                created_at=fp.created_at,
            )
            for fp in footprints
        ],
        total=len(footprints),
    )