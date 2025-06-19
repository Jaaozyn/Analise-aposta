from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # Projeto
    PROJECT_NAME: str = "QuantumBet"
    VERSION: str = "1.0.0"
    
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 dias
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Banco de Dados
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://quantumbet:password@localhost/quantumbet_db"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # APIs Externas
    API_FOOTBALL_KEY: Optional[str] = os.getenv("API_FOOTBALL_KEY")
    PANDASCORE_KEY: Optional[str] = os.getenv("PANDASCORE_KEY")
    ODDS_API_KEY: Optional[str] = os.getenv("ODDS_API_KEY")
    
    # Pagamentos
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    MERCADOPAGO_ACCESS_TOKEN: Optional[str] = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    MERCADOPAGO_PUBLIC_KEY: Optional[str] = os.getenv("MERCADOPAGO_PUBLIC_KEY")
    
    PAYPAL_CLIENT_ID: Optional[str] = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET: Optional[str] = os.getenv("PAYPAL_CLIENT_SECRET")
    PAYPAL_MODE: str = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox ou live
    
    # Machine Learning
    ML_MODEL_PATH: str = "models/"
    ML_DATA_PATH: str = "data/"
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379")
    
    # Logs
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 