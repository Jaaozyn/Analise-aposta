import redis.asyncio as redis
import json
from typing import Any, Optional
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class CacheManager:
    def __init__(self):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Buscar valor do cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Salvar valor no cache"""
        try:
            json_value = json.dumps(value, default=str)
            await self.redis.setex(key, expire, json_value)
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Deletar chave do cache"""
        try:
            await self.redis.delete(key)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Verificar se chave existe no cache"""
        try:
            return await self.redis.exists(key) > 0
        except Exception:
            return False
    
    async def flush_all(self) -> bool:
        """Limpar todo o cache"""
        try:
            await self.redis.flushall()
            return True
        except Exception:
            return False

cache = CacheManager() 