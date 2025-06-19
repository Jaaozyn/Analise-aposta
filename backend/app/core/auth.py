"""
Sistema de Autenticação JWT Robusto - QuantumBet
Inclui 2FA, refresh tokens, session management e políticas de senha
"""

import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import re
from dataclasses import dataclass
from enum import Enum
import logging

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.core.cache import redis_client
from app.core.rate_limiter import enhanced_rate_limit_check

logger = logging.getLogger(__name__)

# Configuração de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class TokenType(Enum):
    """Tipos de tokens JWT"""
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"

@dataclass
class TokenData:
    """Dados do token JWT"""
    sub: str  # user_id
    token_type: TokenType
    exp: datetime
    iat: datetime
    jti: str  # JWT ID único
    scope: str = "user"
    
class PasswordPolicy:
    """Políticas de senha robustas"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, str]:
        """Valida senha contra políticas"""
        if len(password) < cls.MIN_LENGTH:
            return False, f"Senha deve ter pelo menos {cls.MIN_LENGTH} caracteres"
        
        if len(password) > cls.MAX_LENGTH:
            return False, f"Senha não pode ter mais de {cls.MAX_LENGTH} caracteres"
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Senha deve conter pelo menos uma letra maiúscula"
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Senha deve conter pelo menos uma letra minúscula"
        
        if cls.REQUIRE_NUMBERS and not re.search(r'\d', password):
            return False, "Senha deve conter pelo menos um número"
        
        if cls.REQUIRE_SPECIAL and not re.search(f'[{re.escape(cls.SPECIAL_CHARS)}]', password):
            return False, f"Senha deve conter pelo menos um caractere especial: {cls.SPECIAL_CHARS}"
        
        # Verificar padrões comuns
        common_patterns = [
            r'123456', r'password', r'qwerty', r'abc123',
            r'(.)\1{2,}',  # Repetição de caracteres
            r'01234|12345|23456|34567|45678|56789'  # Sequências numéricas
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                return False, "Senha muito comum ou previsível"
        
        return True, "Senha válida"

class TwoFactorAuth:
    """Sistema de autenticação de dois fatores (2FA)"""
    
    @staticmethod
    def generate_secret() -> str:
        """Gera secret para TOTP"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user_email: str, secret: str) -> str:
        """Gera QR code para configuração do 2FA"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="QuantumBet"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_token(secret: str, token: str) -> bool:
        """Verifica token TOTP"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # ±30 segundos

