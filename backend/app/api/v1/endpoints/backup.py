"""
Backup Endpoints - Gerenciamento de Backup e Recovery
Endpoints para criar, restaurar e monitorar backups do sistema
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.core.backup_system import (
    backup_orchestrator, BackupType, BackupStatus, BackupConfig
)
from app.core.auth import get_current_admin_user
from app.models.user import User
from app.core.rate_limiter import limiter, RateLimits
from app.core.audit_trail import log_security_event, AuditEventType

router = APIRouter()

# Schemas
class BackupRequest(BaseModel):
    backup_type: BackupType = BackupType.FULL
    include_database: bool = True
    include_redis: bool = True
    include_files: bool = True
    description: Optional[str] = None

class RestoreRequest(BaseModel):
    backup_id: str
    target_environment: str = "current"
    confirm: bool = Field(..., description="Confirmação obrigatória para restauração")

class BackupResponse(BaseModel):
    backup_id: str
    backup_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    file_size: Optional[int]
    checksum: Optional[str]
    error_message: Optional[str]

class BackupStatusResponse(BaseModel):
    total_backups: int
    active_backups: int
    last_backup: Optional[datetime]
    recent_backups: List[Dict[str, Any]]
    config: Dict[str, Any]

@router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    🔄 Criar novo backup do sistema
    Apenas administradores podem criar backups
    """
    try:
        # Log da ação
        await log_security_event(
            AuditEventType.ADMIN_ACTION,
            f"Backup iniciado por {current_user.email}",
            user_id=current_user.id,
            data={
                "backup_type": request.backup_type.value,
                "include_database": request.include_database,
                "include_redis": request.include_redis,
                "include_files": request.include_files
            }
        )
        
        # Criar backup em background
        def create_backup_task():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                metadata = loop.run_until_complete(
                    backup_orchestrator.create_backup(
                        backup_type=request.backup_type,
                        include_database=request.include_database,
                        include_redis=request.include_redis,
                        include_files=request.include_files
                    )
                )
                return metadata
            finally:
                loop.close()
        
        # Executar em background
        background_tasks.add_task(create_backup_task)
        
        # Retornar resposta imediata
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return BackupResponse(
            backup_id=backup_id,
            backup_type=request.backup_type.value,
            status=BackupStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            completed_at=None,
            file_size=None,
            checksum=None,
            error_message=None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar backup: {str(e)}"
        )

