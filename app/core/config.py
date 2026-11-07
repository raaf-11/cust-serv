from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    MODEL_NAME: str = "qwen/qwen3-32b"
    JUDGE_MODEL_NAME: str = ""
    TEMPERATURE: float = 0.0
    LLM_SEED: int = 42
    CONFIDENCE_THRESHOLD: float = 0.25
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
    RATE_LIMIT_ENABLED: bool = True
    CHAT_RATE_PER_MINUTE: int = 10
    CHAT_RATE_PER_HOUR: int = 100
    LOGIN_RATE_PER_MINUTE: int = 5
    REGISTER_RATE_PER_HOUR: int = 10
    REDIS_URL: str = ""
    TRUST_PROXY_HEADERS: bool = False
    LLM_REQUESTS_PER_MINUTE: int = 25
    LLM_TOKENS_PER_MINUTE: int = 5000
    LLM_MAX_RETRIES: int = 3
    LLM_MAX_RETRY_WAIT_S: float = 20.0

    class Config:
        env_file = ".env"


settings = Settings()
