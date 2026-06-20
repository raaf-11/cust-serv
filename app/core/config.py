from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENROUTER_API_KEY: str

    MODEL_NAME: str = "qwen/qwen3-32b"

    TEMPERATURE: float = 0.3

    QDRANT_URL: str

    class Config:
        env_file = ".env"


settings = Settings()