from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_host: str
    mongo_port: int = 27017
    mongo_user: str
    mongo_password: str
    mongo_database: str

    sqlite_audit_db_path: str = "audit.db"

    virustotal_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://"
            f"{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}"
        )


settings = Settings()
