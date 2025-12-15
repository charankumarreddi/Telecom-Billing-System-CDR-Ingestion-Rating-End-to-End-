from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
	app_name: str = Field(default="telecom-billing-cdr")
	environment: str = Field(default="dev")
	database_url: str = Field(default="sqlite:///./telecom.db", alias="DATABASE_URL")
	log_level: str = Field(default="INFO")

	class Config:
		env_file = ".env"
		env_file_encoding = "utf-8"


settings = Settings()

