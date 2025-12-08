from pydantic import Field
from pydantic_settings import BaseSettings
from structlog.stdlib import get_logger
from functools import lru_cache

LOG = get_logger()


class Settings(BaseSettings):
    HOST: str = Field(..., alias="HOST")
    PORT: int = Field(..., alias="PORT")
    DB_CONNECTION_STRING: str = Field(...,
                                      alias="DB_CONNECTION_STRING")
    JWT_SECRET_KEY: str = Field(...,
                                alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(..., 
                               alias="JWT_ALGORITHM")
    JWT_EXP: int = Field(...,
                         alias="JWT_EXP")
    
    JWT_REFRESH_EXP: int = Field(...,
                                 alias="JWT_REFRESH_EXP")
    JWT_REFRESH_SECRET: str = Field(
        ...,
        alias="JWT_REFRESH_SECRET"
    )

    class Config:
        env_file = ".env"

        env_file_encoding = "utf-8"

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
