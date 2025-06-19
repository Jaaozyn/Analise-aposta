"""
Configurações de Testes - QuantumBet
Setup centralizado para testes unitários, integração e E2E
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
import os
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import redis
from faker import Faker

# Imports da aplicação
from app.main import app
from app.core.config import settings
from app.core.database import get_db, Base
from app.core.auth import AuthService, JWTManager, TokenType
from app.models.user import User
from app.models.pick import Pick
from app.models.match import Match

# Configurar ambiente de teste
os.environ["TESTING"] = "1"
fake = Faker('pt_BR')

# Engine de teste (SQLite em memória)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Cria event loop para toda a sessão de testes"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_test_db():
    """Configura banco de dados de teste"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Sessão de banco de dados para cada teste"""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def override_get_db(db_session: AsyncSession):
    """Override da dependência get_db"""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP assíncrono para testes"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """Cliente HTTP síncrono para testes rápidos"""
    with TestClient(app) as c:
        yield c

# Fixtures para usuários
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Usuário de teste padrão"""
    user = User(
        email="test@quantumbet.com",
        hashed_password=AuthService.hash_password("testpassword123"),
        full_name="Usuário Teste",
        is_active=True,
        is_admin=False,
        balance=1000.0,
        total_roi=15.5,
        win_rate=68.5
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Usuário admin de teste"""
    user = User(
        email="admin@quantumbet.com",
        hashed_password=AuthService.hash_password("adminpassword123"),
        full_name="Admin Teste",
        is_active=True,
        is_admin=True,
        balance=5000.0,
        total_roi=25.8,
        win_rate=75.2
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def user_with_2fa(db_session: AsyncSession) -> User:
    """Usuário com 2FA habilitado"""
    user = User(
        email="2fa@quantumbet.com",
        hashed_password=AuthService.hash_password("2fapassword123"),
        full_name="Usuário 2FA",
        is_active=True,
        is_admin=False,
        two_factor_enabled=True,
        two_factor_secret="JBSWY3DPEHPK3PXP"  # Secret de teste
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Headers de autenticação para testes"""
    access_token = JWTManager.create_token(str(test_user.id), TokenType.ACCESS)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict:
    """Headers de autenticação admin para testes"""
    access_token = JWTManager.create_token(str(admin_user.id), TokenType.ACCESS)
    return {"Authorization": f"Bearer {access_token}"}

# Fixtures para dados de teste
@pytest.fixture
async def test_match(db_session: AsyncSession) -> Match:
    """Partida de teste"""
    match = Match(
        sport="football",
        home_team="Brasil",
        away_team="Argentina",
        start_time="2024-01-15T20:00:00Z",
        status="upcoming",
        home_odds=2.1,
        draw_odds=3.2,
        away_odds=3.8
    )
    db_session.add(match)
    await db_session.commit()
    await db_session.refresh(match)
    return match

@pytest.fixture
async def test_pick(db_session: AsyncSession, test_match: Match) -> Pick:
    """Pick de teste"""
    pick = Pick(
        match_id=test_match.id,
        prediction="Over 2.5 Goals",
        odds=2.1,
        expected_value=12.5,
        confidence_score=8.5,
        stake_suggestion=2.5,
        reasoning="Alta média de gols dos times",
        status="active"
    )
    db_session.add(pick)
    await db_session.commit()
    await db_session.refresh(pick)
    return pick

@pytest.fixture
def sample_picks_data():
    """Dados de picks para testes"""
    return [
        {
            "sport": "football",
            "prediction": "Over 2.5 Goals",
            "odds": 2.1,
            "expected_value": 12.5,
            "confidence_score": 8.5
        },
        {
            "sport": "basketball", 
            "prediction": "Under 210.5 Points",
            "odds": 1.9,
            "expected_value": 8.3,
            "confidence_score": 7.2
        },
        {
            "sport": "cs2",
            "prediction": "Team A ML",
            "odds": 1.75,
            "expected_value": 15.2,
            "confidence_score": 9.1
        }
    ]

# Mocks para serviços externos
@pytest.fixture
def mock_redis():
    """Mock do Redis"""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = True
    return mock

@pytest.fixture
def mock_sports_api():
    """Mock das APIs de esportes"""
    mock = MagicMock()
    mock.get_football_matches.return_value = [
        {
            "id": 1,
            "home_team": "Brasil",
            "away_team": "Argentina", 
            "start_time": "2024-01-15T20:00:00Z",
            "odds": {"home": 2.1, "draw": 3.2, "away": 3.8}
        }
    ]
    return mock

@pytest.fixture
def mock_payment_service():
    """Mock do serviço de pagamentos"""
    mock = MagicMock()
    mock.create_payment.return_value = {
        "id": "pay_123",
        "status": "pending",
        "amount": 99.00,
        "payment_url": "https://checkout.stripe.com/pay/123"
    }
    return mock

# Utilitários para testes
class TestDataFactory:
    """Factory para criar dados de teste"""
    
    @staticmethod
    def create_user_data(
        email: str = None,
        password: str = "testpassword123",
        **kwargs
    ) -> dict:
        """Cria dados de usuário para testes"""
        return {
            "email": email or fake.email(),
            "password": password,
            "confirm_password": password,
            "full_name": fake.name(),
            "agree_to_terms": True,
            **kwargs
        }
    
    @staticmethod
    def create_match_data(sport: str = "football", **kwargs) -> dict:
        """Cria dados de partida para testes"""
        teams = {
            "football": [("Brasil", "Argentina"), ("Real Madrid", "Barcelona")],
            "basketball": [("Lakers", "Warriors"), ("Heat", "Celtics")],
            "cs2": [("Team A", "Team B"), ("FaZe", "Astralis")]
        }
        
        home_team, away_team = fake.random_element(teams.get(sport, teams["football"]))
        
        return {
            "sport": sport,
            "home_team": home_team,
            "away_team": away_team,
            "start_time": fake.future_datetime(end_date="+30d").isoformat(),
            "status": "upcoming",
            "home_odds": round(fake.random.uniform(1.5, 4.0), 2),
            "draw_odds": round(fake.random.uniform(2.5, 5.0), 2),
            "away_odds": round(fake.random.uniform(1.5, 4.0), 2),
            **kwargs
        }
    
    @staticmethod
    def create_pick_data(match_id: int = 1, **kwargs) -> dict:
        """Cria dados de pick para testes"""
        predictions = [
            "Over 2.5 Goals", "Under 2.5 Goals", "Home Win",
            "Away Win", "Both Teams Score", "Clean Sheet"
        ]
        
        return {
            "match_id": match_id,
            "prediction": fake.random_element(predictions),
            "odds": round(fake.random.uniform(1.5, 3.0), 2),
            "expected_value": round(fake.random.uniform(5.0, 20.0), 1),
            "confidence_score": round(fake.random.uniform(6.0, 10.0), 1),
            "stake_suggestion": round(fake.random.uniform(1.0, 5.0), 1),
            "reasoning": fake.text(max_nb_chars=200),
            "status": "active",
            **kwargs
        }

@pytest.fixture
def test_data_factory():
    """Factory de dados de teste"""
    return TestDataFactory

# Configurações para diferentes tipos de teste
pytest_plugins = [
    "tests.unit.test_auth",
    "tests.unit.test_picks", 
    "tests.unit.test_ml",
    "tests.integration.test_api",
    "tests.e2e.test_user_flows",
    "tests.performance.test_load"
]

# Marcadores de teste
def pytest_configure(config):
    """Configuração de marcadores de teste"""
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "e2e: marca testes end-to-end"
    )
    config.addinivalue_line(
        "markers", "performance: marca testes de performance"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes lentos"
    )
    config.addinivalue_line(
        "markers", "auth: marca testes de autenticação"
    )
    config.addinivalue_line(
        "markers", "ml: marca testes de machine learning"
    )
    config.addinivalue_line(
        "markers", "api: marca testes de API"
    )

# Setup e teardown global
@pytest.fixture(autouse=True)
async def setup_test_environment():
    """Setup automático para cada teste"""
    # Limpar estado global antes de cada teste
    yield
    # Cleanup após cada teste
    pass 