@router.get("/status", response_model=BackupStatusResponse)
async def get_backup_status(
    current_user: User = Depends(get_current_admin_user)
):
    """
    📊 Obter status do sistema de backup
    """
    try:
        status_data = backup_orchestrator.get_backup_status()
        
        return BackupStatusResponse(
            total_backups=status_data["total_backups"],
            active_backups=status_data["active_backups"],
            last_backup=status_data["last_backup"],
            recent_backups=status_data["recent_backups"],
            config=status_data["config"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter status do backup: {str(e)}"
        )

@router.get("/list", response_model=List[BackupResponse])
async def list_backups(
    limit: int = 50,
    status_filter: Optional[BackupStatus] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """
    📋 Listar backups disponíveis
    """
    try:
        backups = backup_orchestrator.backup_metadata
        
        # Filtrar por status se especificado
        if status_filter:
            backups = [b for b in backups if b.status == status_filter]
        
        # Ordenar por data de criação (mais recente primeiro)
        backups = sorted(backups, key=lambda x: x.created_at, reverse=True)
        
        # Limitar resultados
        backups = backups[:limit]
        
        return [
            BackupResponse(
                backup_id=backup.backup_id,
                backup_type=backup.backup_type.value,
                status=backup.status.value,
                created_at=backup.created_at,
                completed_at=backup.completed_at,
                file_size=backup.file_size,
                checksum=backup.checksum,
                error_message=backup.error_message
            )
            for backup in backups
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar backups: {str(e)}"
        )

@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup_details(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """
    🔍 Obter detalhes de um backup específico
    """
    try:
        backup = next(
            (b for b in backup_orchestrator.backup_metadata if b.backup_id == backup_id),
            None
        )
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup não encontrado"
            )
        
        return BackupResponse(
            backup_id=backup.backup_id,
            backup_type=backup.backup_type.value,
            status=backup.status.value,
            created_at=backup.created_at,
            completed_at=backup.completed_at,
            file_size=backup.file_size,
            checksum=backup.checksum,
            error_message=backup.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter detalhes do backup: {str(e)}"
        )

@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    🔄 Restaurar sistema a partir de backup
    ⚠️ OPERAÇÃO CRÍTICA - Requer confirmação explícita
    """
    # Verificar confirmação
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmação obrigatória para restauração. Defina 'confirm: true'"
        )
    
    try:
        # Verificar se backup existe
        backup = next(
            (b for b in backup_orchestrator.backup_metadata if b.backup_id == request.backup_id),
            None
        )
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup não encontrado"
            )
        
        if backup.status != BackupStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Backup não está completo e não pode ser restaurado"
            )
        
        # Log crítico da ação
        await log_security_event(
            AuditEventType.ADMIN_ACTION,
            f"RESTAURAÇÃO INICIADA por {current_user.email} - Backup: {request.backup_id}",
            user_id=current_user.id,
            data={
                "backup_id": request.backup_id,
                "target_environment": request.target_environment,
                "backup_created_at": backup.created_at.isoformat()
            }
        )
        
        # Executar restauração em background
        def restore_task():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    backup_orchestrator.restore_from_backup(
                        request.backup_id,
                        request.target_environment
                    )
                )
                
                # Log do resultado
                loop.run_until_complete(
                    log_security_event(
                        AuditEventType.ADMIN_ACTION,
                        f"RESTAURAÇÃO {'CONCLUÍDA' if success else 'FALHADA'} - Backup: {request.backup_id}",
                        user_id=current_user.id,
                        data={"success": success}
                    )
                )
                
                return success
            finally:
                loop.close()
        
        background_tasks.add_task(restore_task)
        
        return {
            "message": f"Restauração do backup {request.backup_id} iniciada",
            "backup_id": request.backup_id,
            "target_environment": request.target_environment,
            "initiated_by": current_user.email,
            "initiated_at": datetime.now().isoformat(),
            "warning": "⚠️ Processo em execução. Monitore os logs para acompanhar o progresso."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar restauração: {str(e)}"
        )

@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """
    🗑️ Deletar backup específico
    """
    try:
        # Verificar se backup existe
        backup = next(
            (b for b in backup_orchestrator.backup_metadata if b.backup_id == backup_id),
            None
        )
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup não encontrado"
            )
        
        # Remover arquivo se existir
        import os
        if os.path.exists(backup.file_path):
            os.remove(backup.file_path)
        
        # Remover da lista
        backup_orchestrator.backup_metadata.remove(backup)
        
        # Log da ação
        await log_security_event(
            AuditEventType.ADMIN_ACTION,
            f"Backup deletado por {current_user.email}: {backup_id}",
            user_id=current_user.id,
            data={"backup_id": backup_id}
        )
        
        return {
            "message": f"Backup {backup_id} deletado com sucesso",
            "deleted_by": current_user.email,
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar backup: {str(e)}"
        )

@router.post("/schedule")
async def configure_backup_schedule(
    schedule_config: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user)
):
    """
    ⏰ Configurar agendamento automático de backups
    """
    try:
        # Validar configuração
        valid_keys = [
            "enabled", "backup_types", "retention_days", 
            "schedule_cron", "include_database", "include_redis", "include_files"
        ]
        
        for key in schedule_config:
            if key not in valid_keys:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Configuração inválida: {key}"
                )
        
        # Atualizar configuração (em produção, salvar no banco de dados)
        backup_orchestrator.config.enabled = schedule_config.get("enabled", True)
        backup_orchestrator.config.retention_days = schedule_config.get("retention_days", 30)
        backup_orchestrator.config.schedule_cron = schedule_config.get("schedule_cron", "0 2 * * *")
        
        # Log da ação
        await log_security_event(
            AuditEventType.ADMIN_ACTION,
            f"Configuração de backup atualizada por {current_user.email}",
            user_id=current_user.id,
            data=schedule_config
        )
        
        return {
            "message": "Configuração de agendamento atualizada",
            "config": schedule_config,
            "updated_by": current_user.email,
            "updated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao configurar agendamento: {str(e)}"
        )

@router.get("/verify/{backup_id}")
async def verify_backup_integrity(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """
    ✅ Verificar integridade de um backup
    """
    try:
        backup = next(
            (b for b in backup_orchestrator.backup_metadata if b.backup_id == backup_id),
            None
        )
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup não encontrado"
            )
        
        # Verificar se arquivo existe
        import os
        file_exists = os.path.exists(backup.file_path)
        
        # Verificar checksum se arquivo existe
        checksum_valid = False
        current_checksum = None
        
        if file_exists and backup.checksum:
            # Calcular checksum atual
            import hashlib
            hash_sha256 = hashlib.sha256()
            with open(backup.file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            current_checksum = hash_sha256.hexdigest()
            checksum_valid = current_checksum == backup.checksum
        
        # Verificar tamanho do arquivo
        file_size_match = False
        current_file_size = None
        
        if file_exists:
            current_file_size = os.path.getsize(backup.file_path)
            file_size_match = current_file_size == backup.file_size
        
        integrity_status = {
            "backup_id": backup_id,
            "file_exists": file_exists,
            "checksum_valid": checksum_valid,
            "file_size_match": file_size_match,
            "original_checksum": backup.checksum,
            "current_checksum": current_checksum,
            "original_file_size": backup.file_size,
            "current_file_size": current_file_size,
            "overall_status": "valid" if (file_exists and checksum_valid and file_size_match) else "invalid",
            "verified_at": datetime.now().isoformat(),
            "verified_by": current_user.email
        }
        
        return integrity_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar integridade: {str(e)}"
        ) 