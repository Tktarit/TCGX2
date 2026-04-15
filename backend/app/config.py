from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./tcgx2.db"
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,webp,avif,heic,heif"

    @property
    def allowed_extensions_set(self) -> set[str]:
        return set(self.ALLOWED_EXTENSIONS.split(","))

    class Config:
        env_file = ".env"


settings = Settings()
