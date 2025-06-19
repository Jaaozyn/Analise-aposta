from fastapi import APIRouter

from app.api.v1.endpoints import picks
from app.api.v1.endpoints import websocket
from app.api.v1.endpoints import pricing

api_router = APIRouter()

# Incluir rotas existentes
api_router.include_router(picks.router, prefix="/picks", tags=["picks"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"]) 