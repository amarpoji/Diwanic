from typing import ClassVar
from pydantic import Field, SecretStr, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class QdrantSettings(BaseModel):
    url: str = Field(default="", description="Qdrant Cloud URL")
    api_key: SecretStr = Field(default=SecretStr(""), description="Qdrant API key")
    host: str = Field(default="localhost", description="Qdrant host")
    port: int = Field(default=6333, description="Qdrant port")
    collection_poems: str = Field(default="poems", description="Poem collection name")
    collection_verses: str = Field(default="verses", description="Verse collection name")

class DatabaseSettings(BaseModel):
    url: SecretStr = Field(default=SecretStr(""), description="PostgreSQL connection string")

class EmbeddingSettings(BaseModel):
    model: str = Field(default="intfloat/multilingual-e5-small", description="Embedding model name")
    dim: int = Field(default=384, description="Embedding vector dimension")

class RouterSettings(BaseModel):
    api_key: SecretStr = Field(default=SecretStr(""), description="Router API key")
    base_url: str = Field(default="http://localhost:20128/v1", description="Router base URL")
    model: str = Field(default="my-combo", description="Router model name")

class ScraperSettings(BaseModel):
    base_url: str = Field(default="https://www.aldiwan.net", description="Scraper base URL")
    delay: float = Field(default=1.5, description="Scraper delay in seconds")

class Settings(BaseSettings):
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    router: RouterSettings = Field(default_factory=RouterSettings)
    scraper: ScraperSettings = Field(default_factory=ScraperSettings)
    
    logfire_token: str = Field(default="", description="Logfire API token")

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        frozen=True,
    )

settings = Settings()
