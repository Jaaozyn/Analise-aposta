"""
WebSocket Manager - Sistema de Atualizações em Tempo Real
Notificações automáticas para picks, odds, resultados e análises
"""

import json
import asyncio
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

from app.core.config import settings
from app.core.cache import redis_client

logger = logging.getLogger(__name__)

class UpdateType(Enum):
    """Tipos de atualizações em tempo real"""
    
    # Picks e Análises
    NEW_PICK = "new_pick"
    PICK_UPDATED = "pick_updated"
    PICK_RESULT = "pick_result"
    
    # Odds e Mercados
    ODDS_CHANGED = "odds_changed"
    NEW_ODDS = "new_odds"
    MARKET_CLOSED = "market_closed"
    
    # Partidas
    MATCH_STARTED = "match_started"
    MATCH_FINISHED = "match_finished"
    LIVE_SCORE = "live_score"
    
    # Usuário
    SUBSCRIPTION_UPDATED = "subscription_updated"
    BALANCE_CHANGED = "balance_changed"
    NOTIFICATION = "notification"
    
    # Sistema
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_ALERT = "system_alert"

@dataclass
class WebSocketMessage:
    """Estrutura padronizada de mensagem WebSocket"""
    
    type: UpdateType
    data: Dict[str, Any]
    timestamp: datetime = None
    user_id: Optional[int] = None
    channel: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "channel": self.channel
        }

class WebSocketConnection:
    """Representa uma conexão WebSocket ativa"""
    
    def __init__(self, websocket: WebSocket, user_id: Optional[int] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.channels: Set[str] = set()
        self.connected_at = datetime.now()
        self.last_ping = datetime.now()
        self.is_active = True
    
    async def send_message(self, message: WebSocketMessage):
        """Envia mensagem para o cliente"""
        try:
            await self.websocket.send_text(json.dumps(message.to_dict()))
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem WebSocket: {e}")
            self.is_active = False
            return False
    
    async def send_ping(self):
        """Envia ping para manter conexão viva"""
        try:
            await self.websocket.send_text(json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()}))
            self.last_ping = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar ping: {e}")
            self.is_active = False
            return False

