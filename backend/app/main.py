from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import redis
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.core.cache import redis_client
from app.core.rate_limiter import limiter, add_rate_limit_headers, RateLimits
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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
    title="QuantumBet API v2.0",
    description="Plataforma Enterprise de Análise Probabilística para Apostas Esportivas com IA Avançada",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware de Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de hosts confiáveis
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

@app.middleware("http")
async def add_rate_limit_headers_middleware(request: Request, call_next):
    """Middleware para adicionar headers de rate limiting"""
    response = await call_next(request)
    add_rate_limit_headers(request, response)
    return response

# Rotas com rate limiting
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
@limiter.limit(RateLimits.PUBLIC_GENERAL)
async def root(request: Request):
    return {
        "message": "QuantumBet API",
        "version": "1.0.0",
        "description": "Plataforma de análise probabilística para apostas esportivas",
        "status": "operational"
    }

@app.get("/health")
@limiter.limit(RateLimits.PUBLIC_HEALTH)
async def health_check(request: Request):
    try:
        # Verificar Redis
        await redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "version": "1.0.0",
        "timestamp": logger.info("Health check realizado")
    } 