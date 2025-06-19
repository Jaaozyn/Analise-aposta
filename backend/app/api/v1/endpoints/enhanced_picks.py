"""
Enhanced Picks Endpoints - Sistema de Múltiplos Picks
Sempre retorna 5 picks por partida + destaque para EV+
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum

from app.core.database import get_db
from app.models.user import User
from app.models.match import Match
from app.api.dependencies import get_current_user, get_optional_current_user
from app.core.rate_limiter import limiter, enhanced_rate_limit_check, RateLimits
from app.core.smart_cache import cache_result
from app.core.audit_trail import log_user_action, AuditEventType

# Simular o analisador (seria importado do arquivo que criei acima)
# from app.ml.multi_market_analyzer import create_multi_market_analyzer, MarketPick, MatchAnalysis

router = APIRouter()

# Schemas de resposta
class PickResponse(BaseModel):
    """Resposta de um pick individual"""
    market_type: str
    selection: str
    description: str
    calculated_probability: float
    market_odds: float
    expected_value: float
    confidence_score: float
    stake_suggestion: float
    risk_level: str
    reasoning: List[str]
    is_value_bet: bool
    market_probability: float
    value_badge: Optional[str] = None  # "🔥 EV+" quando for valor

class MatchPicksResponse(BaseModel):
    """Resposta completa de picks para uma partida"""
    match_id: str
    home_team: str
    away_team: str
    sport: str
    league: str
    match_time: datetime
    
    # Picks organizados
    value_picks: List[PickResponse]      # EV+ destacados
    top_picks: List[PickResponse]        # Top 5 sempre
    analysis_summary: Dict[str, Any]     # Resumo da análise
    
    # Metadados
    total_markets_analyzed: int
    value_opportunities_found: int
    recommendation_level: str            # "excellent", "good", "fair", "poor"
    created_at: datetime

class MultipleMatchesResponse(BaseModel):
    """Resposta para múltiplas partidas"""
    matches: List[MatchPicksResponse]
    summary: Dict[str, Any]
    total_matches: int
    total_value_opportunities: int

@router.get("/enhanced-picks", response_model=MultipleMatchesResponse)
@limiter.limit("30/hour")  # Rate limit moderado
async def get_enhanced_picks(
    request: Request,
    sport: str = Query("football", description="Esporte (football, basketball, cs2, valorant)"),
    league: Optional[str] = Query(None, description="Liga específica"),
    date: Optional[str] = Query(None, description="Data (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de partidas"),
    current_user: User = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    🎯 ENDPOINT PRINCIPAL: Picks Melhorados com 5 opções por partida
    
    Features:
    - Sempre retorna 5 picks por partida
    - Destaca picks com EV+ quando existir  
    - Análise de múltiplos mercados
    - Classificação por nível de recomendação
    """
    
    try:
        # Rate limiting específico
        await enhanced_rate_limit_check(
            request,
            endpoint_type="enhanced_picks",
            limit="30/hour"
        )
        
        # Buscar partidas do dia/esporte
        matches_data = await _get_matches_data(db, sport, league, date, limit)
        
        if not matches_data:
            return MultipleMatchesResponse(
                matches=[],
                summary={"message": "Nenhuma partida encontrada para os critérios"},
                total_matches=0,
                total_value_opportunities=0
            )
        
        # Analisar cada partida
        analyzed_matches = []
        total_value_opps = 0
        
        for match_data in matches_data:
            # Simular análise completa (seria feita pelo MultiMarketAnalyzer)
            match_analysis = await _analyze_match_comprehensive(match_data, sport)
            
            # Converter para response format
            match_response = await _convert_to_response(match_analysis)
            analyzed_matches.append(match_response)
            
            total_value_opps += match_response.value_opportunities_found
        
        # Log da ação
        if current_user:
            await log_user_action(
                user_id=current_user.id,
                action="enhanced_picks_requested",
                details={
                    "sport": sport,
                    "matches_analyzed": len(analyzed_matches),
                    "value_opportunities": total_value_opps
                }
            )
        
        # Resumo geral
        summary = {
            "total_matches_analyzed": len(analyzed_matches),
            "average_picks_per_match": 5,
            "total_value_opportunities": total_value_opps,
            "value_rate": f"{(total_value_opps / (len(analyzed_matches) * 5) * 100):.1f}%" if analyzed_matches else "0%",
            "analysis_quality": "high" if total_value_opps > 0 else "standard",
            "recommendation": _generate_overall_recommendation(analyzed_matches, total_value_opps)
        }
        
        return MultipleMatchesResponse(
            matches=analyzed_matches,
            summary=summary,
            total_matches=len(analyzed_matches),
            total_value_opportunities=total_value_opps
        )
        
    except Exception as e:
        logger.error(f"Erro em enhanced_picks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar picks melhorados: {str(e)}"
        )

