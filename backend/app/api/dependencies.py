"""
API Dependencies - Dependências de Autenticação e Validação
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from datetime import datetime

from app.core.config import settings
from app.models.user import User

security = HTTPBearer()

async def get_current_user() -> User:
    """Dependency para obter usuário atual (mock)"""
    # Mock user para desenvolvimento
    return User(
        id=1,
        email="user@quantumbet.com",
        is_active=True,
        is_admin=False,
        balance=1000.0,
        total_roi=15.5,
        win_rate=68.5
    )

async def get_current_user_websocket() -> User:
    """Dependency para WebSocket (mock)"""
    # Mock user para desenvolvimento
    return User(
        id=1,
        email="admin@quantumbet.com",
        is_active=True,
        is_admin=True,
        balance=5000.0,
        total_roi=25.8,
        win_rate=75.2
    ) 