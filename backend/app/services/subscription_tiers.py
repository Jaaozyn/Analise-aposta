"""
Subscription Tiers - Sistema de Assinaturas e Tiers
Modelo de negócio focado em análise e recomendações (não apostas)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SubscriptionTier(Enum):
    """Tiers de assinatura"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class BillingPeriod(Enum):
    """Períodos de cobrança"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"  # 3 meses
    ANNUAL = "annual"        # 12 meses

@dataclass
class TierFeatures:
    """Features de cada tier"""
    tier: SubscriptionTier
    name: str
    description: str
    price_monthly: float
    price_quarterly: float  # Com desconto
    price_annual: float     # Com desconto maior
    
    # Limites quantitativos
    picks_per_month: int
    ai_questions_per_month: int
    portfolio_tracking: bool
    historical_data_months: int
    
    # Features qualitativas
    confidence_threshold: float     # Confidence mínimo dos picks
    ev_threshold: float            # EV mínimo dos picks
    sports_available: List[str]
    markets_available: List[str]
    
    # Funcionalidades avançadas
    educational_content: bool
    priority_support: bool
    custom_alerts: bool
    advanced_analytics: bool
    api_access: bool
    multiple_users: int            # Quantos usuários (Enterprise)
    
    # Benefícios adicionais
    features_highlight: List[str]
    target_audience: str

@dataclass
class UserSubscription:
    """Assinatura do usuário"""
    user_id: str
    tier: SubscriptionTier
    billing_period: BillingPeriod
    price_paid: float
    started_at: datetime
    expires_at: datetime
    auto_renew: bool
    payment_method: str
    usage_stats: Dict
    last_payment: Optional[datetime]

class SubscriptionManager:
    """Gerenciador do sistema de assinaturas"""
    
    def __init__(self):
        self.tiers = self._initialize_tiers()
    
    def _initialize_tiers(self) -> Dict[SubscriptionTier, TierFeatures]:
        """Inicializa configuração dos tiers"""
        
        return {
            SubscriptionTier.FREE: TierFeatures(
                tier=SubscriptionTier.FREE,
                name="QuantumBet Free",
                description="Experimente nossas análises básicas",
                price_monthly=0.0,
                price_quarterly=0.0,
                price_annual=0.0,
                
                # Limites restritivos para incentivar upgrade
                picks_per_month=5,
                ai_questions_per_month=10,
                portfolio_tracking=False,
                historical_data_months=1,
                
                # Qualidade básica
                confidence_threshold=7.0,  # Apenas picks alta confiança
                ev_threshold=8.0,          # Apenas EV alto
                sports_available=["football"],
                markets_available=["match_result", "over_under"],
                
                # Features limitadas
                educational_content=True,   # Apenas conteúdo básico
                priority_support=False,
                custom_alerts=False,
                advanced_analytics=False,
                api_access=False,
                multiple_users=1,
                
                features_highlight=[
                    "5 picks premium por mês",
                    "Análises de futebol",
                    "Confidence 7+ apenas",
                    "Conteúdo educacional básico",
                    "Suporte via email"
                ],
                target_audience="Iniciantes que querem experimentar"
            ),
            
            SubscriptionTier.BASIC: TierFeatures(
                tier=SubscriptionTier.BASIC,
                name="QuantumBet Basic",
                description="Análises regulares para apostadores casuais",
                price_monthly=49.00,
                price_quarterly=129.00,    # 12% desconto
                price_annual=470.00,       # 20% desconto
                
                # Limites moderados
                picks_per_month=50,
                ai_questions_per_month=100,
                portfolio_tracking=True,
                historical_data_months=6,
                
                # Qualidade boa
                confidence_threshold=6.0,
                ev_threshold=5.0,
                sports_available=["football", "basketball"],
                markets_available=["match_result", "over_under", "both_teams_score", "handicap"],
                
                # Features intermediárias
                educational_content=True,
                priority_support=False,
                custom_alerts=True,
                advanced_analytics=False,
                api_access=False,
                multiple_users=1,
                
                features_highlight=[
                    "50 picks analisados por mês",
                    "Futebol + Basquete",
                    "Portfolio tracking completo",
                    "100 perguntas IA/mês",
                    "Alertas personalizados",
                    "6 meses de histórico"
                ],
                target_audience="Apostadores casuais e entusiastas"
            ),
            
            SubscriptionTier.PREMIUM: TierFeatures(
                tier=SubscriptionTier.PREMIUM,
                name="QuantumBet Premium",
                description="Análises ilimitadas para apostadores sérios",
                price_monthly=99.00,
                price_quarterly=267.00,    # 10% desconto
                price_annual=950.00,       # 20% desconto
                
                # Sem limites importantes
                picks_per_month=999,       # Praticamente ilimitado
                ai_questions_per_month=500,
                portfolio_tracking=True,
                historical_data_months=24,
                
                # Qualidade alta
                confidence_threshold=5.0,
                ev_threshold=3.0,
                sports_available=["football", "basketball", "cs2", "valorant"],
                markets_available=["match_result", "over_under", "both_teams_score", 
                                 "handicap", "correct_score", "first_half", "clean_sheet"],
                
                # Features avançadas
                educational_content=True,
                priority_support=True,
                custom_alerts=True,
                advanced_analytics=True,
                api_access=False,
                multiple_users=1,
                
                features_highlight=[
                    "Picks ilimitados",
                    "Todos os esportes",
                    "500 perguntas IA/mês",
                    "2 anos de histórico",
                    "Analytics avançados",
                    "Suporte prioritário",
                    "Todos os mercados"
                ],
                target_audience="Apostadores sérios e profissionais"
            ),
            
            SubscriptionTier.PROFESSIONAL: TierFeatures(
                tier=SubscriptionTier.PROFESSIONAL,
                name="QuantumBet Professional",
                description="Ferramenta completa para profissionais",
                price_monthly=149.00,
                price_quarterly=402.00,    # 10% desconto
                price_annual=1430.00,      # 20% desconto
                
                # Sem limites
                picks_per_month=999,
                ai_questions_per_month=1000,
                portfolio_tracking=True,
                historical_data_months=60,  # 5 anos
                
                # Qualidade máxima
                confidence_threshold=3.0,
                ev_threshold=1.0,
                sports_available=["football", "basketball", "cs2", "valorant", "tennis", "hockey"],
                markets_available=["all"],  # Todos os mercados
                
                # Todas as features
                educational_content=True,
                priority_support=True,
                custom_alerts=True,
                advanced_analytics=True,
                api_access=True,           # Acesso API
                multiple_users=1,
                
                features_highlight=[
                    "Acesso completo ilimitado",
                    "Todos esportes + mercados",
                    "1000 perguntas IA/mês",
                    "5 anos de histórico",
                    "API access completo",
                    "Suporte dedicado",
                    "Consultoria mensal",
                    "Confidence 3+ (mais picks)"
                ],
                target_audience="Traders profissionais e analistas"
            ),
            
            SubscriptionTier.ENTERPRISE: TierFeatures(
                tier=SubscriptionTier.ENTERPRISE,
                name="QuantumBet Enterprise",
                description="Solução corporativa para equipes e organizações",
                price_monthly=299.00,
                price_quarterly=807.00,    # 10% desconto
                price_annual=2870.00,      # 20% desconto
                
                # Limites corporativos
                picks_per_month=999,
                ai_questions_per_month=5000,
                portfolio_tracking=True,
                historical_data_months=120,  # 10 anos
                
                # Sem restrições
                confidence_threshold=0.0,  # Todos os picks
                ev_threshold=0.0,          # Incluindo EV negativos
                sports_available=["all"],
                markets_available=["all"],
                
                # Features enterprise
                educational_content=True,
                priority_support=True,
                custom_alerts=True,
                advanced_analytics=True,
                api_access=True,
                multiple_users=10,         # Até 10 usuários
                
                features_highlight=[
                    "Até 10 usuários",
                    "5000 perguntas IA/mês",
                    "10 anos de dados históricos",
                    "API enterprise ilimitada",
                    "White-label option",
                    "SLA 99.9% uptime",
                    "Suporte 24/7",
                    "Consultoria semanal",
                    "Custom features"
                ],
                target_audience="Empresas, fundos e organizações"
            )
        }
    
    def get_tier_features(self, tier: SubscriptionTier) -> TierFeatures:
        """Retorna features de um tier específico"""
        return self.tiers[tier]
    
    def get_all_tiers(self) -> List[TierFeatures]:
        """Retorna todos os tiers disponíveis"""
        return list(self.tiers.values())
    
    def calculate_price(
        self, 
        tier: SubscriptionTier, 
        billing_period: BillingPeriod,
        discount_code: Optional[str] = None
    ) -> Dict:
        """Calcula preço final com descontos"""
        
        tier_features = self.tiers[tier]
        
        if billing_period == BillingPeriod.MONTHLY:
            base_price = tier_features.price_monthly
            discount_text = "Sem desconto"
        elif billing_period == BillingPeriod.QUARTERLY:
            base_price = tier_features.price_quarterly
            monthly_equivalent = base_price / 3
            monthly_saved = tier_features.price_monthly - monthly_equivalent
            discount_text = f"Economize R$ {monthly_saved:.2f}/mês"
        else:  # ANNUAL
            base_price = tier_features.price_annual
            monthly_equivalent = base_price / 12
            monthly_saved = tier_features.price_monthly - monthly_equivalent
            discount_text = f"Economize R$ {monthly_saved:.2f}/mês"
        
        # Aplicar código de desconto se fornecido
        additional_discount = 0
        if discount_code:
            additional_discount = self._apply_discount_code(discount_code, base_price)
        
        final_price = base_price - additional_discount
        
        return {
            "tier": tier.value,
            "billing_period": billing_period.value,
            "base_price": base_price,
            "additional_discount": additional_discount,
            "final_price": final_price,
            "discount_text": discount_text,
            "savings_vs_monthly": (tier_features.price_monthly * 
                                 (3 if billing_period == BillingPeriod.QUARTERLY else 12)) - base_price
            if billing_period != BillingPeriod.MONTHLY else 0
        }
    
    def check_feature_access(self, user_subscription: UserSubscription, feature: str) -> Dict:
        """Verifica se usuário tem acesso a uma feature específica"""
        
        tier_features = self.tiers[user_subscription.tier]
        current_usage = user_subscription.usage_stats
        
        # Verificar limites de uso
        if feature == "picks_generation":
            used = current_usage.get("picks_this_month", 0)
            limit = tier_features.picks_per_month
            has_access = used < limit
            remaining = max(0, limit - used)
            
            return {
                "has_access": has_access,
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "message": f"Você usou {used}/{limit} picks este mês" if not has_access 
                          else f"{remaining} picks restantes este mês"
            }
        
        elif feature == "ai_questions":
            used = current_usage.get("ai_questions_this_month", 0)
            limit = tier_features.ai_questions_per_month
            has_access = used < limit
            remaining = max(0, limit - used)
            
            return {
                "has_access": has_access,
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "message": f"Você usou {used}/{limit} perguntas IA este mês"
            }
        
        elif feature == "portfolio_tracking":
            return {
                "has_access": tier_features.portfolio_tracking,
                "message": "Portfolio tracking disponível" if tier_features.portfolio_tracking 
                          else "Upgrade para Basic+ para portfolio tracking"
            }
        
        elif feature == "advanced_analytics":
            return {
                "has_access": tier_features.advanced_analytics,
                "message": "Analytics avançados disponíveis" if tier_features.advanced_analytics
                          else "Upgrade para Premium+ para analytics avançados"
            }
        
        elif feature == "api_access":
            return {
                "has_access": tier_features.api_access,
                "message": "API access disponível" if tier_features.api_access
                          else "Upgrade para Professional+ para API access"
            }
        
        else:
            return {"has_access": False, "message": "Feature não reconhecida"}
    
    def get_upgrade_recommendations(self, user_subscription: UserSubscription) -> List[Dict]:
        """Sugere upgrades baseado no uso"""
        
        current_tier = user_subscription.tier
        current_usage = user_subscription.usage_stats
        recommendations = []
        
        # Verificar se está atingindo limites
        tier_features = self.tiers[current_tier]
        
        # Limite de picks
        picks_usage = current_usage.get("picks_this_month", 0)
        if picks_usage >= tier_features.picks_per_month * 0.8:  # 80% do limite
            next_tier = self._get_next_tier(current_tier)
            if next_tier:
                next_features = self.tiers[next_tier]
                recommendations.append({
                    "reason": "limite_picks",
                    "message": f"Você está usando {picks_usage}/{tier_features.picks_per_month} picks. "
                              f"Upgrade para {next_features.name} e tenha {next_features.picks_per_month} picks/mês",
                    "suggested_tier": next_tier.value,
                    "benefit": f"+{next_features.picks_per_month - tier_features.picks_per_month} picks/mês"
                })
        
        # Limite de IA
        ai_usage = current_usage.get("ai_questions_this_month", 0)
        if ai_usage >= tier_features.ai_questions_per_month * 0.8:
            next_tier = self._get_next_tier(current_tier)
            if next_tier:
                next_features = self.tiers[next_tier]
                recommendations.append({
                    "reason": "limite_ai",
                    "message": f"Você está usando {ai_usage}/{tier_features.ai_questions_per_month} perguntas IA. "
                              f"Upgrade para ter {next_features.ai_questions_per_month} perguntas/mês",
                    "suggested_tier": next_tier.value,
                    "benefit": f"+{next_features.ai_questions_per_month - tier_features.ai_questions_per_month} perguntas IA/mês"
                })
        
        # Features não disponíveis
        if not tier_features.advanced_analytics and current_usage.get("analytics_requests", 0) > 5:
            recommendations.append({
                "reason": "analytics_avancados",
                "message": "Você tem interesse em analytics. Upgrade para Premium e tenha acesso completo",
                "suggested_tier": SubscriptionTier.PREMIUM.value,
                "benefit": "Analytics avançados, backtesting, performance tracking"
            })
        
        return recommendations
    
    def simulate_usage_projection(self, user_subscription: UserSubscription, months: int = 3) -> Dict:
        """Projeta uso futuro baseado no padrão atual"""
        
        current_usage = user_subscription.usage_stats
        tier_features = self.tiers[user_subscription.tier]
        
        # Calcular médias mensais
        avg_picks = current_usage.get("picks_this_month", 0)
        avg_ai_questions = current_usage.get("ai_questions_this_month", 0)
        
        # Projetar crescimento (assumir 10% crescimento mensal)
        growth_rate = 1.1
        
        projected_usage = []
        for month in range(1, months + 1):
            projected_picks = int(avg_picks * (growth_rate ** month))
            projected_ai = int(avg_ai_questions * (growth_rate ** month))
            
            # Verificar se vai exceder limites
            will_exceed_picks = projected_picks > tier_features.picks_per_month
            will_exceed_ai = projected_ai > tier_features.ai_questions_per_month
            
            projected_usage.append({
                "month": month,
                "projected_picks": projected_picks,
                "projected_ai_questions": projected_ai,
                "will_exceed_picks_limit": will_exceed_picks,
                "will_exceed_ai_limit": will_exceed_ai,
                "recommended_action": "upgrade" if (will_exceed_picks or will_exceed_ai) else "stay"
            })
        
        return {
            "current_tier": user_subscription.tier.value,
            "projection_months": months,
            "projected_usage": projected_usage,
            "upgrade_recommendation": any(month["recommended_action"] == "upgrade" for month in projected_usage)
        }
    
    def _apply_discount_code(self, code: str, base_price: float) -> float:
        """Aplica código de desconto"""
        
        discount_codes = {
            "WELCOME10": 0.10,     # 10% desconto
            "SAVE20": 0.20,        # 20% desconto
            "STUDENT": 0.30,       # 30% desconto estudante
            "ANNUAL50": 0.50       # 50% primeiro ano
        }
        
        if code in discount_codes:
            return base_price * discount_codes[code]
        
        return 0
    
    def _get_next_tier(self, current_tier: SubscriptionTier) -> Optional[SubscriptionTier]:
        """Retorna próximo tier na hierarquia"""
        
        tier_hierarchy = [
            SubscriptionTier.FREE,
            SubscriptionTier.BASIC,
            SubscriptionTier.PREMIUM,
            SubscriptionTier.PROFESSIONAL,
            SubscriptionTier.ENTERPRISE
        ]
        
        try:
            current_index = tier_hierarchy.index(current_tier)
            if current_index < len(tier_hierarchy) - 1:
                return tier_hierarchy[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    def get_tier_comparison(self) -> Dict:
        """Retorna comparação entre todos os tiers"""
        
        comparison = {
            "tiers": [],
            "features_comparison": {
                "picks_per_month": {},
                "ai_questions_per_month": {},
                "sports_available": {},
                "historical_data": {},
                "key_features": {}
            }
        }
        
        for tier, features in self.tiers.items():
            tier_info = {
                "tier": tier.value,
                "name": features.name,
                "price_monthly": features.price_monthly,
                "price_annual": features.price_annual,
                "target_audience": features.target_audience,
                "highlights": features.features_highlight[:3]  # Top 3 features
            }
            comparison["tiers"].append(tier_info)
            
            # Preencher comparação de features
            comparison["features_comparison"]["picks_per_month"][tier.value] = features.picks_per_month
            comparison["features_comparison"]["ai_questions_per_month"][tier.value] = features.ai_questions_per_month
            comparison["features_comparison"]["sports_available"][tier.value] = len(features.sports_available)
            comparison["features_comparison"]["historical_data"][tier.value] = features.historical_data_months
            
            key_features = []
            if features.portfolio_tracking:
                key_features.append("Portfolio Tracking")
            if features.advanced_analytics:
                key_features.append("Analytics Avançados")
            if features.api_access:
                key_features.append("API Access")
            if features.multiple_users > 1:
                key_features.append(f"{features.multiple_users} Usuários")
            
            comparison["features_comparison"]["key_features"][tier.value] = key_features
        
        return comparison 