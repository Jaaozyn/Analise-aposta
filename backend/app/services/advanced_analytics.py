"""
Advanced Analytics Service - Analytics Avançados de Picks
Sistema completo de análise de performance das recomendações
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

class AnalyticsTimeframe(Enum):
    """Períodos de análise"""
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"
    ALL_TIME = "all"

@dataclass
class PickPerformanceMetrics:
    """Métricas de performance de um pick"""
    pick_id: str
    selection: str
    sport: str
    market_type: str
    recommended_odds: float
    actual_odds_achieved: Optional[float]
    expected_value: float
    confidence_score: float
    outcome: Optional[str]  # "won", "lost", "void", "pending"
    roi: Optional[float]
    stake_suggested: float
    stake_actual: Optional[float]
    profit_loss: Optional[float]
    created_at: datetime
    settled_at: Optional[datetime]

@dataclass
class PortfolioAnalytics:
    """Analytics completos do portfólio de um usuário"""
    user_id: str
    timeframe: str
    
    # Métricas Gerais
    total_picks: int
    settled_picks: int
    pending_picks: int
    win_rate: float
    total_roi: float
    total_stake: float
    total_profit: float
    
    # Métricas Avançadas
    sharpe_ratio: float
    max_drawdown: float
    longest_winning_streak: int
    longest_losing_streak: int
    avg_odds: float
    avg_ev_recommended: float
    
    # Por Esporte
    performance_by_sport: Dict[str, Dict]
    
    # Por Mercado
    performance_by_market: Dict[str, Dict]
    
    # Evolução Temporal
    monthly_performance: List[Dict]
    
    # Insights IA
    ai_insights: List[str]

class AdvancedAnalyticsService:
    """Serviço de Analytics Avançados"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_portfolio_analytics(
        self, 
        user_id: str, 
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MONTH
    ) -> PortfolioAnalytics:
        """
        Gera analytics completos do portfólio do usuário
        """
        
        # Calcular período
        end_date = datetime.now()
        if timeframe == AnalyticsTimeframe.WEEK:
            start_date = end_date - timedelta(days=7)
        elif timeframe == AnalyticsTimeframe.MONTH:
            start_date = end_date - timedelta(days=30)
        elif timeframe == AnalyticsTimeframe.QUARTER:
            start_date = end_date - timedelta(days=90)
        elif timeframe == AnalyticsTimeframe.YEAR:
            start_date = end_date - timedelta(days=365)
        else:  # ALL_TIME
            start_date = datetime(2020, 1, 1)
        
        # Buscar picks do usuário no período
        user_picks = await self._get_user_picks_with_results(user_id, start_date, end_date)
        
        if not user_picks:
            return self._empty_analytics(user_id, timeframe.value)
        
        # Calcular métricas básicas
        total_picks = len(user_picks)
        settled_picks = len([p for p in user_picks if p.outcome in ["won", "lost"]])
        pending_picks = len([p for p in user_picks if p.outcome == "pending"])
        won_picks = len([p for p in user_picks if p.outcome == "won"])
        
        win_rate = (won_picks / settled_picks * 100) if settled_picks > 0 else 0
        
        # Calcular ROI e lucro
        total_stake = sum(p.stake_actual or 0 for p in user_picks if p.stake_actual)
        total_profit = sum(p.profit_loss or 0 for p in user_picks if p.profit_loss is not None)
        total_roi = (total_profit / total_stake * 100) if total_stake > 0 else 0
        
        # Métricas avançadas
        sharpe_ratio = await self._calculate_sharpe_ratio(user_picks)
        max_drawdown = await self._calculate_max_drawdown(user_picks)
        longest_winning_streak = await self._calculate_longest_streak(user_picks, "won")
        longest_losing_streak = await self._calculate_longest_streak(user_picks, "lost")
        
        avg_odds = np.mean([p.actual_odds_achieved or p.recommended_odds for p in user_picks])
        avg_ev_recommended = np.mean([p.expected_value for p in user_picks])
        
        # Performance por esporte
        performance_by_sport = await self._calculate_performance_by_category(
            user_picks, "sport"
        )
        
        # Performance por mercado
        performance_by_market = await self._calculate_performance_by_category(
            user_picks, "market_type"
        )
        
        # Evolução mensal
        monthly_performance = await self._calculate_monthly_evolution(user_picks)
        
        # Insights IA
        ai_insights = await self._generate_ai_insights(user_picks)
        
        return PortfolioAnalytics(
            user_id=user_id,
            timeframe=timeframe.value,
            total_picks=total_picks,
            settled_picks=settled_picks,
            pending_picks=pending_picks,
            win_rate=win_rate,
            total_roi=total_roi,
            total_stake=total_stake,
            total_profit=total_profit,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            longest_winning_streak=longest_winning_streak,
            longest_losing_streak=longest_losing_streak,
            avg_odds=avg_odds,
            avg_ev_recommended=avg_ev_recommended,
            performance_by_sport=performance_by_sport,
            performance_by_market=performance_by_market,
            monthly_performance=monthly_performance,
            ai_insights=ai_insights
        )
    
    async def get_pick_detailed_analytics(self, pick_id: str) -> Dict:
        """
        Analytics detalhados de um pick específico
        """
        
        # Buscar dados do pick
        pick_data = await self._get_pick_with_results(pick_id)
        
        if not pick_data:
            return {"error": "Pick não encontrado"}
        
        # Comparar com picks similares
        similar_picks_performance = await self._get_similar_picks_performance(pick_data)
        
        # Análise de timing
        timing_analysis = await self._analyze_pick_timing(pick_data)
        
        # Market analysis
        market_efficiency = await self._analyze_market_efficiency(pick_data)
        
        return {
            "pick_details": {
                "id": pick_data.pick_id,
                "selection": pick_data.selection,
                "sport": pick_data.sport,
                "market_type": pick_data.market_type,
                "recommended_odds": pick_data.recommended_odds,
                "expected_value": pick_data.expected_value,
                "confidence_score": pick_data.confidence_score,
                "outcome": pick_data.outcome,
                "roi": pick_data.roi
            },
            "performance_context": {
                "similar_picks_win_rate": similar_picks_performance["win_rate"],
                "similar_picks_avg_roi": similar_picks_performance["avg_roi"],
                "percentile_rank": similar_picks_performance["percentile_rank"]
            },
            "timing_analysis": timing_analysis,
            "market_analysis": market_efficiency,
            "lessons_learned": await self._generate_pick_lessons(pick_data)
        }
    
    async def get_platform_analytics(self) -> Dict:
        """
        Analytics gerais da plataforma (para admin)
        """
        
        # Últimos 30 dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Métricas de picks
        total_picks_generated = await self._count_picks_generated(start_date, end_date)
        avg_daily_picks = total_picks_generated / 30
        
        # Accuracy da plataforma
        platform_accuracy = await self._calculate_platform_accuracy(start_date, end_date)
        
        # EV accuracy (quantos picks EV+ realmente foram lucrativos)
        ev_accuracy = await self._calculate_ev_accuracy(start_date, end_date)
        
        # Performance por esporte
        sport_performance = await self._get_platform_sport_performance(start_date, end_date)
        
        # Top performing markets
        top_markets = await self._get_top_performing_markets(start_date, end_date)
        
        # User engagement
        user_engagement = await self._calculate_user_engagement_metrics(start_date, end_date)
        
        return {
            "period": "últimos_30_dias",
            "picks_metrics": {
                "total_generated": total_picks_generated,
                "avg_daily": avg_daily_picks,
                "platform_accuracy": platform_accuracy,
                "ev_accuracy": ev_accuracy
            },
            "performance_by_sport": sport_performance,
            "top_markets": top_markets,
            "user_engagement": user_engagement,
            "quality_metrics": {
                "avg_confidence": await self._get_avg_confidence(start_date, end_date),
                "avg_ev": await self._get_avg_ev(start_date, end_date),
                "picks_with_high_confidence": await self._count_high_confidence_picks(start_date, end_date)
            }
        }
    
    async def generate_performance_report(self, user_id: str) -> Dict:
        """
        Gera relatório completo de performance para o usuário
        """
        
        # Analytics de diferentes períodos
        weekly = await self.get_user_portfolio_analytics(user_id, AnalyticsTimeframe.WEEK)
        monthly = await self.get_user_portfolio_analytics(user_id, AnalyticsTimeframe.MONTH)
        quarterly = await self.get_user_portfolio_analytics(user_id, AnalyticsTimeframe.QUARTER)
        
        # Comparação com a média da plataforma
        platform_benchmarks = await self._get_platform_benchmarks()
        
        # Recommendations personalizadas
        personalized_recommendations = await self._generate_personalized_recommendations(user_id)
        
        # Strengths e weaknesses
        strengths_weaknesses = await self._analyze_user_strengths_weaknesses(user_id)
        
        return {
            "user_id": user_id,
            "report_date": datetime.now().isoformat(),
            "performance_summary": {
                "7_days": {
                    "roi": weekly.total_roi,
                    "win_rate": weekly.win_rate,
                    "picks": weekly.total_picks
                },
                "30_days": {
                    "roi": monthly.total_roi,
                    "win_rate": monthly.win_rate,
                    "picks": monthly.total_picks
                },
                "90_days": {
                    "roi": quarterly.total_roi,
                    "win_rate": quarterly.win_rate,
                    "picks": quarterly.total_picks
                }
            },
            "platform_comparison": {
                "your_roi_vs_platform": monthly.total_roi - platform_benchmarks["avg_roi"],
                "your_winrate_vs_platform": monthly.win_rate - platform_benchmarks["avg_winrate"],
                "percentile_rank": await self._calculate_user_percentile(user_id)
            },
            "strengths": strengths_weaknesses["strengths"],
            "improvement_areas": strengths_weaknesses["weaknesses"],
            "personalized_recommendations": personalized_recommendations,
            "next_goals": await self._suggest_next_goals(user_id)
        }
    
    # Métodos auxiliares
    async def _get_user_picks_with_results(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[PickPerformanceMetrics]:
        """Busca picks do usuário com resultados"""
        
        # Simulação de dados - em produção seria query real no banco
        sample_picks = [
            PickPerformanceMetrics(
                pick_id="pick_001",
                selection="Over 2.5 Goals",
                sport="football",
                market_type="over_under",
                recommended_odds=1.75,
                actual_odds_achieved=1.80,
                expected_value=12.5,
                confidence_score=8.5,
                outcome="won",
                roi=80.0,
                stake_suggested=3.0,
                stake_actual=50.0,
                profit_loss=40.0,
                created_at=datetime.now() - timedelta(days=5),
                settled_at=datetime.now() - timedelta(days=5, hours=2)
            ),
            PickPerformanceMetrics(
                pick_id="pick_002",
                selection="Home Win",
                sport="football", 
                market_type="match_result",
                recommended_odds=2.10,
                actual_odds_achieved=2.05,
                expected_value=8.3,
                confidence_score=7.2,
                outcome="lost",
                roi=-100.0,
                stake_suggested=2.5,
                stake_actual=30.0,
                profit_loss=-30.0,
                created_at=datetime.now() - timedelta(days=3),
                settled_at=datetime.now() - timedelta(days=3, hours=2)
            ),
            PickPerformanceMetrics(
                pick_id="pick_003",
                selection="Both Teams Score",
                sport="football",
                market_type="both_teams_score",
                recommended_odds=1.65,
                actual_odds_achieved=1.70,
                expected_value=15.2,
                confidence_score=9.1,
                outcome="won",
                roi=70.0,
                stake_suggested=4.0,
                stake_actual=40.0,
                profit_loss=28.0,
                created_at=datetime.now() - timedelta(days=1),
                settled_at=datetime.now() - timedelta(hours=2)
            )
        ]
        
        return sample_picks
    
    async def _calculate_sharpe_ratio(self, picks: List[PickPerformanceMetrics]) -> float:
        """Calcula Sharpe Ratio dos picks"""
        if not picks:
            return 0.0
        
        returns = [p.roi/100 for p in picks if p.roi is not None]
        if not returns:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        return mean_return / std_return
    
    async def _calculate_max_drawdown(self, picks: List[PickPerformanceMetrics]) -> float:
        """Calcula maior drawdown"""
        if not picks:
            return 0.0
        
        # Ordenar por data
        sorted_picks = sorted(picks, key=lambda x: x.created_at)
        
        cumulative_returns = []
        cumulative_sum = 0
        
        for pick in sorted_picks:
            if pick.profit_loss is not None:
                cumulative_sum += pick.profit_loss
                cumulative_returns.append(cumulative_sum)
        
        if not cumulative_returns:
            return 0.0
        
        # Calcular drawdown
        peak = cumulative_returns[0]
        max_drawdown = 0
        
        for value in cumulative_returns:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / abs(peak) * 100 if peak != 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    async def _calculate_longest_streak(self, picks: List[PickPerformanceMetrics], outcome: str) -> int:
        """Calcula maior sequência de vitórias/derrotas"""
        if not picks:
            return 0
        
        sorted_picks = sorted(picks, key=lambda x: x.created_at)
        current_streak = 0
        max_streak = 0
        
        for pick in sorted_picks:
            if pick.outcome == outcome:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    async def _calculate_performance_by_category(
        self, 
        picks: List[PickPerformanceMetrics], 
        category: str
    ) -> Dict[str, Dict]:
        """Calcula performance por categoria (esporte, mercado, etc.)"""
        
        performance = {}
        
        for pick in picks:
            cat_value = getattr(pick, category)
            
            if cat_value not in performance:
                performance[cat_value] = {
                    "picks": [],
                    "total_picks": 0,
                    "won": 0,
                    "lost": 0,
                    "total_stake": 0,
                    "total_profit": 0
                }
            
            cat_stats = performance[cat_value]
            cat_stats["picks"].append(pick)
            cat_stats["total_picks"] += 1
            
            if pick.outcome == "won":
                cat_stats["won"] += 1
            elif pick.outcome == "lost":
                cat_stats["lost"] += 1
            
            if pick.stake_actual:
                cat_stats["total_stake"] += pick.stake_actual
            if pick.profit_loss:
                cat_stats["total_profit"] += pick.profit_loss
        
        # Calcular métricas finais
        for cat_value, stats in performance.items():
            settled = stats["won"] + stats["lost"]
            stats["win_rate"] = (stats["won"] / settled * 100) if settled > 0 else 0
            stats["roi"] = (stats["total_profit"] / stats["total_stake"] * 100) if stats["total_stake"] > 0 else 0
            
            # Remover lista de picks para response mais limpa
            del stats["picks"]
        
        return performance
    
    async def _calculate_monthly_evolution(self, picks: List[PickPerformanceMetrics]) -> List[Dict]:
        """Calcula evolução mensal do portfólio"""
        
        # Agrupar por mês
        monthly_data = {}
        
        for pick in picks:
            month_key = pick.created_at.strftime("%Y-%m")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_key,
                    "picks": 0,
                    "won": 0,
                    "stake": 0,
                    "profit": 0
                }
            
            monthly_data[month_key]["picks"] += 1
            if pick.outcome == "won":
                monthly_data[month_key]["won"] += 1
            if pick.stake_actual:
                monthly_data[month_key]["stake"] += pick.stake_actual
            if pick.profit_loss:
                monthly_data[month_key]["profit"] += pick.profit_loss
        
        # Calcular métricas mensais
        evolution = []
        for month_data in sorted(monthly_data.values(), key=lambda x: x["month"]):
            month_data["win_rate"] = (month_data["won"] / month_data["picks"] * 100) if month_data["picks"] > 0 else 0
            month_data["roi"] = (month_data["profit"] / month_data["stake"] * 100) if month_data["stake"] > 0 else 0
            evolution.append(month_data)
        
        return evolution
    
    async def _generate_ai_insights(self, picks: List[PickPerformanceMetrics]) -> List[str]:
        """Gera insights IA baseados na performance"""
        
        insights = []
        
        if not picks:
            return ["Ainda não há dados suficientes para gerar insights."]
        
        settled_picks = [p for p in picks if p.outcome in ["won", "lost"]]
        
        if len(settled_picks) < 5:
            insights.append("📊 Você precisa de pelo menos 5 picks finalizados para insights precisos.")
            return insights
        
        # Análise de win rate
        win_rate = len([p for p in settled_picks if p.outcome == "won"]) / len(settled_picks) * 100
        
        if win_rate > 70:
            insights.append("🔥 Excelente taxa de acerto! Você está seguindo picks de alta qualidade.")
        elif win_rate > 55:
            insights.append("✅ Boa taxa de acerto! Continue seguindo nossas recomendações.")
        else:
            insights.append("⚠️ Taxa de acerto abaixo do esperado. Considere focar apenas em picks com EV+ > 10%.")
        
        # Análise de EV vs resultado
        high_ev_picks = [p for p in settled_picks if p.expected_value > 10]
        if high_ev_picks:
            high_ev_winrate = len([p for p in high_ev_picks if p.outcome == "won"]) / len(high_ev_picks) * 100
            insights.append(f"🎯 Picks com EV+ alto (>10%) têm {high_ev_winrate:.1f}% de acerto para você.")
        
        # Análise por esporte
        sport_performance = await self._calculate_performance_by_category(settled_picks, "sport")
        if len(sport_performance) > 1:
            best_sport = max(sport_performance.items(), key=lambda x: x[1]["win_rate"])
            insights.append(f"⚽ Seu melhor esporte é {best_sport[0]} com {best_sport[1]['win_rate']:.1f}% de acerto.")
        
        # Análise de stake
        stakes = [p.stake_actual for p in picks if p.stake_actual]
        if stakes:
            avg_stake = np.mean(stakes)
            if avg_stake > 100:
                insights.append("💰 Cuidado com stakes altos. Recomendamos máximo 5% da banca por pick.")
        
        return insights
    
    def _empty_analytics(self, user_id: str, timeframe: str) -> PortfolioAnalytics:
        """Retorna analytics vazios quando não há dados"""
        return PortfolioAnalytics(
            user_id=user_id,
            timeframe=timeframe,
            total_picks=0,
            settled_picks=0,
            pending_picks=0,
            win_rate=0.0,
            total_roi=0.0,
            total_stake=0.0,
            total_profit=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            longest_winning_streak=0,
            longest_losing_streak=0,
            avg_odds=0.0,
            avg_ev_recommended=0.0,
            performance_by_sport={},
            performance_by_market={},
            monthly_performance=[],
            ai_insights=["Comece seguindo nossos picks para gerar analytics!"]
        )
    
    # Métodos para analytics da plataforma (placeholder - implementar com queries reais)
    async def _count_picks_generated(self, start_date: datetime, end_date: datetime) -> int:
        return 250  # Simulação
    
    async def _calculate_platform_accuracy(self, start_date: datetime, end_date: datetime) -> float:
        return 67.5  # Simulação
    
    async def _calculate_ev_accuracy(self, start_date: datetime, end_date: datetime) -> float:
        return 73.2  # Simulação
    
    async def _get_platform_sport_performance(self, start_date: datetime, end_date: datetime) -> Dict:
        return {
            "football": {"accuracy": 68.5, "avg_ev": 9.2, "picks": 180},
            "basketball": {"accuracy": 65.1, "avg_ev": 7.8, "picks": 45},
            "cs2": {"accuracy": 71.2, "avg_ev": 11.5, "picks": 25}
        }
    
    async def _get_top_performing_markets(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        return [
            {"market": "Both Teams Score", "accuracy": 74.2, "avg_ev": 10.8},
            {"market": "Over/Under Goals", "accuracy": 69.5, "avg_ev": 8.9},
            {"market": "Asian Handicap", "accuracy": 66.3, "avg_ev": 12.1}
        ]
    
    async def _calculate_user_engagement_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        return {
            "daily_active_users": 450,
            "avg_picks_per_user": 8.3,
            "user_retention_7d": 78.5,
            "picks_followed_rate": 62.1
        } 