class JWTManager:
    """Gerenciador de tokens JWT"""
    
    @staticmethod
    def create_token(
        user_id: str,
        token_type: TokenType,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Cria token JWT"""
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Tempos padrão por tipo de token
            if token_type == TokenType.ACCESS:
                expire = datetime.now(timezone.utc) + timedelta(minutes=15)
            elif token_type == TokenType.REFRESH:
                expire = datetime.now(timezone.utc) + timedelta(days=7)
            elif token_type == TokenType.EMAIL_VERIFICATION:
                expire = datetime.now(timezone.utc) + timedelta(hours=24)
            elif token_type == TokenType.PASSWORD_RESET:
                expire = datetime.now(timezone.utc) + timedelta(hours=1)
        
        jti = secrets.token_urlsafe(32)
        iat = datetime.now(timezone.utc)
        
        payload = {
            "sub": str(user_id),
            "token_type": token_type.value,
            "exp": expire,
            "iat": iat,
            "jti": jti
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        # Armazenar JTI no Redis para revogação
        redis_key = f"jwt:{jti}"
        redis_client.setex(
            redis_key, 
            int((expire - iat).total_seconds()), 
            f"{user_id}:{token_type.value}"
        )
        
        return token
    
    @staticmethod
    async def verify_token(token: str, expected_type: TokenType) -> TokenData:
        """Verifica e decodifica token JWT"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            
            # Verificar tipo de token
            if payload.get("token_type") != expected_type.value:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tipo de token inválido"
                )
            
            # Verificar se token foi revogado
            jti = payload.get("jti")
            if jti:
                redis_key = f"jwt:{jti}"
                if not await redis_client.exists(redis_key):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token revogado"
                    )
            
            return TokenData(
                sub=payload["sub"],
                token_type=TokenType(payload["token_type"]),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                jti=jti
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
    
    @staticmethod
    async def revoke_token(jti: str):
        """Revoga token específico"""
        redis_key = f"jwt:{jti}"
        await redis_client.delete(redis_key)
    
    @staticmethod
    async def revoke_all_user_tokens(user_id: str):
        """Revoga todos os tokens de um usuário"""
        pattern = f"jwt:*"
        keys = await redis_client.keys(pattern)
        
        for key in keys:
            value = await redis_client.get(key)
            if value and value.startswith(f"{user_id}:"):
                await redis_client.delete(key)

class SessionManager:
    """Gerenciador de sessões"""
    
    @staticmethod
    async def create_session(user_id: str, request: Request) -> str:
        """Cria nova sessão"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ip_address": request.client.host if hasattr(request, 'client') else None,
            "user_agent": request.headers.get("user-agent"),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
        
        # Armazenar sessão por 30 dias
        redis_key = f"session:{session_id}"
        await redis_client.setex(redis_key, 2592000, json.dumps(session_data))
        
        return session_id
    
    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict]:
        """Recupera dados da sessão"""
        redis_key = f"session:{session_id}"
        data = await redis_client.get(redis_key)
        
        if data:
            return json.loads(data)
        return None
    
    @staticmethod
    async def update_session_activity(session_id: str):
        """Atualiza última atividade da sessão"""
        session_data = await SessionManager.get_session(session_id)
        if session_data:
            session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
            redis_key = f"session:{session_id}"
            await redis_client.setex(redis_key, 2592000, json.dumps(session_data))
    
    @staticmethod
    async def revoke_session(session_id: str):
        """Revoga sessão específica"""
        redis_key = f"session:{session_id}"
        await redis_client.delete(redis_key)
    
    @staticmethod
    async def revoke_all_user_sessions(user_id: str):
        """Revoga todas as sessões de um usuário"""
        pattern = "session:*"
        keys = await redis_client.keys(pattern)
        
        for key in keys:
            data = await redis_client.get(key)
            if data:
                session_data = json.loads(data)
                if session_data.get("user_id") == user_id:
                    await redis_client.delete(key)

class AuthService:
    """Serviço principal de autenticação"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash da senha"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica senha"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession, 
        email: str, 
        password: str,
        totp_token: Optional[str] = None
    ) -> Optional[User]:
        """Autentica usuário com email/senha e 2FA opcional"""
        
        # Buscar usuário
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        
        # Verificar se conta está ativa
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Conta desativada"
            )
        
        # Verificar 2FA se habilitado
        if user.two_factor_enabled:
            if not totp_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 2FA obrigatório",
                    headers={"X-Require-2FA": "true"}
                )
            
            if not TwoFactorAuth.verify_token(user.two_factor_secret, totp_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 2FA inválido"
                )
        
        # Atualizar último login
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        
        return user
    
    @staticmethod
    async def create_tokens(user_id: str) -> Dict[str, str]:
        """Cria access e refresh tokens"""
        access_token = JWTManager.create_token(user_id, TokenType.ACCESS)
        refresh_token = JWTManager.create_token(user_id, TokenType.REFRESH)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        """Atualiza access token usando refresh token"""
        token_data = await JWTManager.verify_token(refresh_token, TokenType.REFRESH)
        
        # Revogar refresh token antigo
        await JWTManager.revoke_token(token_data.jti)
        
        # Criar novos tokens
        return await AuthService.create_tokens(token_data.sub)

# Dependências para FastAPI
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency para obter usuário atual autenticado"""
    
    # Rate limiting para autenticação
    await enhanced_rate_limit_check(
        request, 
        endpoint_type="auth_verify", 
        limit="60/hour"  # 60 verificações por hora
    )
    
    # Verificar token
    token_data = await JWTManager.verify_token(credentials.credentials, TokenType.ACCESS)
    
    # Buscar usuário
    result = await db.execute(select(User).filter(User.id == int(token_data.sub)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conta desativada"
        )
    
    return user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency para obter usuário admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso administrativo necessário"
        )
    return current_user

async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Dependency para obter usuário opcional (pode ser None)"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        token_data = await JWTManager.verify_token(token, TokenType.ACCESS)
        
        result = await db.execute(select(User).filter(User.id == int(token_data.sub)))
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            return user
            
    except Exception:
        pass
    
    return None 