"""
Alert System - Sistema de Alertas para Oportunidades EV+
Notifica usuários quando surgem picks com Expected Value positivo
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Tipos de alerta"""
    EV_OPPORTUNITY = "ev_opportunity"       # Nova oportunidade EV+
    HIGH_CONFIDENCE = "high_confidence"     # Pick com confidence 8+
    HOT_STREAK = "hot_streak"              # Sequência de vitórias
    DEADLINE_WARNING = "deadline_warning"   # Pick expirando em breve
    MARKET_MOVEMENT = "market_movement"     # Mudança significativa de odds
    DAILY_SUMMARY = "daily_summary"        # Resumo diário

class AlertPriority(Enum):
    """Prioridade do alerta"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DeliveryMethod(Enum):
    """Métodos de entrega"""
    IN_APP = "in_app"           # Notificação no app
    PUSH = "push"               # Push notification
    EMAIL = "email"             # Email
    SMS = "sms"                 # SMS (premium)
    WEBHOOK = "webhook"         # Webhook (enterprise)

@dataclass
class AlertPreference:
    """Preferências de alerta do usuário"""
    user_id: str
    alert_type: AlertType
    enabled: bool
    min_ev: float               # EV mínimo para alertar
    min_confidence: float       # Confidence mínimo
    sports: List[str]           # Esportes de interesse
    delivery_methods: List[DeliveryMethod]
    quiet_hours_start: Optional[int]  # Hora início silêncio (0-23)
    quiet_hours_end: Optional[int]    # Hora fim silêncio (0-23)
    max_daily_alerts: int      # Máximo alertas por dia

@dataclass
class Alert:
    """Estrutura de um alerta"""
    id: str
    user_id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    data: Dict                  # Dados específicos do alerta
    created_at: datetime
    expires_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    delivery_status: Dict       # Status por método de entrega

class AlertSystem:
    """Sistema de alertas e notificações"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alert_templates = self._initialize_templates()
    
    async def create_ev_opportunity_alert(
        self,
        pick_data: Dict,
        target_users: Optional[List[str]] = None
    ) -> List[str]:
        """
        Cria alerta para nova oportunidade EV+
        """
        
        ev = pick_data.get("expected_value", 0)
        confidence = pick_data.get("confidence_score", 0)
        sport = pick_data.get("sport", "unknown")
        
        # Determinar prioridade baseada em EV e confidence
        if ev >= 15 and confidence >= 8.5:
            priority = AlertPriority.CRITICAL
        elif ev >= 10 and confidence >= 7.5:
            priority = AlertPriority.HIGH
        elif ev >= 6 and confidence >= 6.0:
            priority = AlertPriority.MEDIUM
        else:
            priority = AlertPriority.LOW
        
        # Buscar usuários interessados se não especificados
        if target_users is None:
            target_users = await self._get_interested_users(
                alert_type=AlertType.EV_OPPORTUNITY,
                sport=sport,
                min_ev=ev,
                min_confidence=confidence
            )
        
        alerts_created = []
        
        for user_id in target_users:
            # Verificar se pode enviar alerta
            can_send = await self._can_send_alert(user_id, AlertType.EV_OPPORTUNITY)
            if not can_send:
                continue
            
            # Criar alerta personalizado
            alert = Alert(
                id=f"ev_{pick_data['id']}_{user_id}_{int(datetime.now().timestamp())}",
                user_id=user_id,
                alert_type=AlertType.EV_OPPORTUNITY,
                priority=priority,
                title=self._generate_ev_title(pick_data, priority),
                message=self._generate_ev_message(pick_data),
                data={
                    "pick_id": pick_data["id"],
                    "sport": sport,
                    "ev": ev,
                    "confidence": confidence,
                    "selection": pick_data.get("selection", ""),
                    "match": f"{pick_data.get('home_team', '')} vs {pick_data.get('away_team', '')}",
                    "odds": pick_data.get("recommended_odds", 0),
                    "expires_at": pick_data.get("expires_at")
                },
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=6),  # Alerta expira em 6h
                delivered_at=None,
                read_at=None,
                delivery_status={}
            )
            
            # Salvar alerta
            await self._save_alert(alert)
            
            # Entregar alerta
            await self._deliver_alert(alert, user_id)
            
            alerts_created.append(alert.id)
        
        return alerts_created
    
    async def create_market_movement_alert(
        self,
        pick_id: str,
        old_odds: float,
        new_odds: float,
        movement_percentage: float
    ) -> List[str]:
        """
        Alerta para mudança significativa de odds
        """
        
        # Buscar usuários que têm interesse neste pick
        interested_users = await self._get_users_following_pick(pick_id)
        
        alerts_created = []
        
        for user_id in interested_users:
            # Determinar se movimento é favorável ou desfavorável
            is_favorable = new_odds > old_odds  # Odds maiores = melhor para usuário
            
            if is_favorable and movement_percentage >= 10:
                priority = AlertPriority.HIGH
                emoji = "📈"
                tone = "Oportunidade!"
            elif not is_favorable and movement_percentage >= 15:
                priority = AlertPriority.MEDIUM
                emoji = "📉"
                tone = "Atenção"
            else:
                continue  # Movimento não significativo
            
            alert = Alert(
                id=f"movement_{pick_id}_{user_id}_{int(datetime.now().timestamp())}",
                user_id=user_id,
                alert_type=AlertType.MARKET_MOVEMENT,
                priority=priority,
                title=f"{emoji} {tone} - Movimento de Odds",
                message=f"As odds mudaram de {old_odds:.2f} para {new_odds:.2f} ({movement_percentage:+.1f}%)",
                data={
                    "pick_id": pick_id,
                    "old_odds": old_odds,
                    "new_odds": new_odds,
                    "movement_percentage": movement_percentage,
                    "is_favorable": is_favorable
                },
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=2),
                delivered_at=None,
                read_at=None,
                delivery_status={}
            )
            
            await self._save_alert(alert)
            await self._deliver_alert(alert, user_id)
            alerts_created.append(alert.id)
        
        return alerts_created
    
    async def create_daily_summary_alert(self, user_id: str) -> Optional[str]:
        """
        Cria resumo diário personalizado para o usuário
        """
        
        # Buscar dados do usuário para personalizar
        user_stats = await self._get_user_daily_stats(user_id)
        user_prefs = await self._get_user_preferences(user_id, AlertType.DAILY_SUMMARY)
        
        if not user_prefs or not user_prefs.enabled:
            return None
        
        # Buscar picks do dia que o usuário pode estar interessado
        today_picks = await self._get_todays_picks_for_user(user_id)
        
        # Gerar resumo personalizado
        summary_data = {
            "date": datetime.now().strftime("%d/%m/%Y"),
            "total_picks_available": len(today_picks),
            "value_opportunities": len([p for p in today_picks if p.get("expected_value", 0) >= 5]),
            "high_confidence_picks": len([p for p in today_picks if p.get("confidence_score", 0) >= 8]),
            "user_performance": user_stats,
            "best_pick_today": max(today_picks, key=lambda x: x.get("expected_value", 0)) if today_picks else None,
            "recommended_focus": self._get_daily_focus_recommendation(today_picks)
        }
        
        alert = Alert(
            id=f"daily_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            user_id=user_id,
            alert_type=AlertType.DAILY_SUMMARY,
            priority=AlertPriority.LOW,
            title="📊 Seu Resumo Diário QuantumBet",
            message=self._generate_daily_summary_message(summary_data),
            data=summary_data,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            delivered_at=None,
            read_at=None,
            delivery_status={}
        )
        
        await self._save_alert(alert)
        await self._deliver_alert(alert, user_id)
        
        return alert.id
    
    async def get_user_alerts(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Alert]:
        """
        Busca alertas do usuário
        """
        
        # Simulação - em produção seria query no banco
        sample_alerts = [
            Alert(
                id="alert_001",
                user_id=user_id,
                alert_type=AlertType.EV_OPPORTUNITY,
                priority=AlertPriority.HIGH,
                title="🔥 Oportunidade EV+ 12.5%",
                message="Real Madrid vs Barcelona - Over 2.5 Goals com 12.5% de Expected Value",
                data={
                    "pick_id": "pick_001",
                    "sport": "football",
                    "ev": 12.5,
                    "confidence": 8.3,
                    "match": "Real Madrid vs Barcelona"
                },
                created_at=datetime.now() - timedelta(minutes=30),
                expires_at=datetime.now() + timedelta(hours=5),
                delivered_at=datetime.now() - timedelta(minutes=30),
                read_at=None if unread_only else datetime.now() - timedelta(minutes=15),
                delivery_status={"push": "delivered", "in_app": "delivered"}
            ),
            Alert(
                id="alert_002",
                user_id=user_id,
                alert_type=AlertType.HIGH_CONFIDENCE,
                priority=AlertPriority.MEDIUM,
                title="✅ Pick Alta Confiança - 9.1",
                message="Liverpool vs Arsenal - Both Teams Score com confiança 9.1/10",
                data={
                    "pick_id": "pick_002",
                    "sport": "football",
                    "confidence": 9.1,
                    "ev": 7.8
                },
                created_at=datetime.now() - timedelta(hours=2),
                expires_at=datetime.now() + timedelta(hours=3),
                delivered_at=datetime.now() - timedelta(hours=2),
                read_at=datetime.now() - timedelta(hours=1),
                delivery_status={"push": "delivered", "email": "delivered"}
            )
        ]
        
        if unread_only:
            sample_alerts = [a for a in sample_alerts if a.read_at is None]
        
        return sample_alerts[:limit]
    
    async def mark_alert_as_read(self, alert_id: str, user_id: str) -> bool:
        """
        Marca alerta como lido
        """
        
        # Simulação - em produção atualizaria banco
        # UPDATE alerts SET read_at = NOW() WHERE id = alert_id AND user_id = user_id
        
        return True
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: List[AlertPreference]
    ) -> Dict:
        """
        Atualiza preferências de alerta do usuário
        """
        
        saved_preferences = []
        
        for pref in preferences:
            # Validar preferência
            validation_result = self._validate_preference(pref)
            if not validation_result["valid"]:
                return {"error": f"Preferência inválida: {validation_result['error']}"}
            
            # Salvar preferência (simulação)
            await self._save_user_preference(pref)
            saved_preferences.append(pref.alert_type.value)
        
        return {
            "success": True,
            "updated_preferences": saved_preferences,
            "message": "Preferências de alerta atualizadas com sucesso"
        }
    
    async def get_alert_statistics(self, user_id: str, days: int = 30) -> Dict:
        """
        Estatísticas de alertas do usuário
        """
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Simular estatísticas
        return {
            "period": f"últimos_{days}_dias",
            "total_alerts_sent": 45,
            "alerts_read": 38,
            "read_rate": 84.4,
            "alerts_by_type": {
                "ev_opportunity": 25,
                "high_confidence": 12,
                "market_movement": 5,
                "daily_summary": 3
            },
            "avg_response_time": "4.2 minutos",
            "most_valuable_alert": {
                "type": "ev_opportunity",
                "ev": 18.5,
                "result": "won",
                "profit": 127.50
            },
            "delivery_success_rate": {
                "push": 98.2,
                "email": 94.1,
                "in_app": 100.0
            }
        }
    
    # Métodos auxiliares
    async def _get_interested_users(
        self,
        alert_type: AlertType,
        sport: str,
        min_ev: float,
        min_confidence: float
    ) -> List[str]:
        """Busca usuários interessados em receber este tipo de alerta"""
        
        # Simulação - em produção faria query complexa no banco
        # Buscar usuários com preferências que batem com os critérios
        
        return ["user_001", "user_002", "user_003"]  # Simulação
    
    async def _can_send_alert(self, user_id: str, alert_type: AlertType) -> bool:
        """Verifica se pode enviar alerta para o usuário"""
        
        # Verificar quiet hours
        current_hour = datetime.now().hour
        user_prefs = await self._get_user_preferences(user_id, alert_type)
        
        if user_prefs and user_prefs.quiet_hours_start and user_prefs.quiet_hours_end:
            if user_prefs.quiet_hours_start <= current_hour <= user_prefs.quiet_hours_end:
                return False
        
        # Verificar limite diário
        daily_count = await self._get_daily_alert_count(user_id)
        if user_prefs and daily_count >= user_prefs.max_daily_alerts:
            return False
        
        return True
    
    def _generate_ev_title(self, pick_data: Dict, priority: AlertPriority) -> str:
        """Gera título para alerta de EV+"""
        
        ev = pick_data.get("expected_value", 0)
        
        if priority == AlertPriority.CRITICAL:
            return f"🔥 OPORTUNIDADE EXCELENTE - EV+ {ev:.1f}%"
        elif priority == AlertPriority.HIGH:
            return f"⭐ OPORTUNIDADE EV+ {ev:.1f}%"
        else:
            return f"💡 Oportunidade EV+ {ev:.1f}%"
    
    def _generate_ev_message(self, pick_data: Dict) -> str:
        """Gera mensagem para alerta de EV+"""
        
        match = f"{pick_data.get('home_team', '')} vs {pick_data.get('away_team', '')}"
        selection = pick_data.get("selection", "")
        ev = pick_data.get("expected_value", 0)
        confidence = pick_data.get("confidence_score", 0)
        
        return f"{match} - {selection} com {ev:.1f}% de Expected Value e {confidence:.1f}/10 de confiança"
    
    def _generate_daily_summary_message(self, summary_data: Dict) -> str:
        """Gera mensagem do resumo diário"""
        
        total_picks = summary_data["total_picks_available"]
        value_opps = summary_data["value_opportunities"]
        
        message = f"📊 {total_picks} picks analisados hoje"
        
        if value_opps > 0:
            message += f", {value_opps} com EV+"
        
        if summary_data["best_pick_today"]:
            best_ev = summary_data["best_pick_today"]["expected_value"]
            message += f". Melhor oportunidade: {best_ev:.1f}% EV"
        
        return message
    
    async def _save_alert(self, alert: Alert):
        """Salva alerta no banco"""
        # Simulação - em produção salvaria no banco
        pass
    
    async def _deliver_alert(self, alert: Alert, user_id: str):
        """Entrega alerta pelos métodos configurados"""
        
        user_prefs = await self._get_user_preferences(user_id, alert.alert_type)
        
        if not user_prefs:
            return
        
        delivery_status = {}
        
        # Entregar por cada método configurado
        for method in user_prefs.delivery_methods:
            try:
                if method == DeliveryMethod.PUSH:
                    success = await self._send_push_notification(alert, user_id)
                elif method == DeliveryMethod.EMAIL:
                    success = await self._send_email(alert, user_id)
                elif method == DeliveryMethod.SMS:
                    success = await self._send_sms(alert, user_id)
                elif method == DeliveryMethod.IN_APP:
                    success = await self._save_in_app_notification(alert, user_id)
                else:
                    success = False
                
                delivery_status[method.value] = "delivered" if success else "failed"
                
            except Exception as e:
                logger.error(f"Erro ao entregar alerta {alert.id} via {method.value}: {e}")
                delivery_status[method.value] = "error"
        
        # Atualizar status de entrega
        alert.delivery_status = delivery_status
        alert.delivered_at = datetime.now()
        
        await self._update_alert_delivery_status(alert)
    
    # Métodos de entrega (simulações)
    async def _send_push_notification(self, alert: Alert, user_id: str) -> bool:
        logger.info(f"Enviando push para {user_id}: {alert.title}")
        return True
    
    async def _send_email(self, alert: Alert, user_id: str) -> bool:
        logger.info(f"Enviando email para {user_id}: {alert.title}")
        return True
    
    async def _send_sms(self, alert: Alert, user_id: str) -> bool:
        logger.info(f"Enviando SMS para {user_id}: {alert.title}")
        return True
    
    async def _save_in_app_notification(self, alert: Alert, user_id: str) -> bool:
        logger.info(f"Salvando notificação in-app para {user_id}")
        return True
    
    # Métodos auxiliares adicionais (simulações)
    async def _get_user_preferences(self, user_id: str, alert_type: AlertType) -> Optional[AlertPreference]:
        # Simulação de preferências do usuário
        return AlertPreference(
            user_id=user_id,
            alert_type=alert_type,
            enabled=True,
            min_ev=5.0,
            min_confidence=6.0,
            sports=["football", "basketball"],
            delivery_methods=[DeliveryMethod.PUSH, DeliveryMethod.IN_APP],
            quiet_hours_start=23,
            quiet_hours_end=7,
            max_daily_alerts=10
        )
    
    async def _get_daily_alert_count(self, user_id: str) -> int:
        return 3  # Simulação
    
    async def _get_users_following_pick(self, pick_id: str) -> List[str]:
        return ["user_001", "user_002"]  # Simulação
    
    async def _get_user_daily_stats(self, user_id: str) -> Dict:
        return {
            "picks_followed_today": 2,
            "current_roi": 8.5,
            "win_streak": 3
        }
    
    async def _get_todays_picks_for_user(self, user_id: str) -> List[Dict]:
        # Simulação de picks do dia para o usuário
        return [
            {"id": "pick_001", "expected_value": 12.5, "confidence_score": 8.3},
            {"id": "pick_002", "expected_value": 7.8, "confidence_score": 9.1}
        ]
    
    def _get_daily_focus_recommendation(self, picks: List[Dict]) -> str:
        """Gera recomendação de foco para o dia"""
        
        if not picks:
            return "Dia sem oportunidades claras - descanse ou estude!"
        
        high_ev_picks = [p for p in picks if p.get("expected_value", 0) >= 10]
        
        if len(high_ev_picks) >= 3:
            return "Dia excelente! Foque nos picks com maior EV"
        elif len(high_ev_picks) >= 1:
            return "Algumas boas oportunidades hoje"
        else:
            return "Dia conservador - apenas picks selecionados"
    
    def _validate_preference(self, pref: AlertPreference) -> Dict:
        """Valida preferência de alerta"""
        
        if pref.min_ev < 0 or pref.min_ev > 100:
            return {"valid": False, "error": "EV mínimo deve estar entre 0 e 100"}
        
        if pref.min_confidence < 0 or pref.min_confidence > 10:
            return {"valid": False, "error": "Confidence mínimo deve estar entre 0 e 10"}
        
        if pref.max_daily_alerts < 1 or pref.max_daily_alerts > 50:
            return {"valid": False, "error": "Máximo de alertas diários deve estar entre 1 e 50"}
        
        return {"valid": True}
    
    async def _save_user_preference(self, pref: AlertPreference):
        """Salva preferência do usuário"""
        # Simulação
        pass
    
    async def _update_alert_delivery_status(self, alert: Alert):
        """Atualiza status de entrega do alerta"""
        # Simulação
        pass
    
    def _initialize_templates(self) -> Dict:
        """Inicializa templates de alertas"""
        return {
            "ev_opportunity": {
                "title": "🎯 Nova Oportunidade EV+",
                "template": "{match} - {selection} com {ev}% de Expected Value"
            },
            "high_confidence": {
                "title": "✅ Pick Alta Confiança",
                "template": "{selection} com {confidence}/10 de confiança"
            }
        } 