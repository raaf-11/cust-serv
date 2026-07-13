from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.ticket import router as ticket_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.qdrant import router as qdrant_router
from app.api.embedding import router as embedding_router
from app.api.ingestion import router as ingestion_router
from app.api.retrieval import router as retrieval_router
from app.api.chat_session import router as chat_session_router
from app.api.auth import router as auth_router

app = FastAPI(
    title="Customer Support Copilot"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(health_router)
app.include_router(qdrant_router)
app.include_router(embedding_router)
app.include_router(ingestion_router)
app.include_router(retrieval_router)
app.include_router(chat_session_router)
app.include_router(auth_router)
app.include_router(ticket_router)