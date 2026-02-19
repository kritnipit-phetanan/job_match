from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DB_HOST: str
    DB_PORT: str = "5432"
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # AI Config
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"
        # อนุญาตให้มีตัวแปรอื่นใน .env ได้โดยไม่ error
        extra = "ignore" 

settings = Settings()