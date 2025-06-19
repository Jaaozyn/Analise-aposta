"""
Rate Limiting System - Proteção Avançada contra Spam/Bots
Implementação crítica para segurança da aplicação
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Optional
import redis.asyncio as redis
import json
import hashlib
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configurar Redis para rate limiting
redis_client = redis.from_url(settings.REDIS_URL)

class AdvancedRateLimiter:
    """Rate Limiter avançado com diferentes estratégias"""
    
    def __init__(self):
        self.redis = redis_client
        
    async def get_user_identifier(self, request: Request) -> str:
        """
        Identifica usuário para rate limiting
        Prioridade: user_id > session > IP
        """
        # 1. Usuário autenticado (melhor identificação)
        user = getattr(request.state, 'user', None)
        if user:
            return f"user:{user.id}"
        
        # 2. Session ID (usuários não autenticados mas com sessão)
        session_id = request.cookies.get("session_id")
        if session_id:
            return f"session:{session_id}"
        
        # 3. IP Address (fallback)
        ip = get_remote_address(request)
        return f"ip:{ip}"
    
    async def is_rate_limited(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int,
        endpoint: str = "general"
    ) -> tuple[bool, dict]:
        """
        Verifica se usuário excedeu rate limit
        
        Returns:
            (is_limited, info_dict)
        """
        key = f"rate_limit:{endpoint}:{identifier}"
        
        try:
            # Usar sliding window com Redis
            now = datetime.now().timestamp()
            window_start = now - window_seconds
            
            # Remover requests antigos
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Contar requests no window atual
            current_count = await self.redis.zcard(key)
            
            if current_count >= limit:
                # Calcular quando pode tentar novamente
                oldest_request = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    retry_after = int(oldest_request[0][1] + window_seconds - now)
                else:
                    retry_after = window_seconds
                
                return True, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": retry_after,
                    "current_count": current_count
                }
            
            # Adicionar request atual
            await self.redis.zadd(key, {str(now): now})
            await self.redis.expire(key, window_seconds)
            
            return False, {
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset": window_seconds,
                "current_count": current_count + 1
            }
            
        except Exception as e:
            logger.error(f"Erro no rate limiting: {e}")
            # Em caso de erro, permitir (fail-open)
            return False, {"limit": limit, "remaining": limit, "reset": window_seconds}
    
    async def check_suspicious_activity(self, identifier: str, endpoint: str) -> bool:
        """
        Detecta atividade suspeita que pode indicar bot
        """
        # Verificar múltiplos indicadores
        suspicious_indicators = []
        
        # 1. Frequência muito alta
        key_freq = f"freq_check:{identifier}"
        requests_last_minute = await self.redis.zcount(
            key_freq, 
            datetime.now().timestamp() - 60, 
            datetime.now().timestamp()
        )
        
        if requests_last_minute > 50:  # Mais de 50 req/min = suspeito
            suspicious_indicators.append("high_frequency")
        
        # 2. Padrão muito regular (bot-like)
        if await self._detect_regular_pattern(identifier):
            suspicious_indicators.append("regular_pattern")
        
        # 3. Múltiplos endpoints simultaneamente
        if await self._detect_endpoint_scanning(identifier):
            suspicious_indicators.append("endpoint_scanning")
        
        # Se 2 ou mais indicadores = atividade suspeita
        is_suspicious = len(suspicious_indicators) >= 2
        
        if is_suspicious:
            logger.warning(f"Atividade suspeita detectada: {identifier} - {suspicious_indicators}")
        
        return is_suspicious
    
    async def _detect_regular_pattern(self, identifier: str) -> bool:
        """Detecta padrões muito regulares (bot-like)"""
        key = f"pattern:{identifier}"
        
        # Buscar últimos 10 requests
        recent_requests = await self.redis.zrange(key, -10, -1, withscores=True)
        
        if len(recent_requests) < 5:
            return False
        
        # Calcular intervalos entre requests
        intervals = []
        for i in range(1, len(recent_requests)):
            interval = recent_requests[i][1] - recent_requests[i-1][1]
            intervals.append(interval)
        
        # Se todos os intervalos são muito similares = bot
        if len(intervals) >= 4:
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            
            # Variância muito baixa = padrão regular = bot
            return variance < 1.0
        
        return False
    
    async def _detect_endpoint_scanning(self, identifier: str) -> bool:
        """Detecta scanning de múltiplos endpoints"""
        key = f"endpoints:{identifier}"
        
        # Contar endpoints únicos acessados na última hora
        now = datetime.now().timestamp()
        hour_ago = now - 3600
        
        endpoint_count = await self.redis.zcount(key, hour_ago, now)
        
        # Mais de 10 endpoints diferentes em 1h = scanning
        return endpoint_count > 10

# Instância global
advanced_limiter = AdvancedRateLimiter()

# Limiter básico do slowapi
limiter = Limiter(key_func=get_remote_address)

# Rate limits específicos por tipo de endpoint
class RateLimits:
    """Configurações de rate limiting por endpoint"""
    
    # APIs críticas (geração de picks)
    PICKS_GENERATION = "5/hour"      # Máximo 5 gerações por hora
    PICKS_LIST = "100/hour"          # Listar picks
    
    # APIs de usuário
    USER_AUTH = "10/minute"          # Login/register
    USER_DATA = "50/hour"            # Dados do usuário
    
    # APIs de pagamento
    PAYMENT_CREATE = "3/hour"        # Criar pagamento
    PAYMENT_STATUS = "20/hour"       # Verificar status
    
    # APIs públicas
    PUBLIC_GENERAL = "200/hour"      # Endpoints públicos
    PUBLIC_HEALTH = "1000/hour"      # Health check
    
    # Emergency brake
    GLOBAL_LIMIT = "500/hour"        # Limite global por usuário

async def enhanced_rate_limit_check(
    request: Request,
    endpoint_type: str = "general",
    limit: str = "100/hour"
) -> None:
    """
    Rate limiting avançado com detecção de anomalias
    """
    # Parse do limite
    limit_number, period = limit.split("/")
    limit_number = int(limit_number)
    
    window_seconds = {
        "minute": 60,
        "hour": 3600,
        "day": 86400
    }.get(period, 3600)
    
    # Identificar usuário
    identifier = await advanced_limiter.get_user_identifier(request)
    
    # Verificar rate limit
    is_limited, info = await advanced_limiter.is_rate_limited(
        identifier, limit_number, window_seconds, endpoint_type
    )
    
    # Adicionar headers informativos
    request.state.rate_limit_info = info
    
    if is_limited:
        # Verificar se é atividade suspeita
        is_suspicious = await advanced_limiter.check_suspicious_activity(
            identifier, endpoint_type
        )
        
        if is_suspicious:
            # Log detalhado para investigação
            logger.error(f"Rate limit + atividade suspeita: {identifier} em {endpoint_type}")
            
            # Ban temporário mais severo para suspeitos
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Atividade suspeita detectada. Conta temporariamente restrita.",
                    "retry_after": info["reset"] * 2,  # Dobrar tempo de espera
                    "contact": "suporte@quantumbet.com"
                }
            )
        
        # Rate limit normal
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Limite de {limit} excedido. Tente novamente em {info['reset']} segundos.",
                "limit": info["limit"],
                "remaining": info["remaining"],
                "retry_after": info["reset"]
            }
        )

def add_rate_limit_headers(request: Request, response):
    """Adiciona headers informativos sobre rate limiting"""
    if hasattr(request.state, 'rate_limit_info'):
        info = request.state.rate_limit_info
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

# Decorators para facilitar uso
def rate_limit(limit: str, endpoint_type: str = "general"):
    """Decorator para aplicar rate limiting em endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or args[0]
            await enhanced_rate_limit_check(request, endpoint_type, limit)
            return await func(*args, **kwargs)
        return wrapper
    return decorator 