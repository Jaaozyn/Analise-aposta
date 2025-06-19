from fastapi import APIRouter

from app.api.v1.endpoints import picks
from app.api.v1.endpoints import websocket
from app.api.v1.endpoints import pricing
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import backup

api_router = APIRouter()

# Incluir rotas existentes e novas
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(picks.router, prefix="/picks", tags=["picks"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
api_router.include_router(backup.router, prefix="/backup", tags=["backup"]) 