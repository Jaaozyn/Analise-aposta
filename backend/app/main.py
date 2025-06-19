from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import redis
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.core.cache import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando QuantumBet API...")
    await init_db()
    logger.info("Banco de dados inicializado")
    
    # Verificar conexão Redis
    try:
        await redis_client.ping()
        logger.info("Conexão Redis estabelecida")
    except Exception as e:
        logger.error(f"Erro ao conectar com Redis: {e}")
    
    yield
    
    # Shutdown
    logger.info("Encerrando QuantumBet API...")
    await redis_client.close()

app = FastAPI(
    title="QuantumBet API",
    description="API para análise probabilística de apostas esportivas com Machine Learning",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Rotas
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "QuantumBet API",
        "version": "1.0.0",
        "description": "Plataforma de análise probabilística para apostas esportivas"
    }

@app.get("/health")
async def health_check():
    try:
        # Verificar Redis
        await redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "version": "1.0.0"
    } 