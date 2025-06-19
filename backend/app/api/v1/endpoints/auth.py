"""
Auth Endpoints - Sistema de Autenticação Robusto
Endpoints para login, registro, 2FA, refresh tokens e gerenciamento de sessões
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from app.core.database import get_db
from app.core.auth import (
    AuthService, JWTManager, TwoFactorAuth, PasswordPolicy,
    SessionManager, TokenType, get_current_user
)
from app.models.user import User
from app.core.rate_limiter import limiter, enhanced_rate_limit_check
from app.core.audit_trail import log_security_event, AuditEventType

router = APIRouter()

# Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    totp_token: Optional[str] = Field(None, min_length=6, max_length=6)
    remember_me: bool = False

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    full_name: str = Field(..., min_length=2, max_length=100)
    agree_to_terms: bool

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

class Enable2FAResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list[str]

class Verify2FARequest(BaseModel):
    secret: str
    token: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ConfirmResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    🔐 Login com email/senha e 2FA opcional
    """
    # Rate limiting específico para login
    await enhanced_rate_limit_check(
        request, 
        endpoint_type="auth_login", 
        limit="10/hour"  # 10 tentativas por hora
    )
    
    try:
        # Autenticar usuário
        user = await AuthService.authenticate_user(
            db, 
            login_data.email, 
            login_data.password,
            login_data.totp_token
        )
        
        if not user:
            # Log de tentativa de login falhada
            await log_security_event(
                AuditEventType.FAILED_LOGIN,
                f"Tentativa de login falhada para {login_data.email}",
                ip_address=request.client.host if hasattr(request, 'client') else None,
                data={"email": login_data.email}
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )
        
        # Criar tokens
        tokens = await AuthService.create_tokens(str(user.id))
        
        # Criar sessão se remember_me
        if login_data.remember_me:
            session_id = await SessionManager.create_session(str(user.id), request)
            response.set_cookie(
                key="session_id",
                value=session_id,
                max_age=2592000,  # 30 dias
                httponly=True,
                secure=True,
                samesite="strict"
            )
        
        # Log de login bem-sucedido
        await log_security_event(
            AuditEventType.USER_LOGIN,
            f"Login bem-sucedido para {user.email}",
            user_id=user.id,
            ip_address=request.client.host if hasattr(request, 'client') else None
        )
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=900,  # 15 minutos
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin,
                "two_factor_enabled": user.two_factor_enabled,
                "subscription_tier": user.subscription_tier
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await log_security_event(
            AuditEventType.SYSTEM_ERROR,
            f"Erro no login: {str(e)}",
            ip_address=request.client.host if hasattr(request, 'client') else None
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    📝 Registro de novo usuário
    """
    # Rate limiting para registro
    await enhanced_rate_limit_check(
        request,
        endpoint_type="auth_register",
        limit="5/hour"  # 5 registros por hora por IP
    )
    
    # Validar dados
    if register_data.password != register_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senhas não conferem"
        )
    
    if not register_data.agree_to_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você deve aceitar os termos de uso"
        )
    
    # Validar política de senha
    is_valid, message = PasswordPolicy.validate(register_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Senha inválida: {message}"
        )
    
    # Verificar se email já existe
    result = await db.execute(select(User).filter(User.email == register_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    try:
        # Criar usuário
        hashed_password = AuthService.hash_password(register_data.password)
        
        user = User(
            email=register_data.email,
            hashed_password=hashed_password,
            full_name=register_data.full_name,
            is_active=True,  # Em produção, pode requerer verificação de email
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Criar tokens
        tokens = await AuthService.create_tokens(str(user.id))
        
        # Log de registro
        await log_security_event(
            AuditEventType.USER_REGISTER,
            f"Novo usuário registrado: {user.email}",
            user_id=user.id,
            ip_address=request.client.host if hasattr(request, 'client') else None
        )
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=900,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin,
                "two_factor_enabled": user.two_factor_enabled,
                "subscription_tier": user.subscription_tier
            }
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar usuário"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    🔄 Renovar access token usando refresh token
    """
    await enhanced_rate_limit_check(
        request,
        endpoint_type="auth_refresh",
        limit="30/hour"
    )
    
    try:
        # Renovar tokens
        new_tokens = await AuthService.refresh_access_token(refresh_data.refresh_token)
        
        # Buscar dados do usuário
        token_data = await JWTManager.verify_token(
            new_tokens["access_token"], 
            TokenType.ACCESS
        )
        
        result = await db.execute(select(User).filter(User.id == int(token_data.sub)))
        user = result.scalar_one_or_none()
        
        return TokenResponse(
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens["refresh_token"],
            expires_in=900,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin,
                "two_factor_enabled": user.two_factor_enabled,
                "subscription_tier": user.subscription_tier
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização inválido"
        )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    🚪 Logout - revoga tokens e sessões
    """
    try:
        # Revogar todos os tokens do usuário
        await JWTManager.revoke_all_user_tokens(str(current_user.id))
        
        # Revogar todas as sessões
        await SessionManager.revoke_all_user_sessions(str(current_user.id))
        
        # Remover cookie de sessão
        response.delete_cookie("session_id")
        
        # Log de logout
        await log_security_event(
            AuditEventType.USER_LOGOUT,
            f"Logout realizado para {current_user.email}",
            user_id=current_user.id,
            ip_address=request.client.host if hasattr(request, 'client') else None
        )
        
        return {"message": "Logout realizado com sucesso"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao realizar logout"
        )

@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    📱 Habilitar autenticação de dois fatores
    """
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA já está habilitado"
        )
    
    # Gerar secret
    secret = TwoFactorAuth.generate_secret()
    
    # Gerar QR code
    qr_code = TwoFactorAuth.generate_qr_code(current_user.email, secret)
    
    # Gerar códigos de backup
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
    
    # Salvar secret temporário (será confirmado quando verificar)
    current_user.two_factor_secret = secret
    current_user.backup_codes = backup_codes
    await db.commit()
    
    return Enable2FAResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )

