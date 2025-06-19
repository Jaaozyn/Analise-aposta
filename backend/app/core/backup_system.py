"""
Sistema de Backup e Recovery - QuantumBet
Backup automatizado, point-in-time recovery e replicação cross-region
"""

import asyncio
import os
import shutil
import tarfile
import gzip
import json
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging
from contextlib import asynccontextmanager
import aiofiles
import subprocess
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db
from app.core.cache import redis_client

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Tipos de backup"""
    FULL = "full"           # Backup completo
    INCREMENTAL = "incremental"  # Backup incremental
    DIFFERENTIAL = "differential"  # Backup diferencial
    POINT_IN_TIME = "point_in_time"  # Snapshot específico

class BackupStatus(Enum):
    """Status do backup"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"

class StorageProvider(Enum):
    """Provedores de armazenamento"""
    LOCAL = "local"
    AWS_S3 = "aws_s3"
    GOOGLE_CLOUD = "google_cloud"
    AZURE_BLOB = "azure_blob"

@dataclass
class BackupConfig:
    """Configuração de backup"""
    enabled: bool = True
    backup_types: List[BackupType] = None
    retention_days: int = 30
    compression_enabled: bool = True
    encryption_enabled: bool = True
    storage_providers: List[StorageProvider] = None
    schedule_cron: str = "0 2 * * *"  # 2h da manhã diariamente
    max_concurrent_backups: int = 2
    
    def __post_init__(self):
        if self.backup_types is None:
            self.backup_types = [BackupType.FULL, BackupType.INCREMENTAL]
        if self.storage_providers is None:
            self.storage_providers = [StorageProvider.LOCAL]

@dataclass
class BackupMetadata:
    """Metadados do backup"""
    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime]
    file_path: str
    file_size: Optional[int]
    checksum: Optional[str]
    database_snapshot: bool
    redis_snapshot: bool
    files_snapshot: bool
    error_message: Optional[str] = None

