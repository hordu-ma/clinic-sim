"""应用配置模块。

使用 pydantic-settings 从环境变量和 .env 文件加载配置。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置。"""

    # 数据库配置
    DATABASE_URL: str

    # MinIO 配置
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "clinic-sim-dev"
    MINIO_SECURE: bool = False  # 开发环境使用 HTTP

    # LLM 配置
    LLM_BASE_URL: str
    LLM_MODEL: str
    LLM_TIMEOUT: int = 60  # 请求超时时间（秒）
    LLM_MAX_TOKENS: int = 500  # 最大生成 token 数
    LLM_TEMPERATURE: float = 0.7

    # JWT 配置
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # 应用环境
    ENV: str = "dev"  # dev / production
    DEBUG: bool = True

    # CORS 配置
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# 全局配置实例
settings = Settings()
