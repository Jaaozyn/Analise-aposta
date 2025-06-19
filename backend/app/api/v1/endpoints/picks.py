from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.pick import Pick, PickStatus
from app.models.match import Match
from app.schemas.pick import PickResponse, PickCreate, PickListResponse
from app.services.pick_generator import PickGeneratorService
from app.core.cache import cache

router = APIRouter()

@router.get("/", response_model=PickListResponse)
async def get_picks(
    sport: Optional[str] = Query(None, description="Filtrar por esporte"),
    status: Optional[str] = Query(PickStatus.ACTIVE, description="Status das dicas"),
    min_ev: Optional[float] = Query(0, description="EV mínimo"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db)
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
        query = db.query(Pick).join(Match)
        
        # Aplicar filtros
        if sport:
            query = query.filter(Match.sport == sport)
        if status:
            query = query.filter(Pick.status == status)
        if min_ev > 0:
            query = query.filter(Pick.expected_value >= min_ev)
        
        # Ordenar por EV decrescente e limitar
        query = query.order_by(Pick.expected_value.desc()).limit(limit)
        
        picks = await query.all()
        
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
async def get_pick_detail(
    pick_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Buscar detalhes de uma dica específica
    
    Retorna informações completas da dica incluindo análise
    """
    
    try:
        pick = await db.query(Pick).join(Match).filter(Pick.id == pick_id).first()
        
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

@router.post("/generate", response_model=dict)
async def generate_picks(
    sport: str = Query(..., description="Esporte para gerar picks"),
    force: bool = Query(False, description="Forçar geração mesmo se já existem picks"),
    db: AsyncSession = Depends(get_db)
):
    """
    Gerar novas dicas para um esporte
    
    Analisa partidas e gera picks com valor esperado positivo
    """
    
    try:
        pick_service = PickGeneratorService(db)
        result = await pick_service.generate_picks_for_sport(sport, force_regenerate=force)
        
        return {
            "message": f"Picks gerados para {sport}",
            "picks_generated": result["picks_generated"],
            "matches_analyzed": result["matches_analyzed"],
            "sport": sport
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar picks: {str(e)}")

@router.get("/stats/summary", response_model=dict)
async def get_picks_stats(
    sport: Optional[str] = Query(None),
    days: int = Query(7, description="Número de dias para análise"),
    db: AsyncSession = Depends(get_db)
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