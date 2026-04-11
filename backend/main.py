from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import documents, sessions, qa, health

app = FastAPI(
    title="Maphiver API",
    description="流式知识河 - FastAPI 后端",
    version="C1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(qa.router, prefix="/api/qa", tags=["qa"])