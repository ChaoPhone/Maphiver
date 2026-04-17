from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from config import DATA_DIR

router = APIRouter()

IMAGES_DIR = DATA_DIR / "images"


import mimetypes

@router.get("/{image_filename}")
async def get_image(image_filename: str):
    image_path = IMAGES_DIR / image_filename
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 自动识别正确的MIME类型
    mime_type, _ = mimetypes.guess_type(image_filename)
    if not mime_type:
        mime_type = "image/png"  #  fallback
    
    return FileResponse(
        image_path,
        media_type=mime_type,
        content_disposition_type="inline"
    )