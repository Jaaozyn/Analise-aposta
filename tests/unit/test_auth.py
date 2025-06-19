"""
Testes Unitários - Sistema de Autenticação
Testa JWT, 2FA, políticas de senha e gerenciamento de sessões
"""

import pytest
import jwt
import pyotp
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from httpx import AsyncClient

from app.core.auth import (
    AuthService, JWTManager, TwoFactorAuth, PasswordPolicy,
    SessionManager, TokenType
)
from app.models.user import User


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordPolicy:
    """Testes para políticas de senha"""
    
    def test_valid_password(self):
        """Testa senha válida"""
        valid_password = "MinhaSenh@123"
        is_valid, message = PasswordPolicy.validate(valid_password)
        assert is_valid is True
        assert message == "Senha válida"
    
    def test_too_short_password(self):
        """Testa senha muito curta"""
        short_password = "Ab1@"
        is_valid, message = PasswordPolicy.validate(short_password)
        assert is_valid is False
        assert "pelo menos 8 caracteres" in message
    
    def test_no_uppercase(self):
        """Testa senha sem maiúscula"""
        password = "minhasenha@123"
        is_valid, message = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "letra maiúscula" in message
    
    def test_no_lowercase(self):
        """Testa senha sem minúscula"""
        password = "MINHASENHA@123"
        is_valid, message = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "letra minúscula" in message
    
    def test_no_numbers(self):
        """Testa senha sem números"""
        password = "MinhaSenha@"
        is_valid, message = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "número" in message
    
    def test_no_special_chars(self):
        """Testa senha sem caracteres especiais"""
        password = "MinhaSenha123"
        is_valid, message = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "caractere especial" in message
    
    def test_common_password(self):
        """Testa senhas comuns"""
        common_passwords = ["password123", "123456789", "qwerty123"]
        for password in common_passwords:
            is_valid, message = PasswordPolicy.validate(password)
            assert is_valid is False
            assert "comum ou previsível" in message
    
    def test_repeated_characters(self):
        """Testa senhas com muita repetição"""
        password = "Aaaaaa1@"
        is_valid, message = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "comum ou previsível" in message


@pytest.mark.unit
@pytest.mark.auth
class TestTwoFactorAuth:
    """Testes para autenticação de dois fatores"""
    
    def test_generate_secret(self):
        """Testa geração de secret"""
        secret = TwoFactorAuth.generate_secret()
        assert len(secret) == 32
        assert secret.isalnum()
        assert secret.isupper()
    
    def test_generate_qr_code(self):
        """Testa geração de QR code"""
        secret = "JBSWY3DPEHPK3PXP"
        email = "test@quantumbet.com"
        qr_code = TwoFactorAuth.generate_qr_code(email, secret)
        assert qr_code.startswith("data:image/png;base64,")
    
    def test_verify_valid_token(self):
        """Testa verificação de token válido"""
        secret = "JBSWY3DPEHPK3PXP"
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        is_valid = TwoFactorAuth.verify_token(secret, token)
        assert is_valid is True
    
    def test_verify_invalid_token(self):
        """Testa verificação de token inválido"""
        secret = "JBSWY3DPEHPK3PXP"
        invalid_token = "000000"
        
        is_valid = TwoFactorAuth.verify_token(secret, invalid_token)
        assert is_valid is False