class WebSocketManager:
    """Gerenciador central de conexões WebSocket"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> connection_ids
        self.channel_subscribers: Dict[str, Set[str]] = {}  # channel -> connection_ids
        self.redis_client = redis_client
        self.ping_interval = 30  # segundos
        self.cleanup_interval = 60  # segundos
        
        # Canais de notificação
        self.channels = {
            "picks_general": "Picks gerais",
            "picks_football": "Picks de futebol", 
            "picks_basketball": "Picks de basquete",
            "picks_esports": "Picks de esports",
            "odds_updates": "Atualizações de odds",
            "live_matches": "Partidas ao vivo",
            "user_notifications": "Notificações pessoais",
            "system_alerts": "Alertas do sistema"
        }
    
    def generate_connection_id(self, websocket: WebSocket) -> str:
        """Gera ID único para a conexão"""
        return f"ws_{id(websocket)}_{datetime.now().timestamp()}"
    
    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None) -> str:
        """Registra nova conexão WebSocket"""
        connection_id = self.generate_connection_id(websocket)
        connection = WebSocketConnection(websocket, user_id)
        
        # Registrar conexão
        self.connections[connection_id] = connection
        
        # Associar usuário à conexão
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        # Subscrever em canais padrão
        await self.subscribe_to_channel(connection_id, "system_alerts")
        if user_id:
            await self.subscribe_to_channel(connection_id, "user_notifications")
        
        logger.info(f"Nova conexão WebSocket: {connection_id} (user: {user_id})")
        
        # Enviar mensagem de boas-vindas
        welcome_message = WebSocketMessage(
            type=UpdateType.NOTIFICATION,
            data={
                "message": "Conectado ao QuantumBet Real-Time",
                "connection_id": connection_id,
                "available_channels": list(self.channels.keys())
            },
            user_id=user_id
        )
        
        await connection.send_message(welcome_message)
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Remove conexão WebSocket"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Remover de canais
        for channel in connection.channels.copy():
            await self.unsubscribe_from_channel(connection_id, channel)
        
        # Remover associação de usuário
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remover conexão
        del self.connections[connection_id]
        
        logger.info(f"Conexão WebSocket removida: {connection_id}")
    
    async def subscribe_to_channel(self, connection_id: str, channel: str):
        """Subscreve conexão a um canal"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.channels.add(channel)
        
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        self.channel_subscribers[channel].add(connection_id)
        
        # Notificar sucesso
        message = WebSocketMessage(
            type=UpdateType.NOTIFICATION,
            data={
                "message": f"Subscrito ao canal: {self.channels.get(channel, channel)}",
                "channel": channel
            },
            user_id=connection.user_id,
            channel=channel
        )
        
        await connection.send_message(message)
        
        logger.debug(f"Conexão {connection_id} subscrita ao canal {channel}")
        return True
    
    async def unsubscribe_from_channel(self, connection_id: str, channel: str):
        """Remove subscrição de canal"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.channels.discard(channel)
        
        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(connection_id)
            if not self.channel_subscribers[channel]:
                del self.channel_subscribers[channel]
        
        logger.debug(f"Conexão {connection_id} removida do canal {channel}")
        return True
    
    async def broadcast_to_channel(self, channel: str, message: WebSocketMessage):
        """Envia mensagem para todos os subscritores de um canal"""
        if channel not in self.channel_subscribers:
            return 0
        
        sent_count = 0
        dead_connections = []
        
        for connection_id in self.channel_subscribers[channel].copy():
            if connection_id not in self.connections:
                dead_connections.append(connection_id)
                continue
            
            connection = self.connections[connection_id]
            message.channel = channel
            
            if await connection.send_message(message):
                sent_count += 1
            else:
                dead_connections.append(connection_id)
        
        # Limpar conexões mortas
        for dead_id in dead_connections:
            await self.disconnect(dead_id)
        
        logger.debug(f"Mensagem enviada para {sent_count} conexões no canal {channel}")
        return sent_count
    
    async def send_to_user(self, user_id: int, message: WebSocketMessage):
        """Envia mensagem para todas as conexões de um usuário"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        dead_connections = []
        
        for connection_id in self.user_connections[user_id].copy():
            if connection_id not in self.connections:
                dead_connections.append(connection_id)
                continue
            
            connection = self.connections[connection_id]
            message.user_id = user_id
            
            if await connection.send_message(message):
                sent_count += 1
            else:
                dead_connections.append(connection_id)
        
        # Limpar conexões mortas
        for dead_id in dead_connections:
            await self.disconnect(dead_id)
        
        logger.debug(f"Mensagem enviada para {sent_count} conexões do usuário {user_id}")
        return sent_count
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Envia mensagem para todas as conexões ativas"""
        sent_count = 0
        dead_connections = []
        
        for connection_id, connection in self.connections.items():
            if await connection.send_message(message):
                sent_count += 1
            else:
                dead_connections.append(connection_id)
        
        # Limpar conexões mortas
        for dead_id in dead_connections:
            await self.disconnect(dead_id)
        
        logger.info(f"Broadcast enviado para {sent_count} conexões")
        return sent_count
    
    async def handle_client_message(self, connection_id: str, message_data: dict):
        """Processa mensagem recebida do cliente"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        message_type = message_data.get("type")
        
        if message_type == "ping":
            # Responder ping
            pong_message = WebSocketMessage(
                type=UpdateType.NOTIFICATION,
                data={"type": "pong", "timestamp": datetime.now().isoformat()},
                user_id=connection.user_id
            )
            await connection.send_message(pong_message)
        
        elif message_type == "subscribe":
            # Subscrever a canal
            channel = message_data.get("channel")
            if channel and channel in self.channels:
                await self.subscribe_to_channel(connection_id, channel)
        
        elif message_type == "unsubscribe":
            # Cancelar subscrição
            channel = message_data.get("channel")
            if channel:
                await self.unsubscribe_from_channel(connection_id, channel)
        
        elif message_type == "get_channels":
            # Listar canais disponíveis
            channels_message = WebSocketMessage(
                type=UpdateType.NOTIFICATION,
                data={
                    "available_channels": self.channels,
                    "subscribed_channels": list(connection.channels)
                },
                user_id=connection.user_id
            )
            await connection.send_message(channels_message)
    
    async def start_background_tasks(self):
        """Inicia tarefas em background"""
        asyncio.create_task(self._ping_connections())
        asyncio.create_task(self._cleanup_connections())
        asyncio.create_task(self._listen_redis_events())
    
    async def _ping_connections(self):
        """Envia ping periódico para manter conexões vivas"""
        while True:
            try:
                await asyncio.sleep(self.ping_interval)
                
                dead_connections = []
                for connection_id, connection in self.connections.items():
                    if not await connection.send_ping():
                        dead_connections.append(connection_id)
                
                # Limpar conexões mortas
                for dead_id in dead_connections:
                    await self.disconnect(dead_id)
                
            except Exception as e:
                logger.error(f"Erro no ping de conexões: {e}")
    
    async def _cleanup_connections(self):
        """Remove conexões inativas periodicamente"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                now = datetime.now()
                dead_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Conexão sem ping há muito tempo
                    if (now - connection.last_ping).seconds > (self.ping_interval * 3):
                        dead_connections.append(connection_id)
                    # Conexão marcada como inativa
                    elif not connection.is_active:
                        dead_connections.append(connection_id)
                
                # Limpar conexões mortas
                for dead_id in dead_connections:
                    await self.disconnect(dead_id)
                
                if dead_connections:
                    logger.info(f"Limpeza: {len(dead_connections)} conexões removidas")
                
            except Exception as e:
                logger.error(f"Erro na limpeza de conexões: {e}")
    
    async def _listen_redis_events(self):
        """Escuta eventos do Redis para distribuir via WebSocket"""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("quantumbet:websocket:*")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        channel = message["channel"].decode()
                        data = json.loads(message["data"])
                        
                        # Extrair canal WebSocket do canal Redis
                        ws_channel = channel.replace("quantumbet:websocket:", "")
                        
                        ws_message = WebSocketMessage(
                            type=UpdateType(data["type"]),
                            data=data["data"],
                            user_id=data.get("user_id")
                        )
                        
                        await self.broadcast_to_channel(ws_channel, ws_message)
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar evento Redis: {e}")
        
        except Exception as e:
            logger.error(f"Erro na escuta de eventos Redis: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas das conexões WebSocket"""
        return {
            "total_connections": len(self.connections),
            "authenticated_users": len(self.user_connections),
            "active_channels": len(self.channel_subscribers),
            "channels": {
                channel: len(subscribers) 
                for channel, subscribers in self.channel_subscribers.items()
            },
            "connection_details": [
                {
                    "connection_id": conn_id,
                    "user_id": conn.user_id,
                    "channels": list(conn.channels),
                    "connected_at": conn.connected_at.isoformat(),
                    "last_ping": conn.last_ping.isoformat(),
                    "is_active": conn.is_active
                }
                for conn_id, conn in self.connections.items()
            ]
        }

