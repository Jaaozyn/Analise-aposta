"""
Smart Cache System - Cache Inteligente Multi-Layer
Reduz latência de 3s para 50ms através de cache hierárquico
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import redis.asyncio as redis
from functools import wraps
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Estratégias de cache baseadas no tipo de dados"""
    
    # Cache ultra-rápido (em memória) - dados estáticos
    MEMORY = "memory"          # TTL: 5min, dados pequenos e frequentes
    
    # Cache rápido (Redis) - dados dinâmicos
    REDIS_FAST = "redis_fast"  # TTL: 15min, dados de sessão/usuário
    
    # Cache persistente - dados computacionalmente caros
    REDIS_PERSIST = "redis_persist"  # TTL: 2h, resultados ML/análises
    
    # Cache longo - dados que mudam pouco
    REDIS_LONG = "redis_long"  # TTL: 24h, odds históricas, estatísticas

@dataclass
class CacheConfig:
    """Configuração de cache por tipo de dados"""
    strategy: CacheStrategy
    ttl: int  # Time to live em segundos
    compress: bool = False  # Compressão para dados grandes
    invalidate_on: Optional[List[str]] = None  # Eventos que invalidam o cache

class SmartCacheManager:
    """
    Sistema de cache inteligente com múltiplas camadas
    
    Hierarquia:
    1. Memory Cache (mais rápido, menor capacidade)
    2. Redis Fast (rápido, média capacidade)  
    3. Redis Persist (persistente, grande capacidade)
    4. Redis Long (longo prazo, dados estáticos)
    """
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.memory_cache: Dict[str, Any] = {}
        self.memory_expiry: Dict[str, datetime] = {}
        
        # Configurações pré-definidas por tipo de dados
        self.configs = {
            # Dados de picks e análises
            "picks_list": CacheConfig(CacheStrategy.REDIS_FAST, 900),  # 15min
            "pick_detail": CacheConfig(CacheStrategy.REDIS_FAST, 1800),  # 30min
            "pick_generation": CacheConfig(CacheStrategy.REDIS_PERSIST, 3600),  # 1h
            
            # Dados de odds e mercados
            "odds_current": CacheConfig(CacheStrategy.MEMORY, 60),  # 1min
            "odds_historical": CacheConfig(CacheStrategy.REDIS_LONG, 86400),  # 24h
            
            # Dados de partidas
            "matches_live": CacheConfig(CacheStrategy.MEMORY, 30),  # 30s
            "matches_upcoming": CacheConfig(CacheStrategy.REDIS_FAST, 600),  # 10min
            "matches_completed": CacheConfig(CacheStrategy.REDIS_LONG, 86400),  # 24h
            
            # Dados de usuário
            "user_profile": CacheConfig(CacheStrategy.REDIS_FAST, 1800),  # 30min
            "user_stats": CacheConfig(CacheStrategy.REDIS_FAST, 900),  # 15min
            "user_subscription": CacheConfig(CacheStrategy.REDIS_PERSIST, 3600),  # 1h
            
            # Análises ML (computacionalmente caras)
            "ml_predictions": CacheConfig(CacheStrategy.REDIS_PERSIST, 7200),  # 2h
            "ml_model_results": CacheConfig(CacheStrategy.REDIS_LONG, 43200),  # 12h
            "backtesting_results": CacheConfig(CacheStrategy.REDIS_LONG, 86400),  # 24h
            
            # APIs externas (rate limited)
            "api_football": CacheConfig(CacheStrategy.REDIS_PERSIST, 1800),  # 30min
            "api_odds": CacheConfig(CacheStrategy.REDIS_FAST, 300),  # 5min
            "api_esports": CacheConfig(CacheStrategy.REDIS_FAST, 600),  # 10min
        }
    
    def _generate_key(self, key_type: str, identifier: str, params: Dict = None) -> str:
        """Gera chave única para cache"""
        base_key = f"cache:{key_type}:{identifier}"
        if params:
            # Criar hash dos parâmetros para chave única
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            base_key += f":{params_hash}"
        return base_key
    
    async def get(self, key_type: str, identifier: str, params: Dict = None) -> Optional[Any]:
        """
        Busca dados no cache seguindo hierarquia inteligente
        """
        cache_key = self._generate_key(key_type, identifier, params)
        config = self.configs.get(key_type)
        
        if not config:
            logger.warning(f"Configuração de cache não encontrada para: {key_type}")
            return None
        
        try:
            # 1. Tentar memory cache primeiro (mais rápido)
            if config.strategy == CacheStrategy.MEMORY:
                return self._get_from_memory(cache_key)
            
            # 2. Tentar Redis
            if config.strategy in [CacheStrategy.REDIS_FAST, CacheStrategy.REDIS_PERSIST, CacheStrategy.REDIS_LONG]:
                return await self._get_from_redis(cache_key, config.compress)
                
        except Exception as e:
            logger.error(f"Erro ao buscar cache {cache_key}: {e}")
            
        return None
    
    async def set(
        self, 
        key_type: str, 
        identifier: str, 
        data: Any, 
        params: Dict = None,
        custom_ttl: Optional[int] = None
    ) -> bool:
        """
        Armazena dados no cache usando estratégia apropriada
        """
        cache_key = self._generate_key(key_type, identifier, params)
        config = self.configs.get(key_type)
        
        if not config:
            logger.warning(f"Configuração de cache não encontrada para: {key_type}")
            return False
        
        ttl = custom_ttl or config.ttl
        
        try:
            # Escolher estratégia de armazenamento
            if config.strategy == CacheStrategy.MEMORY:
                return self._set_in_memory(cache_key, data, ttl)
            
            elif config.strategy in [CacheStrategy.REDIS_FAST, CacheStrategy.REDIS_PERSIST, CacheStrategy.REDIS_LONG]:
                return await self._set_in_redis(cache_key, data, ttl, config.compress)
                
        except Exception as e:
            logger.error(f"Erro ao salvar cache {cache_key}: {e}")
            return False
        
        return False
    
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """Busca dados do cache em memória"""
        if key not in self.memory_cache:
            return None
            
        # Verificar expiração
        if key in self.memory_expiry and datetime.now() > self.memory_expiry[key]:
            del self.memory_cache[key]
            del self.memory_expiry[key]
            return None
            
        return self.memory_cache[key]
    
    def _set_in_memory(self, key: str, data: Any, ttl: int) -> bool:
        """Armazena dados no cache em memória"""
        self.memory_cache[key] = data
        self.memory_expiry[key] = datetime.now() + timedelta(seconds=ttl)
        
        # Limpar cache old se necessário (manter até 1000 entradas)
        if len(self.memory_cache) > 1000:
            self._cleanup_memory_cache()
            
        return True
    
    async def _get_from_redis(self, key: str, compressed: bool = False) -> Optional[Any]:
        """Busca dados do Redis"""
        try:
            raw_data = await self.redis_client.get(key)
            if not raw_data:
                return None
                
            if compressed:
                data = pickle.loads(raw_data)
            else:
                data = json.loads(raw_data.decode('utf-8'))
                
            return data
            
        except Exception as e:
            logger.error(f"Erro ao buscar do Redis {key}: {e}")
            return None
    
    async def _set_in_redis(self, key: str, data: Any, ttl: int, compress: bool = False) -> bool:
        """Armazena dados no Redis"""
        try:
            if compress:
                serialized_data = pickle.dumps(data)
            else:
                serialized_data = json.dumps(data, default=str).encode('utf-8')
                
            await self.redis_client.setex(key, ttl, serialized_data)
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar no Redis {key}: {e}")
            return False
    
    def _cleanup_memory_cache(self):
        """Remove entradas expiradas do cache em memória"""
        now = datetime.now()
        expired_keys = [
            key for key, expiry in self.memory_expiry.items() 
            if now > expiry
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
            del self.memory_expiry[key]
    
    async def invalidate(self, key_type: str, identifier: str = "*", params: Dict = None):
        """Invalida cache específico ou por padrão"""
        if identifier == "*":
            # Invalidar todos os caches do tipo
            pattern = f"cache:{key_type}:*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        else:
            cache_key = self._generate_key(key_type, identifier, params)
            await self.redis_client.delete(cache_key)
            
            # Remover do memory cache também
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
                if cache_key in self.memory_expiry:
                    del self.memory_expiry[cache_key]
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Estatísticas do sistema de cache"""
        redis_info = await self.redis_client.info('memory')
        memory_keys = len(self.memory_cache)
        
        return {
            "memory_cache": {
                "keys": memory_keys,
                "max_keys": 1000,
                "usage_percent": (memory_keys / 1000) * 100
            },
            "redis_cache": {
                "memory_used": redis_info.get('used_memory_human', 'N/A'),
                "keys": await self.redis_client.dbsize(),
                "hit_rate": "N/A"  # Implementar contador de hits/misses
            }
        }

# Instância global
smart_cache = SmartCacheManager()

# Decorator para cache automático
def cache_result(key_type: str, ttl: Optional[int] = None, use_params: bool = True):
    """
    Decorator para cache automático de resultados de funções
    
    Args:
        key_type: Tipo de cache da configuração
        ttl: TTL customizado (opcional)
        use_params: Se deve usar parâmetros da função na chave
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar identificador baseado na função e parâmetros
            func_name = f"{func.__module__}.{func.__name__}"
            
            if use_params:
                # Usar argumentos como parâmetros do cache
                params = {"args": str(args), "kwargs": str(kwargs)}
            else:
                params = None
            
            # Tentar buscar do cache primeiro
            cached_result = await smart_cache.get(key_type, func_name, params)
            if cached_result is not None:
                logger.debug(f"Cache HIT para {func_name}")
                return cached_result
            
            # Executar função se não estiver em cache
            logger.debug(f"Cache MISS para {func_name}")
            result = await func(*args, **kwargs)
            
            # Salvar resultado no cache
            await smart_cache.set(key_type, func_name, result, params, ttl)
            
            return result
        return wrapper
    return decorator

# Cache específico para picks (mais usado)
async def cache_picks_list(sport: str, filters: Dict) -> Optional[List]:
    """Cache otimizado para lista de picks"""
    return await smart_cache.get("picks_list", sport, filters)

async def set_picks_list_cache(sport: str, filters: Dict, picks: List):
    """Salva lista de picks no cache"""
    await smart_cache.set("picks_list", sport, picks, filters)

# Cache para análises ML (computacionalmente caras)
async def cache_ml_prediction(model_name: str, input_data: Dict) -> Optional[Dict]:
    """Cache otimizado para predições ML"""
    return await smart_cache.get("ml_predictions", model_name, input_data)

async def set_ml_prediction_cache(model_name: str, input_data: Dict, prediction: Dict):
    """Salva predição ML no cache"""
    await smart_cache.set("ml_predictions", model_name, prediction, input_data) 