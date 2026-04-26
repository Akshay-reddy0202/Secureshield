from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "SecureShield V2"
    OPENROUTER_API_KEY: str 
    MONGODB_URI: str = "mongodb://localhost:27017"
    ENVIRONMENT: str = "development"
    
    # Security
    JWT_SECRET: str = "fallback_secret_do_not_use_in_prod"
    CORS_ORIGINS: str = "http://localhost:5173"
    
    # Models
    MAIN_MODEL: str = "meta-llama/llama-3.1-8b-instruct"
    GUARD_MODEL: str = "google/gemini-2.0-flash-001"
    
    # Retention
    RETENTION_DAYS: int = 30

    @property
    def CORS_ORIGINS_LIST(self):
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
