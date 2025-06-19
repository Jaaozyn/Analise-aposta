"""
Audit Trail System - Sistema de Auditoria Completo
Rastreabilidade total para compliance, segurança e análise de comportamento
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import Request
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings
from app.core.database import Base
from app.core.cache import redis_client

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Tipos de eventos auditáveis"""
    
    # Autenticação e Autorização
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    PASSWORD_CHANGE = "password_change"
    FAILED_LOGIN = "failed_login"
    
    # Ações de Usuário
    PICK_GENERATED = "pick_generated"
    PICK_VIEWED = "pick_viewed"
    PICK_FAVORITED = "pick_favorited"
    PROFILE_UPDATED = "profile_updated"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    
    # Pagamentos
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REFUNDED = "payment_refunded"
    
    # Sistema/Admin
    SYSTEM_ERROR = "system_error"
    ADMIN_ACTION = "admin_action"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    
    # API Usage
    API_CALL = "api_call"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Conformidade
    GDPR_REQUEST = "gdpr_request"
    DATA_BREACH = "data_breach"
    POLICY_VIOLATION = "policy_violation"

class AuditSeverity(Enum):
    """Níveis de severidade dos eventos"""
    
    LOW = "low"           # Ações normais do usuário
    MEDIUM = "medium"     # Ações importantes
    HIGH = "high"         # Ações críticas de segurança
    CRITICAL = "critical" # Violações, ataques, falhas de segurança

@dataclass
class AuditEvent:
    """Estrutura padronizada para eventos de auditoria"""
    
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

class AuditLog(Base):
    """Modelo de banco de dados para logs de auditoria"""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    data = Column(Text, nullable=True)  # JSON serializado
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    request_id = Column(String(255), nullable=True, index=True)
    
    # Índices compostos para queries eficientes
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_event_timestamp', 'event_type', 'timestamp'),
        Index('idx_severity_timestamp', 'severity', 'timestamp'),
        Index('idx_ip_timestamp', 'ip_address', 'timestamp'),
    )

