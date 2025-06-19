"""
Performance Tracker - Sistema de Tracking de Performance das Recomendações
Permite usuários informarem resultados e acompanharem performance
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class PickOutcome(Enum):
    """Possíveis resultados de um pick"""
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"  # Jogo cancelado/adiado
    HALF_WON = "half_won"  # Handicap asiático
    HALF_LOST = "half_lost"

@dataclass
class UserPickResult:
    """Resultado de um pick informado pelo usuário"""
    user_id: str
    pick_id: str
    outcome: PickOutcome
    odds_achieved: float
    stake_amount: float
    profit_loss: float
    notes: Optional[str]
    reported_at: datetime

@dataclass
class PerformanceSnapshot:
    """Snapshot de performance do usuário"""
    user_id: str
    total_picks: int
    settled_picks: int
    won_picks: int
    total_stake: float
    total_profit: float
    win_rate: float
    roi: float
    best_streak: int
    current_streak: int
    last_updated: datetime

class PerformanceTracker:
    """Sistema de tracking de performance"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def report_pick_result(
        self,
        user_id: str,
        pick_id: str,
        outcome: str,
        odds_achieved: float,
        stake_amount: float,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Usuário reporta resultado de um pick
        """
        
        try:
            # Validar outcome
            if outcome not in [e.value for e in PickOutcome]:
                return {"error": "Outcome inválido"}
            
            # Validar se pick existe e pertence ao usuário
            pick_exists = await self._validate_pick_access(user_id, pick_id)
            if not pick_exists:
                return {"error": "Pick não encontrado ou sem acesso"}
            
            # Calcular profit/loss
            profit_loss = self._calculate_profit_loss(outcome, odds_achieved, stake_amount)
            
            # Salvar resultado
            result = UserPickResult(
                user_id=user_id,
                pick_id=pick_id,
                outcome=PickOutcome(outcome),
                odds_achieved=odds_achieved,
                stake_amount=stake_amount,
                profit_loss=profit_loss,
                notes=notes,
                reported_at=datetime.now()
            )
            
            # Salvar no banco (simulação)
            await self._save_pick_result(result)
            
            # Atualizar performance do usuário
            await self._update_user_performance(user_id)
            
            # Gerar insights
            insights = await self._generate_result_insights(result)
            
            return {
                "success": True,
                "result": {
                    "pick_id": pick_id,
                    "outcome": outcome,
                    "profit_loss": profit_loss,
                    "roi_this_pick": ((profit_loss / stake_amount) * 100) if stake_amount > 0 else 0
                },
                "insights": insights,
                "updated_performance": await self.get_user_performance_snapshot(user_id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao reportar resultado: {e}")
            return {"error": "Erro interno"}
    
    async def get_user_performance_snapshot(self, user_id: str) -> PerformanceSnapshot:
        """
        Retorna snapshot atual da performance do usuário
        """
        
        # Buscar todos os resultados do usuário (simulação)
        user_results = await self._get_user_results(user_id)
        
        if not user_results:
            return PerformanceSnapshot(
                user_id=user_id,
                total_picks=0,
                settled_picks=0,
                won_picks=0,
                total_stake=0.0,
                total_profit=0.0,
                win_rate=0.0,
                roi=0.0,
                best_streak=0,
                current_streak=0,
                last_updated=datetime.now()
            )
        
        # Calcular métricas
        total_picks = len(user_results)
        settled_results = [r for r in user_results if r.outcome not in [PickOutcome.PENDING]]
        settled_picks = len(settled_results)
        won_picks = len([r for r in settled_results if r.outcome == PickOutcome.WON])
        
        total_stake = sum(r.stake_amount for r in settled_results)
        total_profit = sum(r.profit_loss for r in settled_results)
        
        win_rate = (won_picks / settled_picks * 100) if settled_picks > 0 else 0
        roi = (total_profit / total_stake * 100) if total_stake > 0 else 0
        
        # Calcular streaks
        streaks = self._calculate_streaks(settled_results)
        
        return PerformanceSnapshot(
            user_id=user_id,
            total_picks=total_picks,
            settled_picks=settled_picks,
            won_picks=won_picks,
            total_stake=total_stake,
            total_profit=total_profit,
            win_rate=win_rate,
            roi=roi,
            best_streak=streaks["best"],
            current_streak=streaks["current"],
            last_updated=datetime.now()
        )
    
    async def get_detailed_performance_history(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict:
        """
        Histórico detalhado de performance
        """
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Buscar resultados do período
        results = await self._get_user_results_period(user_id, start_date, end_date)
        
        # Agrupar por data
        daily_performance = {}
        cumulative_profit = 0
        
        for result in sorted(results, key=lambda x: x.reported_at):
            date_key = result.reported_at.strftime("%Y-%m-%d")
            
            if date_key not in daily_performance:
                daily_performance[date_key] = {
                    "date": date_key,
                    "picks": 0,
                    "won": 0,
                    "stake": 0,
                    "profit": 0
                }
            
            daily_performance[date_key]["picks"] += 1
            if result.outcome == PickOutcome.WON:
                daily_performance[date_key]["won"] += 1
            
            daily_performance[date_key]["stake"] += result.stake_amount
            daily_performance[date_key]["profit"] += result.profit_loss
            
            cumulative_profit += result.profit_loss
        
        # Calcular métricas diárias
        performance_history = []
        for day_data in daily_performance.values():
            day_data["win_rate"] = (day_data["won"] / day_data["picks"] * 100) if day_data["picks"] > 0 else 0
            day_data["roi"] = (day_data["profit"] / day_data["stake"] * 100) if day_data["stake"] > 0 else 0
            performance_history.append(day_data)
        
        # Performance por esporte
        sport_performance = await self._calculate_sport_performance(results)
        
        # Melhores picks do período
        best_picks = sorted(
            [r for r in results if r.profit_loss > 0],
            key=lambda x: x.profit_loss,
            reverse=True
        )[:5]
        
        return {
            "period": f"últimos_{days}_dias",
            "summary": await self.get_user_performance_snapshot(user_id),
            "daily_history": performance_history,
            "sport_performance": sport_performance,
            "best_picks": [
                {
                    "pick_id": pick.pick_id,
                    "profit": pick.profit_loss,
                    "roi": (pick.profit_loss / pick.stake_amount * 100),
                    "odds": pick.odds_achieved,
                    "date": pick.reported_at.strftime("%Y-%m-%d")
                }
                for pick in best_picks
            ],
            "insights": await self._generate_period_insights(results)
        }
    
    async def bulk_import_results(self, user_id: str, results_data: List[Dict]) -> Dict:
        """
        Importação em lote de resultados (para usuários que já têm histórico)
        """
        
        imported = 0
        errors = []
        
        for data in results_data:
            try:
                result = await self.report_pick_result(
                    user_id=user_id,
                    pick_id=data["pick_id"],
                    outcome=data["outcome"],
                    odds_achieved=data["odds_achieved"],
                    stake_amount=data["stake_amount"],
                    notes=data.get("notes")
                )
                
                if result.get("success"):
                    imported += 1
                else:
                    errors.append(f"Pick {data['pick_id']}: {result.get('error')}")
                    
            except Exception as e:
                errors.append(f"Pick {data.get('pick_id', 'unknown')}: {str(e)}")
        
        return {
            "imported": imported,
            "total": len(results_data),
            "errors": errors[:10],  # Máximo 10 erros
            "success_rate": (imported / len(results_data) * 100) if results_data else 0
        }
    
    def _calculate_profit_loss(self, outcome: str, odds: float, stake: float) -> float:
        """Calcula profit/loss baseado no resultado"""
        
        if outcome == "won":
            return stake * (odds - 1)  # Lucro
        elif outcome == "lost":
            return -stake  # Prejuízo total
        elif outcome == "void":
            return 0  # Stake devolvido
        elif outcome == "half_won":
            return stake * (odds - 1) / 2  # Meio lucro
        elif outcome == "half_lost":
            return -stake / 2  # Meio prejuízo
        else:
            return 0
    
    def _calculate_streaks(self, results: List[UserPickResult]) -> Dict:
        """Calcula streaks de vitórias"""
        
        if not results:
            return {"best": 0, "current": 0}
        
        # Ordenar por data
        sorted_results = sorted(results, key=lambda x: x.reported_at)
        
        best_streak = 0
        current_streak = 0
        
        for result in sorted_results:
            if result.outcome == PickOutcome.WON:
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 0
        
        return {"best": best_streak, "current": current_streak}
    
    async def _validate_pick_access(self, user_id: str, pick_id: str) -> bool:
        """Valida se usuário tem acesso ao pick"""
        # Simulação - em produção verificaria no banco
        return True
    
    async def _save_pick_result(self, result: UserPickResult):
        """Salva resultado no banco"""
        # Simulação - em produção salvaria no banco
        pass
    
    async def _update_user_performance(self, user_id: str):
        """Atualiza cache de performance do usuário"""
        # Simulação - em produção atualizaria cache
        pass
    
    async def _get_user_results(self, user_id: str) -> List[UserPickResult]:
        """Busca todos os resultados do usuário"""
        # Simulação de dados
        return [
            UserPickResult(
                user_id=user_id,
                pick_id="pick_001",
                outcome=PickOutcome.WON,
                odds_achieved=1.80,
                stake_amount=50.0,
                profit_loss=40.0,
                notes="Ótimo pick!",
                reported_at=datetime.now() - timedelta(days=5)
            ),
            UserPickResult(
                user_id=user_id,
                pick_id="pick_002",
                outcome=PickOutcome.LOST,
                odds_achieved=2.05,
                stake_amount=30.0,
                profit_loss=-30.0,
                notes=None,
                reported_at=datetime.now() - timedelta(days=3)
            ),
            UserPickResult(
                user_id=user_id,
                pick_id="pick_003",
                outcome=PickOutcome.WON,
                odds_achieved=1.70,
                stake_amount=40.0,
                profit_loss=28.0,
                notes="Seguiu recomendação corretamente",
                reported_at=datetime.now() - timedelta(days=1)
            )
        ]
    
    async def _get_user_results_period(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UserPickResult]:
        """Busca resultados de um período específico"""
        all_results = await self._get_user_results(user_id)
        return [r for r in all_results if start_date <= r.reported_at <= end_date]
    
    async def _calculate_sport_performance(self, results: List[UserPickResult]) -> Dict:
        """Calcula performance por esporte"""
        # Simulação - em produção buscaria dados do pick para identificar esporte
        return {
            "football": {"picks": 8, "won": 6, "win_rate": 75.0, "roi": 15.5},
            "basketball": {"picks": 3, "won": 1, "win_rate": 33.3, "roi": -12.2},
            "cs2": {"picks": 2, "won": 2, "win_rate": 100.0, "roi": 28.0}
        }
    
    async def _generate_result_insights(self, result: UserPickResult) -> List[str]:
        """Gera insights baseados no resultado reportado"""
        
        insights = []
        
        if result.outcome == PickOutcome.WON:
            roi = (result.profit_loss / result.stake_amount) * 100
            insights.append(f"🎉 Parabéns! ROI de {roi:.1f}% neste pick.")
            
            if roi > 50:
                insights.append("🔥 ROI excelente! Continue seguindo picks com EV+ alto.")
        
        elif result.outcome == PickOutcome.LOST:
            insights.append("📉 Pick não deu certo desta vez. Faz parte do jogo!")
            insights.append("💡 Lembre-se: foque no longo prazo e mantenha disciplina.")
        
        # Verificar stake management
        if result.stake_amount > 100:
            insights.append("⚠️ Stake alto. Recomendamos máximo 5% da banca por pick.")
        
        return insights
    
    async def _generate_period_insights(self, results: List[UserPickResult]) -> List[str]:
        """Gera insights para um período"""
        
        if not results:
            return ["Nenhum resultado reportado no período."]
        
        insights = []
        
        # Análise geral
        won = len([r for r in results if r.outcome == PickOutcome.WON])
        total = len(results)
        win_rate = (won / total) * 100
        
        if win_rate > 60:
            insights.append(f"📈 Excelente período! {win_rate:.1f}% de acerto.")
        elif win_rate > 50:
            insights.append(f"✅ Bom período com {win_rate:.1f}% de acerto.")
        else:
            insights.append(f"📊 Taxa de {win_rate:.1f}%. Foque em picks com maior EV+.")
        
        # Análise de profit
        total_profit = sum(r.profit_loss for r in results)
        if total_profit > 0:
            insights.append(f"💰 Lucro total: R$ {total_profit:.2f}")
        else:
            insights.append(f"📉 Prejuízo no período: R$ {abs(total_profit):.2f}")
        
        return insights 