@router.get("/match/{match_id}/detailed-picks", response_model=MatchPicksResponse)
@limiter.limit("60/hour")  # Rate limit mais generoso para match específica
async def get_detailed_match_picks(
    request: Request,
    match_id: str,
    include_all_markets: bool = Query(False, description="Incluir todos os mercados analisados"),
    current_user: User = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    🔍 Análise detalhada de uma partida específica
    
    Retorna:
    - Todos os picks EV+ encontrados  
    - Top 5 picks sempre
    - Análise detalhada de cada mercado
    - Reasoning completo
    """
    
    try:
        # Buscar dados da partida
        match_data = await _get_single_match_data(db, match_id)
        
        if not match_data:
            raise HTTPException(
                status_code=404,
                detail="Partida não encontrada"
            )
        
        # Análise completa
        match_analysis = await _analyze_match_comprehensive(
            match_data, 
            match_data.get("sport", "football"),
            detailed=True
        )
        
        # Converter para response
        response = await _convert_to_response(match_analysis, include_all_markets)
        
        # Log da consulta detalhada
        if current_user:
            await log_user_action(
                user_id=current_user.id,
                action="detailed_match_analysis",
                details={
                    "match_id": match_id,
                    "picks_generated": len(response.top_picks),
                    "value_picks_found": len(response.value_picks)
                }
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro em detailed_match_picks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao analisar partida {match_id}: {str(e)}"
        )

@router.post("/match/{match_id}/refresh-analysis")
@limiter.limit("10/hour")  # Rate limit restritivo para refresh
async def refresh_match_analysis(
    request: Request,
    match_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    🔄 Forçar nova análise de uma partida
    
    Útil quando:
    - Odds mudaram significativamente
    - Novas informações disponíveis (lesões, escalações)
    - Usuário quer análise mais recente
    """
    
    try:
        # Rate limiting restritivo
        await enhanced_rate_limit_check(
            request,
            endpoint_type="refresh_analysis", 
            limit="10/hour"
        )
        
        # Verificar se partida existe
        match_data = await _get_single_match_data(db, match_id)
        if not match_data:
            raise HTTPException(status_code=404, detail="Partida não encontrada")
        
        # Agendar nova análise em background
        background_tasks.add_task(
            _refresh_match_analysis_background,
            match_id, 
            match_data,
            current_user.id
        )
        
        # Log da ação
        await log_user_action(
            user_id=current_user.id,
            action="analysis_refresh_requested",
            details={"match_id": match_id}
        )
        
        return {
            "message": "Análise atualizada solicitada",
            "match_id": match_id,
            "status": "processing",
            "estimated_completion": "2-3 minutos",
            "note": "A análise será atualizada em background. Consulte novamente em alguns minutos."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro em refresh_analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao solicitar refresh: {str(e)}"
        )

@router.get("/picks-summary", response_model=Dict[str, Any])
@limiter.limit("120/hour")  # Rate limit generoso para summary
async def get_picks_summary(
    request: Request,
    timeframe: str = Query("today", description="today, tomorrow, week"),
    sport: str = Query("all", description="all, football, basketball, cs2, valorant"),
    current_user: User = Depends(get_optional_current_user)
):
    """
    📊 Resumo geral dos picks disponíveis
    
    Mostra:
    - Número de partidas com picks EV+
    - Distribuição por esporte
    - Qualidade média das oportunidades
    - Recomendações do dia
    """
    
    try:
        # Simular dados de resumo
        summary_data = {
            "timeframe": timeframe,
            "sport_filter": sport,
            "overview": {
                "total_matches_today": 15,
                "matches_with_value": 8,
                "total_value_picks": 23,
                "average_ev": 8.4,
                "best_opportunity": {
                    "match": "Real Madrid vs Barcelona",
                    "pick": "Over 2.5 Goals",
                    "ev": 15.2,
                    "confidence": 87
                }
            },
            "by_sport": {
                "football": {"matches": 8, "value_picks": 15, "avg_ev": 9.1},
                "basketball": {"matches": 4, "value_picks": 6, "avg_ev": 7.2},
                "cs2": {"matches": 2, "value_picks": 2, "avg_ev": 6.8},
                "valorant": {"matches": 1, "value_picks": 0, "avg_ev": 0}
            },
            "quality_distribution": {
                "excellent": 5,  # EV > 12%
                "good": 8,       # EV 8-12% 
                "fair": 10,      # EV 5-8%
                "poor": 0        # EV < 5% (não mostrados)
            },
            "recommendations": [
                "Futebol tem as melhores oportunidades hoje",
                "8 partidas com valor matemático identificado",
                "El Clásico com excelente valor em Over 2.5",
                "Evitar e-sports hoje - poucas oportunidades"
            ],
            "market_insights": {
                "best_markets": ["Over/Under Goals", "Both Teams Score", "Asian Handicap"],
                "avoid_markets": ["Correct Score", "First Goalscorer"],
                "market_efficiency": "75%",  # Quão eficiente está o mercado
                "value_rate": "15.3%"       # % de picks com valor
            }
        }
        
        return summary_data
        
    except Exception as e:
        logger.error(f"Erro em picks_summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar resumo: {str(e)}"
        )

# Funções auxiliares
async def _get_matches_data(db: AsyncSession, sport: str, league: Optional[str], date: Optional[str], limit: int) -> List[Dict]:
    """Busca dados das partidas do banco"""
    # Simulação de dados - em produção seria query real
    matches = [
        {
            "id": "match_001",
            "home_team": "Real Madrid",
            "away_team": "Barcelona", 
            "sport": "football",
            "league": "La Liga",
            "match_time": datetime.now() + timedelta(hours=2),
            "home_avg_goals": 2.1,
            "away_avg_goals": 1.9,
            "home_avg_conceded": 0.8,
            "away_avg_conceded": 0.9,
            "home_form": "WWDWL",
            "away_form": "WLWWD",
            "importance_factor": 1.3
        },
        {
            "id": "match_002", 
            "home_team": "Manchester City",
            "away_team": "Liverpool",
            "sport": "football",
            "league": "Premier League",
            "match_time": datetime.now() + timedelta(hours=4),
            "home_avg_goals": 2.3,
            "away_avg_goals": 2.0,
            "home_avg_conceded": 1.0,
            "away_avg_conceded": 1.1,
            "home_form": "WWWDW",
            "away_form": "WWLWW",
            "importance_factor": 1.2
        }
    ]
    
    return matches[:limit]

async def _get_single_match_data(db: AsyncSession, match_id: str) -> Optional[Dict]:
    """Busca dados de uma partida específica"""
    # Simulação - em produção seria query real
    if match_id == "match_001":
        return {
            "id": "match_001",
            "home_team": "Real Madrid",
            "away_team": "Barcelona",
            "sport": "football",
            "league": "La Liga", 
            "match_time": datetime.now() + timedelta(hours=2),
            "home_avg_goals": 2.1,
            "away_avg_goals": 1.9,
            "home_avg_conceded": 0.8,
            "away_avg_conceded": 0.9,
            "home_form": "WWDWL",
            "away_form": "WLWWD",
            "importance_factor": 1.3
        }
    return None

async def _analyze_match_comprehensive(match_data: Dict, sport: str, detailed: bool = False) -> Dict:
    """Simula análise completa da partida"""
    # Em produção seria:
    # analyzer = create_multi_market_analyzer(sport)
    # return analyzer.analyze_match_comprehensive(match_data, market_odds)
    
    # Simulação de picks gerados
    picks = [
        {
            "market_type": "over_under_goals",
            "selection": "Over 2.5 Goals",
            "description": "Mais de 2.5 gols na partida",
            "calculated_probability": 0.65,
            "market_odds": 1.75,
            "expected_value": 13.7,  # EV+
            "confidence_score": 0.85,
            "stake_suggestion": 3.2,
            "risk_level": "low",
            "reasoning": [
                "Ambos times com alta média de gols (2.1 + 1.9)",
                "El Clásico historicamente aberto",
                "Modelos ML convergem em 65% chance Over 2.5"
            ],
            "is_value_bet": True,
            "market_probability": 0.571
        },
        {
            "market_type": "both_teams_score", 
            "selection": "Ambos Marcam - Sim",
            "description": "Ambos os times marcam: Sim",
            "calculated_probability": 0.78,
            "market_odds": 1.65,
            "expected_value": 8.2,  # EV+
            "confidence_score": 0.82,
            "stake_suggestion": 2.8,
            "risk_level": "low",
            "reasoning": [
                "Real marca em 89% dos jogos em casa",
                "Barça marca em 85% dos jogos fora", 
                "Defesas não são herméticas"
            ],
            "is_value_bet": True,
            "market_probability": 0.606
        },
        {
            "market_type": "match_result",
            "selection": "Vitória Real Madrid",
            "description": "Real Madrid vence a partida",
            "calculated_probability": 0.425,
            "market_odds": 2.10,
            "expected_value": -10.7,  # EV negativo
            "confidence_score": 0.85,
            "stake_suggestion": 0.0,
            "risk_level": "high",
            "reasoning": [
                "Real com 42.5% de chance calculada",
                "Mercado precifica em 47.6% (odds 2.10)",
                "Sem valor matemático neste mercado"
            ],
            "is_value_bet": False,
            "market_probability": 0.476
        },
        {
            "market_type": "handicap",
            "selection": "Real Madrid -0.5",
            "description": "Real Madrid com handicap -0.5",
            "calculated_probability": 0.48,
            "market_odds": 2.05,
            "expected_value": -1.8,  # EV levemente negativo
            "confidence_score": 0.80,
            "stake_suggestion": 0.0,
            "risk_level": "medium",
            "reasoning": [
                "Real favorito por margem mínima",
                "Handicap -0.5 elimina empate",
                "Valor marginal negativo"
            ],
            "is_value_bet": False,
            "market_probability": 0.488
        },
        {
            "market_type": "first_half",
            "selection": "1º Tempo - Empate", 
            "description": "Resultado do primeiro tempo: Empate",
            "calculated_probability": 0.35,
            "market_odds": 2.80,
            "expected_value": -2.0,  # EV negativo
            "confidence_score": 0.75,
            "stake_suggestion": 0.0,
            "risk_level": "medium",
            "reasoning": [
                "1º tempo mais equilibrado",
                "35% chance de empate no intervalo",
                "Times começam cautelosos"
            ],
            "is_value_bet": False,
            "market_probability": 0.357
        }
    ]
    
    return {
        "match_data": match_data,
        "all_picks": picks,
        "value_picks": [p for p in picks if p["is_value_bet"]],
        "top_picks": picks,  # Top 5
        "analysis_metadata": {
            "total_markets_analyzed": 8,
            "value_opportunities_found": 2,
            "best_ev": 13.7,
            "analysis_time_ms": 150
        }
    }

async def _convert_to_response(analysis: Dict, include_all: bool = False) -> MatchPicksResponse:
    """Converte análise para formato de resposta"""
    match_data = analysis["match_data"]
    
    # Converter picks para PickResponse
    def convert_pick(pick_data: Dict) -> PickResponse:
        return PickResponse(
            market_type=pick_data["market_type"],
            selection=pick_data["selection"],
            description=pick_data["description"],
            calculated_probability=pick_data["calculated_probability"],
            market_odds=pick_data["market_odds"],
            expected_value=pick_data["expected_value"],
            confidence_score=pick_data["confidence_score"],
            stake_suggestion=pick_data["stake_suggestion"],
            risk_level=pick_data["risk_level"],
            reasoning=pick_data["reasoning"],
            is_value_bet=pick_data["is_value_bet"],
            market_probability=pick_data["market_probability"],
            value_badge="🔥 EV+" if pick_data["is_value_bet"] else None
        )
    
    value_picks = [convert_pick(p) for p in analysis["value_picks"]]
    top_picks = [convert_pick(p) for p in analysis["top_picks"]]
    
    # Determinar nível de recomendação
    value_count = len(value_picks)
    best_ev = max([p["expected_value"] for p in analysis["all_picks"]], default=0)
    
    if value_count >= 3 and best_ev > 12:
        recommendation_level = "excellent"
    elif value_count >= 2 and best_ev > 8:
        recommendation_level = "good"
    elif value_count >= 1 and best_ev > 5:
        recommendation_level = "fair"
    else:
        recommendation_level = "poor"
    
    return MatchPicksResponse(
        match_id=match_data["id"],
        home_team=match_data["home_team"],
        away_team=match_data["away_team"],
        sport=match_data["sport"],
        league=match_data["league"],
        match_time=match_data["match_time"],
        value_picks=value_picks,
        top_picks=top_picks,
        analysis_summary={
            "recommendation_level": recommendation_level,
            "best_ev_found": best_ev,
            "markets_with_value": value_count,
            "analysis_quality": "high" if value_count > 0 else "standard",
            "key_insights": _generate_key_insights(analysis)
        },
        total_markets_analyzed=analysis["analysis_metadata"]["total_markets_analyzed"],
        value_opportunities_found=analysis["analysis_metadata"]["value_opportunities_found"],
        recommendation_level=recommendation_level,
        created_at=datetime.now()
    )

def _generate_key_insights(analysis: Dict) -> List[str]:
    """Gera insights principais da análise"""
    insights = []
    
    value_picks = analysis["value_picks"]
    if value_picks:
        best_pick = max(value_picks, key=lambda x: x["expected_value"])
        insights.append(f"Melhor oportunidade: {best_pick['selection']} (EV: +{best_pick['expected_value']:.1f}%)")
        
        if len(value_picks) > 1:
            insights.append(f"{len(value_picks)} mercados com valor matemático identificados")
    else:
        insights.append("Nenhum valor matemático encontrado - mercado eficiente")
        
    # Análise dos top picks mesmo sem valor
    top_picks = analysis["top_picks"]
    if top_picks:
        best_non_value = max([p for p in top_picks if not p["is_value_bet"]], 
                            key=lambda x: x["expected_value"], default=None)
        if best_non_value:
            insights.append(f"Menor perda esperada: {best_non_value['selection']} (EV: {best_non_value['expected_value']:+.1f}%)")
    
    return insights

def _generate_overall_recommendation(matches: List[MatchPicksResponse], total_value: int) -> str:
    """Gera recomendação geral"""
    if total_value >= 15:
        return "Excelente dia para apostas - múltiplas oportunidades de valor"
    elif total_value >= 8:
        return "Bom dia para apostas - algumas oportunidades sólidas"
    elif total_value >= 3:
        return "Dia moderado - poucas oportunidades de qualidade"
    else:
        return "Dia desafiador - mercado muito eficiente hoje"

async def _refresh_match_analysis_background(match_id: str, match_data: Dict, user_id: int):
    """Executa refresh da análise em background"""
    # Simular processo de refresh
    import asyncio
    await asyncio.sleep(30)  # Simular tempo de processamento
    
    # Log de conclusão
    await log_user_action(
        user_id=user_id,
        action="analysis_refresh_completed",
        details={"match_id": match_id}
    ) 