from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENROUTER_API_KEY: str

    MODEL_NAME: str = "qwen/qwen3-32b"

    # Eval only: model for the LLM judge. Empty = same as MODEL_NAME.
    JUDGE_MODEL_NAME: str = ""

    # 0 = always pick the most likely wording, so the same question gives
    # the same answer. (If your .env sets TEMPERATURE, change it there too.)
    TEMPERATURE: float = 0.0

    # Fixed seed for extra repeatability on providers that support it.
    LLM_SEED: int = 42

    # Below this retrieval confidence the bot asks the user to rephrase;
    # a second miss in a row escalates. See confidence_service.py.
    CONFIDENCE_THRESHOLD: float = 0.25

    # Unresolved bot turns in a row before creating a ticket.
    MAX_UNRESOLVED_TURNS: int = 2

    QDRANT_URL: str

    QDRANT_COLLECTION_NAME: str = "knowledge_base"
    
    EMBEDDING_DIMENSION: int = 384

    DATABASE_URL: str

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ELASTICSEARCH_URL: str

    ELASTICSEARCH_INDEX: str = "knowledge_base"

    DEBUG_RETRIEVAL: bool = True

    MAX_INPUT_LENGTH: int = 2000

    # ---- Inbound API rate limits (see app/core/rate_limiter.py) ----
    RATE_LIMIT_ENABLED: bool = True
    # /chat, per logged-in user: short burst limit + hourly budget.
    CHAT_RATE_PER_MINUTE: int = 10
    CHAT_RATE_PER_HOUR: int = 100
    # /auth, per client IP (brute-force protection).
    LOGIN_RATE_PER_MINUTE: int = 5
    REGISTER_RATE_PER_HOUR: int = 10
    # Set when running several workers so limits are shared, e.g.
    # redis://localhost:6379/0. Empty = in-memory (single worker).
    REDIS_URL: str = ""
    # Only enable behind a reverse proxy you control.
    TRUST_PROXY_HEADERS: bool = False

    # ---- Outbound LLM (Groq) limits (see app/services/llm_rate_limiter.py) ----
    # Set these a little BELOW your Groq plan's limits for MODEL_NAME
    # (console.groq.com/settings/limits) so we queue instead of getting 429s.
    LLM_REQUESTS_PER_MINUTE: int = 25
    LLM_TOKENS_PER_MINUTE: int = 5000
    LLM_MAX_RETRIES: int = 3
    # Never make a chat user wait longer than this for a retry.
    LLM_MAX_RETRY_WAIT_S: float = 20.0

    class Config:
        env_file = ".env"

settings = Settings()


