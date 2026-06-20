from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.qdrant import (
    router as qdrant_router
)

from app.api.embedding import (
    router as embedding_router
)

app = FastAPI(
    title="Customer Support Copilot"
)

app.include_router(chat_router)
app.include_router(health_router)

app.include_router(qdrant_router)

app.include_router(
    embedding_router
)