@router.post("/2fa/verify")
async def verify_2fa(
    request: Request,
    verify_data: Verify2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Verificar e confirmar 2FA
    """
    if not TwoFactorAuth.verify_token(verify_data.secret, verify_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token 2FA inválido"
        )
    
    # Habilitar 2FA
    current_user.two_factor_enabled = True
    await db.commit()
    
    # Log de habilitação 2FA
    await log_security_event(
        AuditEventType.USER_LOGIN,  # Pode criar novo tipo
        f"2FA habilitado para {current_user.email}",
        user_id=current_user.id,
        ip_address=request.client.host if hasattr(request, 'client') else None
    )
    
    return {"message": "2FA habilitado com sucesso"}

@router.post("/2fa/disable")
async def disable_2fa(
    request: Request,
    totp_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ❌ Desabilitar 2FA
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA não está habilitado"
        )
    
    if not TwoFactorAuth.verify_token(current_user.two_factor_secret, totp_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token 2FA inválido"
        )
    
    # Desabilitar 2FA
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.backup_codes = None
    await db.commit()
    
    return {"message": "2FA desabilitado com sucesso"}

@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    🔑 Alterar senha
    """
    # Rate limiting para mudança de senha
    await enhanced_rate_limit_check(
        request,
        endpoint_type="auth_password_change",
        limit="5/hour"
    )
    
    # Verificar senha atual
    if not AuthService.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Validar nova senha
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senhas não conferem"
        )
    
    is_valid, message = PasswordPolicy.validate(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nova senha inválida: {message}"
        )
    
    # Atualizar senha
    current_user.hashed_password = AuthService.hash_password(password_data.new_password)
    await db.commit()
    
    # Revogar todos os tokens (usuário precisa fazer login novamente)
    await JWTManager.revoke_all_user_tokens(str(current_user.id))
    
    # Log de mudança de senha
    await log_security_event(
        AuditEventType.PASSWORD_CHANGE,
        f"Senha alterada para {current_user.email}",
        user_id=current_user.id,
        ip_address=request.client.host if hasattr(request, 'client') else None
    )
    
    return {"message": "Senha alterada com sucesso. Faça login novamente."}

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    👤 Informações do usuário atual
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_admin": current_user.is_admin,
        "two_factor_enabled": current_user.two_factor_enabled,
        "subscription_tier": current_user.subscription_tier,
        "balance": current_user.balance,
        "total_roi": current_user.total_roi,
        "win_rate": current_user.win_rate,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    } 