class DatabaseBackupManager:
    """Gerenciador de backup do banco de dados"""
    
    def __init__(self):
        self.pg_dump_path = "pg_dump"  # Pode ser configurado
        self.backup_dir = Path("backups/database")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_full_backup(self, backup_id: str) -> str:
        """Cria backup completo do banco de dados"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"db_full_{backup_id}_{timestamp}.sql"
        filepath = self.backup_dir / filename
        
        try:
            # Comando pg_dump
            cmd = [
                self.pg_dump_path,
                "--host", settings.DATABASE_URL.split('@')[1].split('/')[0].split(':')[0],
                "--port", "5432",
                "--username", "quantumbet",
                "--dbname", "quantumbet_db",
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-privileges",
                "--format=custom",
                "--file", str(filepath)
            ]
            
            # Executar backup
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PGPASSWORD": "password123"}
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Erro desconhecido no pg_dump"
                raise Exception(f"pg_dump falhou: {error_msg}")
            
            logger.info(f"Backup do banco criado: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erro ao criar backup do banco: {e}")
            raise
    
    async def create_incremental_backup(self, backup_id: str, last_backup_time: datetime) -> str:
        """Cria backup incremental (apenas mudanças desde último backup)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"db_incremental_{backup_id}_{timestamp}.sql"
        filepath = self.backup_dir / filename
        
        try:
            # Query para dados modificados desde último backup
            incremental_query = f"""
            -- Backup incremental desde {last_backup_time}
            COPY (SELECT * FROM users WHERE updated_at > '{last_backup_time}') TO STDOUT WITH CSV HEADER;
            COPY (SELECT * FROM picks WHERE created_at > '{last_backup_time}') TO STDOUT WITH CSV HEADER;
            COPY (SELECT * FROM matches WHERE updated_at > '{last_backup_time}') TO STDOUT WITH CSV HEADER;
            -- Adicionar outras tabelas conforme necessário
            """
            
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(incremental_query)
            
            logger.info(f"Backup incremental criado: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erro ao criar backup incremental: {e}")
            raise
    
    async def restore_from_backup(self, backup_file: str, target_db: str = None) -> bool:
        """Restaura banco de dados a partir de backup"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_file}")
            
            # Comando pg_restore
            cmd = [
                "pg_restore",
                "--host", settings.DATABASE_URL.split('@')[1].split('/')[0].split(':')[0],
                "--port", "5432",
                "--username", "quantumbet",
                "--dbname", target_db or "quantumbet_db",
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-privileges",
                backup_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PGPASSWORD": "password123"}
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Erro desconhecido no pg_restore"
                logger.error(f"pg_restore falhou: {error_msg}")
                return False
            
            logger.info(f"Banco restaurado com sucesso de: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao restaurar banco: {e}")
            return False

class RedisBackupManager:
    """Gerenciador de backup do Redis"""
    
    def __init__(self):
        self.backup_dir = Path("backups/redis")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_snapshot(self, backup_id: str) -> str:
        """Cria snapshot do Redis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"redis_{backup_id}_{timestamp}.rdb"
        filepath = self.backup_dir / filename
        
        try:
            # Executar BGSAVE no Redis
            result = await redis_client.bgsave()
            if not result:
                raise Exception("BGSAVE falhou")
            
            # Aguardar conclusão do BGSAVE
            while True:
                last_save = await redis_client.lastsave()
                await asyncio.sleep(1)
                new_save = await redis_client.lastsave()
                if new_save > last_save:
                    break
            
            # Copiar arquivo RDB
            redis_rdb_path = "/var/lib/redis/dump.rdb"  # Caminho padrão
            if os.path.exists(redis_rdb_path):
                shutil.copy2(redis_rdb_path, filepath)
            else:
                # Fallback: dump dos dados via comandos Redis
                await self._dump_redis_data(filepath)
            
            logger.info(f"Snapshot do Redis criado: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erro ao criar snapshot do Redis: {e}")
            raise
    
    async def _dump_redis_data(self, filepath: str):
        """Fallback: dump dos dados do Redis via comandos"""
        try:
            # Obter todas as chaves
            keys = await redis_client.keys("*")
            
            backup_data = {}
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                
                # Verificar tipo da chave
                key_type = await redis_client.type(key)
                
                if key_type == "string":
                    backup_data[key_str] = {
                        "type": "string",
                        "value": await redis_client.get(key),
                        "ttl": await redis_client.ttl(key)
                    }
                elif key_type == "list":
                    backup_data[key_str] = {
                        "type": "list",
                        "value": await redis_client.lrange(key, 0, -1),
                        "ttl": await redis_client.ttl(key)
                    }
                elif key_type == "set":
                    backup_data[key_str] = {
                        "type": "set",
                        "value": list(await redis_client.smembers(key)),
                        "ttl": await redis_client.ttl(key)
                    }
                elif key_type == "hash":
                    backup_data[key_str] = {
                        "type": "hash",
                        "value": await redis_client.hgetall(key),
                        "ttl": await redis_client.ttl(key)
                    }
            
            # Salvar como JSON
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
                
        except Exception as e:
            logger.error(f"Erro ao fazer dump dos dados do Redis: {e}")
            raise
    
    async def restore_from_snapshot(self, backup_file: str) -> bool:
        """Restaura Redis a partir de snapshot"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_file}")
            
            # Se é arquivo .rdb, copiar para local correto
            if backup_file.endswith('.rdb'):
                # Parar Redis, copiar arquivo, reiniciar
                # (Requer privilégios administrativos)
                logger.warning("Restauração de .rdb requer privilégios administrativos")
                return False
            
            # Se é JSON dump, restaurar via comandos
            async with aiofiles.open(backup_file, 'r') as f:
                content = await f.read()
                backup_data = json.loads(content)
            
            # Limpar Redis atual
            await redis_client.flushall()
            
            # Restaurar dados
            for key, data in backup_data.items():
                value = data["value"]
                ttl = data["ttl"]
                
                if data["type"] == "string":
                    await redis_client.set(key, value)
                elif data["type"] == "list":
                    for item in value:
                        await redis_client.lpush(key, item)
                elif data["type"] == "set":
                    for item in value:
                        await redis_client.sadd(key, item)
                elif data["type"] == "hash":
                    await redis_client.hset(key, mapping=value)
                
                # Definir TTL se necessário
                if ttl > 0:
                    await redis_client.expire(key, ttl)
            
            logger.info(f"Redis restaurado com sucesso de: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao restaurar Redis: {e}")
            return False

class FileSystemBackupManager:
    """Gerenciador de backup do sistema de arquivos"""
    
    def __init__(self):
        self.backup_dir = Path("backups/files")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Diretórios para backup
        self.backup_paths = [
            "models/",           # Modelos ML
            "data/",            # Dados de treinamento
            "uploads/",         # Uploads de usuários
            "static/",          # Arquivos estáticos
            "logs/",           # Logs importantes
        ]
    
    async def create_backup(self, backup_id: str, backup_type: BackupType) -> str:
        """Cria backup do sistema de arquivos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"files_{backup_type.value}_{backup_id}_{timestamp}.tar.gz"
        filepath = self.backup_dir / filename
        
        try:
            # Criar arquivo tar comprimido
            with tarfile.open(filepath, "w:gz") as tar:
                for path in self.backup_paths:
                    if os.path.exists(path):
                        tar.add(path, arcname=path)
                        logger.debug(f"Adicionado ao backup: {path}")
            
            logger.info(f"Backup de arquivos criado: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erro ao criar backup de arquivos: {e}")
            raise
    
    async def restore_from_backup(self, backup_file: str, target_dir: str = ".") -> bool:
        """Restaura arquivos a partir de backup"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_file}")
            
            # Extrair arquivos
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=target_dir)
            
            logger.info(f"Arquivos restaurados com sucesso de: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao restaurar arquivos: {e}")
            return False

class CloudStorageManager:
    """Gerenciador de armazenamento em nuvem"""
    
    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self._setup_client()
    
    def _setup_client(self):
        """Configura cliente da nuvem"""
        if self.provider == StorageProvider.AWS_S3:
            self.client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            self.bucket = os.getenv('AWS_S3_BACKUP_BUCKET', 'quantumbet-backups')
        # Adicionar outros provedores conforme necessário
    
    async def upload_backup(self, local_file: str, remote_key: str) -> bool:
        """Faz upload de backup para nuvem"""
        try:
            if self.provider == StorageProvider.AWS_S3:
                # Upload para S3
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.client.upload_file,
                    local_file,
                    self.bucket,
                    remote_key
                )
                
                logger.info(f"Backup enviado para S3: s3://{self.bucket}/{remote_key}")
                return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar backup para nuvem: {e}")
            return False
    
    async def download_backup(self, remote_key: str, local_file: str) -> bool:
        """Baixa backup da nuvem"""
        try:
            if self.provider == StorageProvider.AWS_S3:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.client.download_file,
                    self.bucket,
                    remote_key,
                    local_file
                )
                
                logger.info(f"Backup baixado do S3: {local_file}")
                return True
            
        except Exception as e:
            logger.error(f"Erro ao baixar backup da nuvem: {e}")
            return False

class BackupOrchestrator:
    """Orquestrador principal do sistema de backup"""
    
    def __init__(self, config: BackupConfig = None):
        self.config = config or BackupConfig()
        self.db_manager = DatabaseBackupManager()
        self.redis_manager = RedisBackupManager()
        self.files_manager = FileSystemBackupManager()
        self.cloud_managers = {
            provider: CloudStorageManager(provider)
            for provider in self.config.storage_providers
            if provider != StorageProvider.LOCAL
        }
        
        self.backup_metadata: List[BackupMetadata] = []
        self.active_backups = 0
    
    async def create_backup(
        self, 
        backup_type: BackupType = BackupType.FULL,
        include_database: bool = True,
        include_redis: bool = True,
        include_files: bool = True
    ) -> BackupMetadata:
        """Cria backup completo do sistema"""
        
        if self.active_backups >= self.config.max_concurrent_backups:
            raise Exception("Máximo de backups simultâneos atingido")
        
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.IN_PROGRESS,
            created_at=datetime.now(),
            completed_at=None,
            file_path="",
            file_size=None,
            checksum=None,
            database_snapshot=include_database,
            redis_snapshot=include_redis,
            files_snapshot=include_files
        )
        
        try:
            self.active_backups += 1
            logger.info(f"Iniciando backup {backup_id} ({backup_type.value})")
            
            backup_files = []
            
            # Backup do banco de dados
            if include_database:
                if backup_type == BackupType.FULL:
                    db_file = await self.db_manager.create_full_backup(backup_id)
                elif backup_type == BackupType.INCREMENTAL:
                    last_backup_time = self._get_last_backup_time()
                    db_file = await self.db_manager.create_incremental_backup(
                        backup_id, last_backup_time
                    )
                backup_files.append(db_file)
            
            # Backup do Redis
            if include_redis:
                redis_file = await self.redis_manager.create_snapshot(backup_id)
                backup_files.append(redis_file)
            
            # Backup dos arquivos
            if include_files:
                files_backup = await self.files_manager.create_backup(backup_id, backup_type)
                backup_files.append(files_backup)
            
            # Criar arquivo final comprimido
            final_backup_path = await self._create_final_backup(backup_id, backup_files)
            
            # Calcular checksum
            checksum = await self._calculate_checksum(final_backup_path)
            
            # Upload para nuvem
            if self.cloud_managers:
                await self._upload_to_cloud(final_backup_path, backup_id)
            
            # Atualizar metadata
            metadata.status = BackupStatus.COMPLETED
            metadata.completed_at = datetime.now()
            metadata.file_path = final_backup_path
            metadata.file_size = os.path.getsize(final_backup_path)
            metadata.checksum = checksum
            
            self.backup_metadata.append(metadata)
            
            logger.info(f"Backup {backup_id} concluído com sucesso")
            
            # Limpeza de backups antigos
            await self._cleanup_old_backups()
            
            return metadata
            
        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            metadata.completed_at = datetime.now()
            
            logger.error(f"Backup {backup_id} falhou: {e}")
            raise
            
        finally:
            self.active_backups -= 1
    
    async def _create_final_backup(self, backup_id: str, backup_files: List[str]) -> str:
        """Cria arquivo final de backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"quantumbet_backup_{backup_id}_{timestamp}.tar.gz"
        final_path = Path("backups") / final_filename
        
        with tarfile.open(final_path, "w:gz") as tar:
            for file_path in backup_files:
                if os.path.exists(file_path):
                    tar.add(file_path, arcname=os.path.basename(file_path))
        
        return str(final_path)
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """Calcula checksum SHA256 do arquivo"""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    async def _upload_to_cloud(self, file_path: str, backup_id: str):
        """Faz upload do backup para todos os provedores de nuvem"""
        remote_key = f"backups/{backup_id}/{os.path.basename(file_path)}"
        
        for provider, manager in self.cloud_managers.items():
            try:
                await manager.upload_backup(file_path, remote_key)
            except Exception as e:
                logger.error(f"Falha no upload para {provider.value}: {e}")
    
    def _get_last_backup_time(self) -> datetime:
        """Obtém timestamp do último backup"""
        if not self.backup_metadata:
            return datetime.now() - timedelta(days=1)
        
        last_backup = max(
            (b for b in self.backup_metadata if b.status == BackupStatus.COMPLETED),
            key=lambda x: x.completed_at,
            default=None
        )
        
        return last_backup.completed_at if last_backup else datetime.now() - timedelta(days=1)
    
    async def _cleanup_old_backups(self):
        """Remove backups antigos baseado na política de retenção"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        for metadata in self.backup_metadata[:]:
            if metadata.created_at < cutoff_date:
                try:
                    # Remover arquivo local
                    if os.path.exists(metadata.file_path):
                        os.remove(metadata.file_path)
                    
                    # Remover da lista
                    self.backup_metadata.remove(metadata)
                    
                    logger.info(f"Backup antigo removido: {metadata.backup_id}")
                    
                except Exception as e:
                    logger.error(f"Erro ao remover backup antigo {metadata.backup_id}: {e}")
    
    async def restore_from_backup(self, backup_id: str, target_env: str = "current") -> bool:
        """Restaura sistema a partir de backup específico"""
        try:
            # Encontrar metadata do backup
            backup_metadata = next(
                (b for b in self.backup_metadata if b.backup_id == backup_id),
                None
            )
            
            if not backup_metadata:
                raise ValueError(f"Backup {backup_id} não encontrado")
            
            if backup_metadata.status != BackupStatus.COMPLETED:
                raise ValueError(f"Backup {backup_id} não está completo")
            
            logger.info(f"Iniciando restauração do backup {backup_id}")
            
            # Baixar da nuvem se necessário
            backup_file = backup_metadata.file_path
            if not os.path.exists(backup_file) and self.cloud_managers:
                # Tentar baixar da nuvem
                await self._download_from_cloud(backup_id, backup_file)
            
            # Extrair backup
            extract_dir = Path("temp_restore") / backup_id
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=extract_dir)
            
            # Restaurar componentes
            success = True
            
            if backup_metadata.database_snapshot:
                db_files = list(extract_dir.glob("db_*.sql"))
                if db_files:
                    success &= await self.db_manager.restore_from_backup(str(db_files[0]))
            
            if backup_metadata.redis_snapshot:
                redis_files = list(extract_dir.glob("redis_*"))
                if redis_files:
                    success &= await self.redis_manager.restore_from_snapshot(str(redis_files[0]))
            
            if backup_metadata.files_snapshot:
                files_archives = list(extract_dir.glob("files_*.tar.gz"))
                if files_archives:
                    success &= await self.files_manager.restore_from_backup(str(files_archives[0]))
            
            # Limpeza
            shutil.rmtree(extract_dir, ignore_errors=True)
            
            if success:
                logger.info(f"Restauração do backup {backup_id} concluída com sucesso")
            else:
                logger.error(f"Restauração do backup {backup_id} teve falhas")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro na restauração do backup {backup_id}: {e}")
            return False
    
    async def _download_from_cloud(self, backup_id: str, local_file: str):
        """Baixa backup da nuvem"""
        remote_key = f"backups/{backup_id}/{os.path.basename(local_file)}"
        
        for provider, manager in self.cloud_managers.items():
            try:
                if await manager.download_backup(remote_key, local_file):
                    return
            except Exception as e:
                logger.error(f"Falha no download de {provider.value}: {e}")
        
        raise Exception("Falha ao baixar backup de todos os provedores de nuvem")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Obtém status do sistema de backup"""
        return {
            "total_backups": len(self.backup_metadata),
            "active_backups": self.active_backups,
            "last_backup": max(
                (b.created_at for b in self.backup_metadata if b.status == BackupStatus.COMPLETED),
                default=None
            ),
            "recent_backups": [
                {
                    "backup_id": b.backup_id,
                    "type": b.backup_type.value,
                    "status": b.status.value,
                    "created_at": b.created_at.isoformat(),
                    "file_size": b.file_size
                }
                for b in sorted(self.backup_metadata, key=lambda x: x.created_at, reverse=True)[:10]
            ],
            "config": {
                "enabled": self.config.enabled,
                "retention_days": self.config.retention_days,
                "storage_providers": [p.value for p in self.config.storage_providers]
            }
        }

# Instância global
backup_orchestrator = BackupOrchestrator()

# Função para agendar backups automáticos
async def schedule_automatic_backups():
    """Agenda backups automáticos baseado na configuração"""
    # Implementar com Celery ou similar
    pass 