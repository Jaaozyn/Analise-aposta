"""
WebSocket Endpoints - Conexões em Tempo Real
Endpoints para comunicação WebSocket com clientes
"""

import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Optional
import logging

from app.core.websocket_manager import websocket_manager, WebSocketMessage, UpdateType
from app.api.dependencies import get_current_user_websocket
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket para usuários anônimos
    """
    await websocket.accept()
    connection_id = await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Aguardar mensagem do cliente
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                await websocket_manager.handle_client_message(connection_id, message_data)
            except json.JSONDecodeError:
                # Mensagem inválida
                error_message = WebSocketMessage(
                    type=UpdateType.NOTIFICATION,
                    data={"error": "Formato de mensagem inválido"}
                )
                await websocket_manager.connections[connection_id].send_message(error_message)
    
    except WebSocketDisconnect:
        await websocket_manager.disconnect(connection_id)

@router.websocket("/ws/{user_id}")
async def websocket_authenticated_endpoint(
    websocket: WebSocket, 
    user_id: int,
    token: Optional[str] = None
):
    """
    Endpoint WebSocket para usuários autenticados
    """
    await websocket.accept()
    
    # Validar token se fornecido
    authenticated_user = None
    if token:
        try:
            # Aqui você validaria o token JWT
            # authenticated_user = validate_jwt_token(token)
            # Por simplicidade, vamos assumir que o user_id é válido
            authenticated_user = user_id
        except Exception as e:
            await websocket.close(code=1008, reason="Token inválido")
            return
    
    connection_id = await websocket_manager.connect(websocket, authenticated_user)
    
    try:
        # Enviar mensagem de boas-vindas personalizada
        if authenticated_user:
            welcome_message = WebSocketMessage(
                type=UpdateType.NOTIFICATION,
                data={
                    "message": f"Bem-vindo de volta, usuário {user_id}!",
                    "features": [
                        "Picks personalizados",
                        "Notificações de resultado",
                        "Alertas de odds favoráveis",
                        "Atualizações de saldo"
                    ]
                },
                user_id=authenticated_user
            )
            await websocket_manager.connections[connection_id].send_message(welcome_message)
        
        while True:
            # Aguardar mensagem do cliente
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                await websocket_manager.handle_client_message(connection_id, message_data)
            except json.JSONDecodeError:
                # Mensagem inválida
                error_message = WebSocketMessage(
                    type=UpdateType.NOTIFICATION,
                    data={"error": "Formato de mensagem inválido"}
                )
                await websocket_manager.connections[connection_id].send_message(error_message)
    
    except WebSocketDisconnect:
        await websocket_manager.disconnect(connection_id)

@router.get("/ws/stats")
async def get_websocket_stats(current_user: User = Depends(get_current_user_websocket)):
    """
    Estatísticas das conexões WebSocket (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return websocket_manager.get_stats()

@router.post("/ws/broadcast")
async def broadcast_message(
    message_data: dict,
    channel: Optional[str] = None,
    current_user: User = Depends(get_current_user_websocket)
):
    """
    Envia mensagem broadcast (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    message = WebSocketMessage(
        type=UpdateType.SYSTEM_ALERT,
        data=message_data
    )
    
    if channel:
        sent_count = await websocket_manager.broadcast_to_channel(channel, message)
    else:
        sent_count = await websocket_manager.broadcast_to_all(message)
    
    return {
        "message": "Broadcast enviado",
        "sent_to": sent_count,
        "channel": channel
    }

@router.post("/ws/notify-user/{user_id}")
async def notify_user(
    user_id: int,
    message_data: dict,
    current_user: User = Depends(get_current_user_websocket)
):
    """
    Envia notificação para usuário específico
    """
    # Verificar se pode notificar (admin ou próprio usuário)
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    message = WebSocketMessage(
        type=UpdateType.NOTIFICATION,
        data=message_data,
        user_id=user_id
    )
    
    sent_count = await websocket_manager.send_to_user(user_id, message)
    
    return {
        "message": "Notificação enviada",
        "user_id": user_id,
        "sent_to": sent_count
    }

# Inicializar tarefas em background quando o módulo for importado
asyncio.create_task(websocket_manager.start_background_tasks()) 