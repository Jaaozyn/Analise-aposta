from fastapi import APIRouter
from app.api.v1.endpoints import picks, matches, users, payments, analytics

api_router = APIRouter()

# Incluir todas as rotas
api_router.include_router(picks.router, prefix="/picks", tags=["picks"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"]) 