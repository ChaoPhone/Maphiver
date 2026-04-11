from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import documents, sessions, qa, health, footprints, cards
from repositories.database import init_db

init_db()

app = FastAPI(
    title="Maphiver API",
    description="流式知识河 - FastAPI 后端",
    version="C2",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(qa.router, prefix="/api/qa", tags=["qa"])
app.include_router(footprints.router, prefix="/api/footprints", tags=["footprints"])
app.include_router(cards.router, prefix="/api/cards", tags=["cards"])