class AuditTrailManager:
    """Gerenciador central do sistema de auditoria"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.batch_size = 100
        self.batch_timeout = 30  # segundos
        self._batch_buffer: List[AuditEvent] = []
        
        # Configurações de retenção por tipo de evento
        self.retention_config = {
            AuditEventType.USER_LOGIN: 90,      # 90 dias
            AuditEventType.FAILED_LOGIN: 365,   # 1 ano
            AuditEventType.PAYMENT_COMPLETED: 2555,  # 7 anos (compliance)
            AuditEventType.GDPR_REQUEST: 2555,  # 7 anos
            AuditEventType.DATA_BREACH: 2555,   # 7 anos
            AuditEventType.SUSPICIOUS_ACTIVITY: 365,  # 1 ano
            "default": 180  # 6 meses
        }
    
    async def log_event(
        self, 
        event: AuditEvent, 
        db: Optional[AsyncSession] = None,
        immediate: bool = False
    ) -> str:
        """
        Registra evento de auditoria
        
        Args:
            event: Evento a ser registrado
            db: Sessão de banco (opcional)
            immediate: Se deve salvar imediatamente (não usar batch)
            
        Returns:
            ID do evento registrado
        """
        # Gerar ID único para o evento
        event_id = self._generate_event_id(event)
        
        # Enriquecer dados do evento
        enriched_event = await self._enrich_event(event)
        
        # Log estruturado
        logger.info(
            f"AUDIT: {event.event_type.value}",
            extra={
                "event_id": event_id,
                "user_id": event.user_id,
                "severity": event.severity.value,
                "ip": event.ip_address,
                "endpoint": event.endpoint
            }
        )
        
        if immediate or event.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
            # Salvar imediatamente para eventos críticos
            await self._save_to_database(enriched_event, db)
            
            # Alertas para eventos críticos
            if event.severity == AuditSeverity.CRITICAL:
                await self._send_critical_alert(enriched_event)
        else:
            # Adicionar ao batch para processamento otimizado
            self._batch_buffer.append(enriched_event)
            
            # Processar batch se atingir o limite
            if len(self._batch_buffer) >= self.batch_size:
                await self._process_batch(db)
        
        return event_id
    
    async def _enrich_event(self, event: AuditEvent) -> AuditEvent:
        """Enriquece evento com dados adicionais"""
        
        # Calcular hash para integridade
        event_hash = self._calculate_event_hash(event)
        
        # Adicionar dados contextuais
        if event.data is None:
            event.data = {}
        
        event.data['event_hash'] = event_hash
        event.data['server_timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Geolocalização do IP (cache Redis)
        if event.ip_address:
            geo_data = await self._get_ip_geolocation(event.ip_address)
            if geo_data:
                event.data['geo_location'] = geo_data
        
        return event
    
    def _generate_event_id(self, event: AuditEvent) -> str:
        """Gera ID único para o evento"""
        data_str = f"{event.event_type.value}{event.timestamp}{event.user_id}{event.ip_address}"
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _calculate_event_hash(self, event: AuditEvent) -> str:
        """Calcula hash para integridade do evento"""
        # Dados essenciais para integridade
        core_data = {
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat() if event.timestamp else None,
            'user_id': event.user_id,
            'description': event.description,
            'endpoint': event.endpoint
        }
        
        data_str = json.dumps(core_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def _get_ip_geolocation(self, ip_address: str) -> Optional[Dict]:
        """Busca geolocalização do IP (com cache)"""
        cache_key = f"geo:{ip_address}"
        
        try:
            # Buscar do cache primeiro
            cached_geo = await self.redis_client.get(cache_key)
            if cached_geo:
                return json.loads(cached_geo)
            
            # Aqui você integraria com serviço de geolocalização
            # Por exemplo: MaxMind, IPinfo, etc.
            # Por enquanto, retornamos dados mock
            geo_data = {
                "country": "BR",
                "city": "São Paulo",
                "latitude": -23.5505,
                "longitude": -46.6333
            }
            
            # Cache por 24 horas
            await self.redis_client.setex(cache_key, 86400, json.dumps(geo_data))
            
            return geo_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar geolocalização: {e}")
            return None
    
    async def _save_to_database(self, event: AuditEvent, db: Optional[AsyncSession] = None):
        """Salva evento no banco de dados"""
        if not db:
            return  # Precisa da sessão para salvar
        
        try:
            audit_log = AuditLog(
                event_type=event.event_type.value,
                severity=event.severity.value,
                user_id=event.user_id,
                session_id=event.session_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                endpoint=event.endpoint,
                method=event.method,
                status_code=event.status_code,
                description=event.description,
                data=json.dumps(event.data) if event.data else None,
                timestamp=event.timestamp,
                request_id=event.request_id
            )
            
            db.add(audit_log)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Erro ao salvar audit log: {e}")
            await db.rollback()
    
    async def _process_batch(self, db: Optional[AsyncSession] = None):
        """Processa batch de eventos acumulados"""
        if not self._batch_buffer or not db:
            return
        
        try:
            # Criar registros em lote
            audit_logs = []
            for event in self._batch_buffer:
                audit_log = AuditLog(
                    event_type=event.event_type.value,
                    severity=event.severity.value,
                    user_id=event.user_id,
                    session_id=event.session_id,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    endpoint=event.endpoint,
                    method=event.method,
                    status_code=event.status_code,
                    description=event.description,
                    data=json.dumps(event.data) if event.data else None,
                    timestamp=event.timestamp,
                    request_id=event.request_id
                )
                audit_logs.append(audit_log)
            
            # Inserção em lote
            db.add_all(audit_logs)
            await db.commit()
            
            # Limpar buffer
            self._batch_buffer.clear()
            
            logger.info(f"Processado batch de {len(audit_logs)} eventos de auditoria")
            
        except Exception as e:
            logger.error(f"Erro ao processar batch de auditoria: {e}")
            await db.rollback()
    
    async def _send_critical_alert(self, event: AuditEvent):
        """Envia alerta para eventos críticos"""
        # Implementar notificações:
        # - Slack webhook
        # - Email para admin
        # - SMS para emergências
        # - Push notification
        
        alert_data = {
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "user_id": event.user_id,
            "ip_address": event.ip_address,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "description": event.description
        }
        
        logger.critical(f"ALERTA CRÍTICO: {event.event_type.value}", extra=alert_data)
        
        # Aqui você implementaria as notificações reais
        # Por exemplo: envio para Slack, email, etc.
    
    async def search_events(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        event_types: Optional[List[AuditEventType]] = None,
        severity: Optional[AuditSeverity] = None,
        ip_address: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Busca eventos de auditoria com filtros
        """
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if event_types:
            event_type_values = [et.value for et in event_types]
            query = query.filter(AuditLog.event_type.in_(event_type_values))
        
        if severity:
            query = query.filter(AuditLog.severity == severity.value)
        
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
        
        results = await query.all()
        
        return [
            {
                "id": log.id,
                "event_type": log.event_type,
                "severity": log.severity,
                "user_id": log.user_id,
                "ip_address": log.ip_address,
                "endpoint": log.endpoint,
                "description": log.description,
                "timestamp": log.timestamp.isoformat(),
                "data": json.loads(log.data) if log.data else None
            }
            for log in results
        ]