# Instância global
websocket_manager = WebSocketManager()

# Funções auxiliares para eventos específicos
async def notify_new_pick(pick_data: dict, sport: str):
    """Notifica sobre novo pick"""
    message = WebSocketMessage(
        type=UpdateType.NEW_PICK,
        data={
            "pick": pick_data,
            "sport": sport,
            "message": f"Novo pick de {sport} disponível!"
        }
    )
    
    # Enviar para canal geral e específico do esporte
    await websocket_manager.broadcast_to_channel("picks_general", message)
    await websocket_manager.broadcast_to_channel(f"picks_{sport}", message)

async def notify_odds_change(match_id: int, old_odds: dict, new_odds: dict):
    """Notifica sobre mudança de odds"""
    message = WebSocketMessage(
        type=UpdateType.ODDS_CHANGED,
        data={
            "match_id": match_id,
            "old_odds": old_odds,
            "new_odds": new_odds,
            "change_percentage": ((new_odds.get("home", 0) - old_odds.get("home", 0)) / old_odds.get("home", 1)) * 100
        }
    )
    
    await websocket_manager.broadcast_to_channel("odds_updates", message)

async def notify_user_event(user_id: int, event_type: str, data: dict):
    """Notifica usuário específico"""
    message = WebSocketMessage(
        type=UpdateType.NOTIFICATION,
        data={
            "event": event_type,
            **data
        },
        user_id=user_id
    )
    
    await websocket_manager.send_to_user(user_id, message) 