@pytest.mark.unit
@pytest.mark.auth
class TestJWTManager:
    """Testes para gerenciamento de JWT"""
    
    def test_create_access_token(self):
        """Testa criação de access token"""
        user_id = "123"
        token = JWTManager.create_token(user_id, TokenType.ACCESS)
        
        # Decodificar sem verificar expiração
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert payload["sub"] == user_id
        assert payload["token_type"] == TokenType.ACCESS.value
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_create_refresh_token(self):
        """Testa criação de refresh token"""
        user_id = "123"
        token = JWTManager.create_token(user_id, TokenType.REFRESH)
        
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert payload["sub"] == user_id
        assert payload["token_type"] == TokenType.REFRESH.value
    
    @pytest.mark.asyncio
    async def test_verify_valid_token(self):
        """Testa verificação de token válido"""
        user_id = "123"
        token = JWTManager.create_token(user_id, TokenType.ACCESS)
        
        with patch('app.core.auth.redis_client') as mock_redis:
            mock_redis.exists.return_value = True
            
            token_data = await JWTManager.verify_token(token, TokenType.ACCESS)
            
            assert token_data.sub == user_id
            assert token_data.token_type == TokenType.ACCESS
    
    @pytest.mark.asyncio
    async def test_verify_expired_token(self):
        """Testa verificação de token expirado"""
        user_id = "123"
        expired_delta = timedelta(seconds=-1)  # Token já expirado
        token = JWTManager.create_token(user_id, TokenType.ACCESS, expired_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            await JWTManager.verify_token(token, TokenType.ACCESS)
        
        assert exc_info.value.status_code == 401
        assert "Token expirado" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_verify_revoked_token(self):
        """Testa verificação de token revogado"""
        user_id = "123"
        token = JWTManager.create_token(user_id, TokenType.ACCESS)
        
        with patch('app.core.auth.redis_client') as mock_redis:
            mock_redis.exists.return_value = False  # Token não existe = revogado
            
            with pytest.raises(HTTPException) as exc_info:
                await JWTManager.verify_token(token, TokenType.ACCESS)
            
            assert exc_info.value.status_code == 401
            assert "Token revogado" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_verify_wrong_token_type(self):
        """Testa verificação de tipo de token errado"""
        user_id = "123"
        token = JWTManager.create_token(user_id, TokenType.REFRESH)
        
        with patch('app.core.auth.redis_client') as mock_redis:
            mock_redis.exists.return_value = True
            
            with pytest.raises(HTTPException) as exc_info:
                await JWTManager.verify_token(token, TokenType.ACCESS)
            
            assert exc_info.value.status_code == 401
            assert "Tipo de token inválido" in str(exc_info.value.detail)


@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    """Testes para serviço de autenticação"""
    
    def test_hash_password(self):
        """Testa hash de senha"""
        password = "minhasenha123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50
    
    def test_verify_password(self):
        """Testa verificação de senha"""
        password = "minhasenha123"
        hashed = AuthService.hash_password(password)
        
        # Senha correta
        assert AuthService.verify_password(password, hashed) is True
        
        # Senha incorreta
        assert AuthService.verify_password("senhaerrada", hashed) is False
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session, test_user):
        """Testa autenticação bem-sucedida"""
        user = await AuthService.authenticate_user(
            db_session,
            test_user.email,
            "testpassword123"
        )
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session, test_user):
        """Testa autenticação com senha errada"""
        user = await AuthService.authenticate_user(
            db_session,
            test_user.email,
            "senhaerrada"
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, db_session):
        """Testa autenticação com usuário inexistente"""
        user = await AuthService.authenticate_user(
            db_session,
            "inexistente@quantumbet.com",
            "qualquersenha"
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_with_2fa_success(self, db_session, user_with_2fa):
        """Testa autenticação com 2FA bem-sucedida"""
        # Gerar token TOTP válido
        totp = pyotp.TOTP(user_with_2fa.two_factor_secret)
        token = totp.now()
        
        user = await AuthService.authenticate_user(
            db_session,
            user_with_2fa.email,
            "2fapassword123",
            token
        )
        
        assert user is not None
        assert user.id == user_with_2fa.id
    
    @pytest.mark.asyncio
    async def test_authenticate_user_with_2fa_missing_token(self, db_session, user_with_2fa):
        """Testa autenticação com 2FA sem token"""
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.authenticate_user(
                db_session,
                user_with_2fa.email,
                "2fapassword123"
            )
        
        assert exc_info.value.status_code == 401
        assert "Token 2FA obrigatório" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_with_2fa_invalid_token(self, db_session, user_with_2fa):
        """Testa autenticação com 2FA e token inválido"""
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.authenticate_user(
                db_session,
                user_with_2fa.email,
                "2fapassword123",
                "000000"  # Token inválido
            )
        
        assert exc_info.value.status_code == 401
        assert "Token 2FA inválido" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_create_tokens(self):
        """Testa criação de tokens"""
        user_id = "123"
        tokens = await AuthService.create_tokens(user_id)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Verificar se tokens são válidos
        access_payload = jwt.decode(tokens["access_token"], options={"verify_signature": False})
        refresh_payload = jwt.decode(tokens["refresh_token"], options={"verify_signature": False})
        
        assert access_payload["sub"] == user_id
        assert refresh_payload["sub"] == user_id
        assert access_payload["token_type"] == TokenType.ACCESS.value
        assert refresh_payload["token_type"] == TokenType.REFRESH.value
    
    @pytest.mark.asyncio
    async def test_refresh_access_token(self):
        """Testa renovação de access token"""
        user_id = "123"
        
        with patch('app.core.auth.redis_client') as mock_redis:
            mock_redis.exists.return_value = True
            mock_redis.delete.return_value = True
            mock_redis.setex.return_value = True
            
            # Criar refresh token
            refresh_token = JWTManager.create_token(user_id, TokenType.REFRESH)
            
            # Renovar tokens
            new_tokens = await AuthService.refresh_access_token(refresh_token)
            
            assert "access_token" in new_tokens
            assert "refresh_token" in new_tokens
            assert "token_type" in new_tokens
            
            # Verificar novos tokens
            access_payload = jwt.decode(new_tokens["access_token"], options={"verify_signature": False})
            assert access_payload["sub"] == user_id


@pytest.mark.unit
@pytest.mark.auth
class TestSessionManager:
    """Testes para gerenciamento de sessões"""
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """Testa criação de sessão"""
        user_id = "123"
        
        # Mock do request
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Mozilla/5.0"
        
        with patch('app.core.auth.redis_client') as mock_redis:
            mock_redis.setex.return_value = True
            
            session_id = await SessionManager.create_session(user_id, mock_request)
            
            assert len(session_id) > 30
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session(self):
        """Testa recuperação de sessão"""
        session_id = "test_session_123"
        session_data = {
            "user_id": "123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ip_address": "127.0.0.1"
        }
        
        with patch('app.core.auth.redis_client') as mock_redis:
            mock_redis.get.return_value = json.dumps(session_data)
            
            result = await SessionManager.get_session(session_id)
            
            assert result == session_data
            mock_redis.get.assert_called_once_with(f"session:{session_id}")
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self):
        """Testa recuperação de sessão inexistente"""
        session_id = "nonexistent_session"
        
        with patch('app.core.auth.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            
            result = await SessionManager.get_session(session_id)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_revoke_session(self):
        """Testa revogação de sessão"""
        session_id = "test_session_123"
        
        with patch('app.core.auth.redis_client') as mock_redis:
            mock_redis.delete.return_value = True
            
            await SessionManager.revoke_session(session_id)
            
            mock_redis.delete.assert_called_once_with(f"session:{session_id}")


# Testes de integração dos endpoints de auth
@pytest.mark.integration
@pytest.mark.auth
class TestAuthEndpoints:
    """Testes de integração para endpoints de autenticação"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Testa login bem-sucedido"""
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user):
        """Testa login com credenciais inválidas"""
        login_data = {
            "email": test_user.email,
            "password": "senhaerrada"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Email ou senha incorretos" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Testa registro bem-sucedido"""
        register_data = {
            "email": "novo@quantumbet.com",
            "password": "NovaSenh@123",
            "confirm_password": "NovaSenh@123",
            "full_name": "Usuário Novo",
            "agree_to_terms": True
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["user"]["email"] == register_data["email"]
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Testa registro com senha fraca"""
        register_data = {
            "email": "fraco@quantumbet.com",
            "password": "123456",  # Senha fraca
            "confirm_password": "123456",
            "full_name": "Usuário Fraco",
            "agree_to_terms": True
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 400
        assert "Senha inválida" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Testa obtenção de usuário atual"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Testa acesso sem autenticação"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # Ou 401, dependendo da implementação 