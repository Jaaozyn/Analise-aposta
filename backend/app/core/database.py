from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import AsyncGenerator

from app.core.config import settings

# Converter URL para async
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Engine assíncrono
async_engine = create_async_engine(
    database_url,
    echo=True,
    future=True
)

AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Inicializar banco de dados"""
    async with async_engine.begin() as conn:
        # Importar todos os modelos aqui para que sejam registrados no Base.metadata
        from app.models import user, match, pick, subscription, sport_data
        
        # Criar todas as tabelas
        await conn.run_sync(Base.metadata.create_all) 