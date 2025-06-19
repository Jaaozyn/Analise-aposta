from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # Projeto
    PROJECT_NAME: str = "QuantumBet"
    VERSION: str = "2.0.0"  # Atualizado para v2.0
    
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Token de acesso expira em 15 minutos
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # Refresh token expira em 7 dias
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Banco de Dados
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://quantumbet:password123@localhost/quantumbet_db"
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
    
    # ===== NOVAS CONFIGURAÇÕES v2.0 =====
    
    # Segurança e Autenticação
    ENABLE_2FA: bool = True
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate Limiting
    RATE_LIMITING_ENABLED: bool = True
    RATE_LIMIT_REDIS_URL: str = os.getenv("RATE_LIMIT_REDIS_URL", REDIS_URL)
    
    # Backup e Recovery
    BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_COMPRESSION: bool = True
    BACKUP_ENCRYPTION: bool = True
    BACKUP_SCHEDULE_CRON: str = "0 2 * * *"  # Todo dia às 2h
    
    # Armazenamento em Nuvem para Backups
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BACKUP_BUCKET: Optional[str] = os.getenv("AWS_S3_BACKUP_BUCKET")
    
    # Monitoramento e Observabilidade
    MONITORING_ENABLED: bool = True
    PROMETHEUS_METRICS_ENABLED: bool = True
    GRAFANA_DASHBOARDS_ENABLED: bool = True
    
    # Cache Inteligente
    SMART_CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 3600  # 1 hora
    CACHE_MAX_MEMORY_KEYS: int = 1000
    
    # Auditoria
    AUDIT_TRAIL_ENABLED: bool = True
    AUDIT_RETENTION_DAYS: int = 365  # 1 ano
    AUDIT_LOG_SENSITIVE_DATA: bool = False
    
    # WebSocket
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_PING_INTERVAL: int = 30
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    
    # Preços Dinâmicos
    DYNAMIC_PRICING_ENABLED: bool = True
    PRICING_BASE_PREMIUM_TIER: float = 99.0
    PRICING_MAX_DISCOUNT: float = 0.30  # 30%
    PRICING_MAX_PREMIUM: float = 0.50   # 50%
    
    # Machine Learning Avançado
    ENSEMBLE_MODELS_ENABLED: bool = True
    ML_CACHE_PREDICTIONS: bool = True
    ML_BACKTESTING_ENABLED: bool = True
    
    # Notificações
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: Optional[str] = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_TLS: bool = True
    
    # Ambiente
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "False").lower() == "true"
    
    # Segurança Avançada
    SECURITY_HEADERS_ENABLED: bool = True
    CORS_ALLOW_CREDENTIALS: bool = True
    TRUSTED_HOSTS: List[str] = ["localhost", "127.0.0.1", "quantumbet.com"]
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30
    
    # Feature Flags (para A/B testing futuro)
    FEATURE_ADVANCED_ANALYTICS: bool = True
    FEATURE_CHURN_PREDICTION: bool = True
    FEATURE_RECOMMENDATION_ENGINE: bool = True
    
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento"""
        return self.ENVIRONMENT.lower() == "development"
    
    def is_testing(self) -> bool:
        """Verifica se está em modo de teste"""
        return self.TESTING
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 