# Instância global
audit_manager = AuditTrailManager()

# Decorator para auditoria automática de endpoints
def audit_endpoint(event_type: AuditEventType, severity: AuditSeverity = AuditSeverity.LOW):
    """Decorator para auditoria automática de endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or (args[0] if args else None)
            
            if request and hasattr(request, 'method'):
                # Extrair dados da requisição
                user_id = getattr(request.state, 'user_id', None)
                
                event = AuditEvent(
                    event_type=event_type,
                    severity=severity,
                    user_id=user_id,
                    ip_address=request.client.host if hasattr(request, 'client') else None,
                    user_agent=request.headers.get('user-agent'),
                    endpoint=str(request.url.path),
                    method=request.method,
                    description=f"Acesso ao endpoint {func.__name__}"
                )
                
                # Executar função
                try:
                    result = await func(*args, **kwargs)
                    event.status_code = 200
                    await audit_manager.log_event(event)
                    return result
                
                except Exception as e:
                    event.status_code = 500
                    event.severity = AuditSeverity.HIGH
                    event.description = f"Erro no endpoint {func.__name__}: {str(e)}"
                    await audit_manager.log_event(event)
                    raise
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Funções auxiliares para eventos específicos
async def log_user_action(
    action: AuditEventType,
    user_id: int,
    description: str,
    data: Optional[Dict] = None,
    request: Optional[Request] = None
):
    """Log para ações específicas de usuário"""
    event = AuditEvent(
        event_type=action,
        severity=AuditSeverity.LOW,
        user_id=user_id,
        description=description,
        data=data
    )
    
    if request:
        event.ip_address = request.client.host if hasattr(request, 'client') else None
        event.user_agent = request.headers.get('user-agent')
        event.endpoint = str(request.url.path)
        event.method = request.method
    
    await audit_manager.log_event(event)

async def log_security_event(
    event_type: AuditEventType,
    description: str,
    ip_address: Optional[str] = None,
    user_id: Optional[int] = None,
    data: Optional[Dict] = None
):
    """Log para eventos de segurança"""
    event = AuditEvent(
        event_type=event_type,
        severity=AuditSeverity.HIGH,
        user_id=user_id,
        ip_address=ip_address,
        description=description,
        data=data
    )
    
    await audit_manager.log_event(event, immediate=True) 