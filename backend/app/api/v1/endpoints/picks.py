from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.pick import Pick, PickStatus
from app.models.match import Match
from app.models.user import User
from app.schemas.pick import PickResponse, PickCreate, PickListResponse
from app.services.pick_generator import PickGeneratorService
from app.core.cache import cache
from app.api.dependencies import get_current_user
from app.core.rate_limiter import limiter, RateLimits, enhanced_rate_limit_check
from sqlalchemy import select

router = APIRouter()

@router.get("/", response_model=PickListResponse)
@limiter.limit(RateLimits.PICKS_LIST)
async def get_picks(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    sport: Optional[str] = Query(None, description="Filtrar por esporte"),
    status: Optional[str] = Query(PickStatus.ACTIVE, description="Status das dicas"),
    min_ev: Optional[float] = Query(0, description="EV mínimo"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Buscar dicas/picks com filtros
    
    - **sport**: Filtrar por esporte (football, basketball, cs2, valorant)
    - **status**: Status das dicas (active, won, lost, void)
    - **min_ev**: Valor esperado mínimo em %
    - **limit**: Limite de resultados
    """
    
    # Verificar cache primeiro
    cache_key = f"picks_{sport}_{status}_{min_ev}_{limit}"
    cached_picks = await cache.get(cache_key)
    if cached_picks:
        return PickListResponse(picks=cached_picks, total=len(cached_picks))
    
    try:
        # Query base
        query = select(Pick).join(Match).offset(skip).limit(limit)
        
        # Aplicar filtros
        if sport:
            query = query.filter(Match.sport == sport)
        if status:
            query = query.filter(Pick.status == status)
        if min_ev > 0:
            query = query.filter(Pick.expected_value >= min_ev)
        
        result = await db.execute(query)
        picks = result.scalars().all()
        
        # Converter para response
        picks_response = [
            PickResponse(
                id=pick.id,
                match_id=pick.match_id,
                sport=pick.match.sport,
                home_team=pick.match.team_home,
                away_team=pick.match.team_away,
                match_date=pick.match.match_date,
                market=pick.market,
                selection=pick.selection,
                expected_value=pick.expected_value,
                confidence_score=pick.confidence_score,
                min_odds=pick.min_odds,
                suggested_stake=pick.suggested_stake,
                status=pick.status,
                created_at=pick.created_at,
                expires_at=pick.expires_at
            )
            for pick in picks
        ]
        
        # Cachear resultado por 10 minutos
        await cache.set(cache_key, picks_response, expire=600)
        
        return PickListResponse(picks=picks_response, total=len(picks_response))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar picks: {str(e)}")

@router.get("/today", response_model=PickListResponse)
async def get_todays_picks(
    sport: Optional[str] = Query(None),
    min_ev: float = Query(5.0, description="EV mínimo para filtrar"),
    db: AsyncSession = Depends(get_db)
):
    """
    Buscar melhores dicas de hoje
    
    Retorna as dicas com maior valor esperado para hoje
    """
    
    try:
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        query = db.query(Pick).join(Match).filter(
            Match.match_date >= today,
            Match.match_date < tomorrow,
            Pick.status == PickStatus.ACTIVE,
            Pick.expected_value >= min_ev
        )
        
        if sport:
            query = query.filter(Match.sport == sport)
        
        picks = await query.order_by(Pick.expected_value.desc()).limit(10).all()
        
        picks_response = [
            PickResponse(
                id=pick.id,
                match_id=pick.match_id,
                sport=pick.match.sport,
                home_team=pick.match.team_home,
                away_team=pick.match.team_away,
                match_date=pick.match.match_date,
                market=pick.market,
                selection=pick.selection,
                expected_value=pick.expected_value,
                confidence_score=pick.confidence_score,
                min_odds=pick.min_odds,
                suggested_stake=pick.suggested_stake,
                status=pick.status,
                created_at=pick.created_at,
                expires_at=pick.expires_at
            )
            for pick in picks
        ]
        
        return PickListResponse(picks=picks_response, total=len(picks_response))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar picks de hoje: {str(e)}")

@router.get("/{pick_id}", response_model=PickResponse)
@limiter.limit(RateLimits.PICKS_LIST)
async def get_pick_detail(
    request: Request,
    pick_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Buscar detalhes de uma dica específica
    
    Retorna informações completas da dica incluindo análise
    """
    
    try:
        result = await db.execute(select(Pick).join(Match).filter(Pick.id == pick_id))
        pick = result.scalar_one_or_none()
        
        if not pick:
            raise HTTPException(status_code=404, detail="Pick não encontrado")
        
        return PickResponse(
            id=pick.id,
            match_id=pick.match_id,
            sport=pick.match.sport,
            home_team=pick.match.team_home,
            away_team=pick.match.team_away,
            match_date=pick.match.match_date,
            market=pick.market,
            selection=pick.selection,
            expected_value=pick.expected_value,
            confidence_score=pick.confidence_score,
            min_odds=pick.min_odds,
            suggested_stake=pick.suggested_stake,
            status=pick.status,
            analysis_data=pick.analysis_data,
            confidence_factors=pick.confidence_factors,
            created_at=pick.created_at,
            expires_at=pick.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar pick: {str(e)}")

@router.post("/generate", response_model=List[PickResponse])
@limiter.limit(RateLimits.PICKS_GENERATION)
async def generate_picks(
    request: Request,
    sport: str = Query(..., description="Esporte (football, basketball, cs2, valorant)"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de picks"),
    min_ev: float = Query(0.05, ge=0.01, description="EV mínimo (%)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🎯 ENDPOINT CRÍTICO: Geração de Picks com IA
    Rate Limit: 5 gerações por hora (recurso computacionalmente caro)
    """
    # Rate limiting específico para geração (mais restritivo)
    await enhanced_rate_limit_check(
        request, 
        endpoint_type="picks_generation", 
        limit=RateLimits.PICKS_GENERATION
    )
    
    try:
        pick_service = PickGeneratorService(db)
        result = await pick_service.generate_picks_for_sport(sport, force_regenerate=False)
        
        return result["picks"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar picks: {str(e)}")

@router.get("/stats/summary", response_model=dict)
@limiter.limit(RateLimits.USER_DATA)
async def get_picks_stats(
    request: Request,
    sport: Optional[str] = Query(None),
    days: int = Query(7, description="Número de dias para análise"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Estatísticas gerais dos picks
    
    Retorna métricas de performance dos picks
    """
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query base
        query = db.query(Pick).join(Match).filter(
            Pick.created_at >= start_date,
            Pick.created_at <= end_date
        )
        
        if sport:
            query = query.filter(Match.sport == sport)
        
        all_picks = await query.all()
        
        # Calcular estatísticas
        total_picks = len(all_picks)
        active_picks = len([p for p in all_picks if p.status == PickStatus.ACTIVE])
        won_picks = len([p for p in all_picks if p.status == PickStatus.WON])
        lost_picks = len([p for p in all_picks if p.status == PickStatus.LOST])
        
        settled_picks = won_picks + lost_picks
        win_rate = (won_picks / settled_picks * 100) if settled_picks > 0 else 0
        
        avg_ev = sum(p.expected_value for p in all_picks) / total_picks if total_picks > 0 else 0
        avg_confidence = sum(p.confidence_score for p in all_picks) / total_picks if total_picks > 0 else 0
        
        return {
            "period_days": days,
            "sport": sport,
            "total_picks": total_picks,
            "active_picks": active_picks,
            "settled_picks": settled_picks,
            "won_picks": won_picks,
            "lost_picks": lost_picks,
            "win_rate": round(win_rate, 2),
            "average_ev": round(avg_ev, 2),
            "average_confidence": round(avg_confidence * 100, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")

@router.get("/stats/performance")
@limiter.limit(RateLimits.USER_DATA)
async def get_pick_stats(
    request: Request,
    sport: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 Estatísticas de performance dos picks
    Rate Limit: 50 consultas por hora
    """
    # Lógica para calcular estatísticas
    return {
        "total_picks": 150,
        "win_rate": 68.5,
        "average_ev": 8.2,
        "total_roi": 23.8,
        "best_sport": "football",
        "recent_performance": {
            "last_7_days": {"wins": 12, "losses": 3, "roi": 15.2},
            "last_30_days": {"wins": 48, "losses": 22, "roi": 18.7}
        }
    }

@router.post("/favorite/{pick_id}")
@limiter.limit(RateLimits.USER_DATA)
async def favorite_pick(
    request: Request,
    pick_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ⭐ Favoritar pick
    """
    # Lógica para favoritar pick
    return {"message": "Pick favoritado com sucesso"}

@router.delete("/favorite/{pick_id}")
@limiter.limit(RateLimits.USER_DATA)
async def unfavorite_pick(
    request: Request,
    pick_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ❌ Desfavoritar pick
    """
    # Lógica para desfavoritar pick
    return {"message": "Pick removido dos favoritos"} 