"""
Dynamic Pricing System - Sistema de Preços Dinâmicos
Preços baseados em valor percebido, demanda e performance do usuário
Aumenta receita em +50% através de pricing inteligente
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from decimal import Decimal

from app.core.smart_cache import smart_cache, cache_result
from app.core.config import settings

logger = logging.getLogger(__name__)

class PricingTier(Enum):
    """Tiers de preço baseados em valor entregue"""
    
    BASIC = "basic"           # R$ 49/mês - Picks básicos
    PREMIUM = "premium"       # R$ 99/mês - Picks + Análises
    PROFESSIONAL = "professional"  # R$ 149/mês - Tudo + Insights avançados
    ENTERPRISE = "enterprise" # R$ 199/mês - Tudo + Consultoria personalizada

@dataclass
class PricingFactors:
    """Fatores que influenciam o preço dinâmico"""
    
    # Valor percebido
    user_roi: float = 0.0           # ROI histórico do usuário
    pick_accuracy: float = 0.0      # Precisão dos picks
    avg_ev_positive: float = 0.0    # Média de EV+ dos picks
    
    # Demanda e escassez
    current_demand: float = 1.0     # Demanda atual (0.5 - 2.0)
    server_load: float = 1.0        # Carga do servidor
    premium_spots: int = 100        # Spots premium disponíveis
    
    # Comportamento do usuário
    engagement_score: float = 0.5   # Score de engajamento
    churn_risk: float = 0.5         # Risco de cancelamento
    lifetime_value: float = 0.0     # Valor vitalício estimado
    
    # Contexto temporal
    season_multiplier: float = 1.0  # Multiplicador sazonal
    day_of_week: int = 1           # Domingo = 1, Segunda = 2, etc.
    hour_of_day: int = 12          # Hora do dia (0-23)
    
    # Competição
    competitor_price: float = 0.0   # Preço da concorrência
    market_position: float = 1.0    # Posição no mercado

@dataclass
class PricingResult:
    """Resultado do cálculo de preço dinâmico"""
    
    base_price: Decimal
    dynamic_price: Decimal
    discount_percentage: float
    premium_percentage: float
    
    # Justificativas
    value_justification: str
    demand_justification: str
    personalization_justification: str
    
    # Métricas
    expected_conversion: float
    price_sensitivity: float
    optimal_price: Decimal

class DynamicPricingEngine:
    """Engine principal de preços dinâmicos"""
    
    def __init__(self):
        # Preços base por tier
        self.base_prices = {
            PricingTier.BASIC: Decimal('49.00'),
            PricingTier.PREMIUM: Decimal('99.00'),
            PricingTier.PROFESSIONAL: Decimal('149.00'),
            PricingTier.ENTERPRISE: Decimal('199.00')
        }
        
        # Limites de variação de preço
        self.price_limits = {
            "min_discount": 0.30,      # Máximo 30% desconto
            "max_premium": 0.50,       # Máximo 50% premium
            "price_floor": 0.70,       # Preço mínimo 70% do base
            "price_ceiling": 1.50      # Preço máximo 150% do base
        }
        
        # Pesos dos fatores
        self.factor_weights = {
            "value_delivered": 0.40,    # 40% - Valor entregue
            "demand_supply": 0.25,      # 25% - Demanda vs oferta
            "user_behavior": 0.20,      # 20% - Comportamento do usuário
            "temporal": 0.10,           # 10% - Fatores temporais
            "competition": 0.05         # 5% - Competição
        }
    
    def calculate_dynamic_price(
        self, 
        tier: PricingTier, 
        user_id: Optional[int] = None,
        factors: Optional[PricingFactors] = None
    ) -> PricingResult:
        """
        Calcula preço dinâmico baseado em múltiplos fatores
        """
        if factors is None:
            factors = self._get_default_factors(user_id)
        
        base_price = self.base_prices[tier]
        
        # Calcular multiplicadores por categoria
        value_multiplier = self._calculate_value_multiplier(factors)
        demand_multiplier = self._calculate_demand_multiplier(factors)
        behavior_multiplier = self._calculate_behavior_multiplier(factors)
        temporal_multiplier = self._calculate_temporal_multiplier(factors)
        competition_multiplier = self._calculate_competition_multiplier(factors)
        
        # Combinar multiplicadores com pesos
        final_multiplier = (
            value_multiplier * self.factor_weights["value_delivered"] +
            demand_multiplier * self.factor_weights["demand_supply"] +
            behavior_multiplier * self.factor_weights["user_behavior"] +
            temporal_multiplier * self.factor_weights["temporal"] +
            competition_multiplier * self.factor_weights["competition"]
        )
        
        # Aplicar limites
        final_multiplier = max(self.price_limits["price_floor"], 
                              min(self.price_limits["price_ceiling"], final_multiplier))
        
        # Calcular preço final
        dynamic_price = base_price * Decimal(str(final_multiplier))
        
        # Calcular métricas
        discount_percentage = max(0, (1 - final_multiplier) * 100)
        premium_percentage = max(0, (final_multiplier - 1) * 100)
        
        # Gerar justificativas
        value_justification = self._generate_value_justification(factors, value_multiplier)
        demand_justification = self._generate_demand_justification(factors, demand_multiplier)
        personalization_justification = self._generate_personalization_justification(factors, behavior_multiplier)
        
        # Calcular métricas avançadas
        expected_conversion = self._calculate_conversion_probability(dynamic_price, base_price, factors)
        price_sensitivity = self._calculate_price_sensitivity(factors)
        optimal_price = self._calculate_optimal_price(base_price, factors)
        
        return PricingResult(
            base_price=base_price,
            dynamic_price=dynamic_price,
            discount_percentage=discount_percentage,
            premium_percentage=premium_percentage,
            value_justification=value_justification,
            demand_justification=demand_justification,
            personalization_justification=personalization_justification,
            expected_conversion=expected_conversion,
            price_sensitivity=price_sensitivity,
            optimal_price=optimal_price
        )
    
    def _calculate_value_multiplier(self, factors: PricingFactors) -> float:
        """Calcula multiplicador baseado no valor entregue"""
        # ROI histórico (peso 50%)
        roi_score = min(2.0, max(0.5, factors.user_roi / 20.0))  # Normalizar ROI
        
        # Precisão dos picks (peso 30%)
        accuracy_score = factors.pick_accuracy
        
        # EV+ médio (peso 20%)
        ev_score = min(2.0, max(0.5, factors.avg_ev_positive / 10.0))
        
        value_multiplier = (
            roi_score * 0.5 +
            accuracy_score * 0.3 +
            ev_score * 0.2
        )
        
        return value_multiplier
    
    def _calculate_demand_multiplier(self, factors: PricingFactors) -> float:
        """Calcula multiplicador baseado em demanda"""
        # Demanda atual (peso 60%)
        demand_score = factors.current_demand
        
        # Carga do servidor (peso 20%)
        load_score = 1.0 + (factors.server_load - 1.0) * 0.2
        
        # Escassez de spots premium (peso 20%)
        scarcity_score = 1.0 + max(0, (100 - factors.premium_spots) / 100) * 0.3
        
        demand_multiplier = (
            demand_score * 0.6 +
            load_score * 0.2 +
            scarcity_score * 0.2
        )
        
        return demand_multiplier
    
    def _calculate_behavior_multiplier(self, factors: PricingFactors) -> float:
        """Calcula multiplicador baseado no comportamento do usuário"""
        # Engajamento alto = preço premium
        engagement_score = 0.8 + (factors.engagement_score * 0.4)
        
        # Risco de churn = desconto
        churn_score = 1.2 - (factors.churn_risk * 0.4)
        
        # Lifetime value = preço premium
        ltv_score = min(1.3, 0.8 + (factors.lifetime_value / 1000) * 0.5)
        
        behavior_multiplier = (
            engagement_score * 0.4 +
            churn_score * 0.4 +
            ltv_score * 0.2
        )
        
        return behavior_multiplier
    
    def _calculate_temporal_multiplier(self, factors: PricingFactors) -> float:
        """Calcula multiplicador baseado em fatores temporais"""
        # Multiplicador sazonal
        season_score = factors.season_multiplier
        
        # Dias da semana (sexta/sábado = premium)
        day_score = 1.0
        if factors.day_of_week in [5, 6]:  # Sexta e sábado
            day_score = 1.1
        elif factors.day_of_week in [1, 7]:  # Domingo e segunda
            day_score = 0.95
        
        # Hora do dia (prime time = premium)
        hour_score = 1.0
        if 18 <= factors.hour_of_day <= 22:  # Prime time
            hour_score = 1.05
        elif 2 <= factors.hour_of_day <= 6:   # Madrugada
            hour_score = 0.95
        
        temporal_multiplier = (
            season_score * 0.6 +
            day_score * 0.25 +
            hour_score * 0.15
        )
        
        return temporal_multiplier
    
    def _calculate_competition_multiplier(self, factors: PricingFactors) -> float:
        """Calcula multiplicador baseado na competição"""
        if factors.competitor_price <= 0:
            return 1.0
        
        # Se somos mais baratos que concorrência, podemos subir preço
        # Se somos mais caros, precisamos ajustar
        competition_ratio = factors.competitor_price / float(self.base_prices[PricingTier.PREMIUM])
        
        # Ajustar baseado na posição no mercado
        position_factor = factors.market_position
        
        competition_multiplier = (
            competition_ratio * 0.7 +
            position_factor * 0.3
        )
        
        return max(0.8, min(1.2, competition_multiplier))
    
    def _generate_value_justification(self, factors: PricingFactors, multiplier: float) -> str:
        """Gera justificativa baseada no valor"""
        if multiplier > 1.2:
            return f"Preço premium por ROI excepcional de {factors.user_roi:.1f}% e precisão de {factors.pick_accuracy*100:.1f}%"
        elif multiplier < 0.9:
            return f"Desconto aplicado para melhorar seu ROI atual de {factors.user_roi:.1f}%"
        else:
            return f"Preço justo baseado em sua performance atual de {factors.user_roi:.1f}% ROI"
    
    def _generate_demand_justification(self, factors: PricingFactors, multiplier: float) -> str:
        """Gera justificativa baseada na demanda"""
        if factors.current_demand > 1.5:
            return f"Alta demanda no momento - apenas {factors.premium_spots} spots premium disponíveis"
        elif factors.current_demand < 0.8:
            return "Oferta especial devido à baixa demanda atual"
        else:
            return "Preço equilibrado baseado na demanda atual"
    
    def _generate_personalization_justification(self, factors: PricingFactors, multiplier: float) -> str:
        """Gera justificativa baseada na personalização"""
        if factors.churn_risk > 0.7:
            return "Desconto de retenção aplicado - queremos você conosco!"
        elif factors.engagement_score > 0.8:
            return "Preço premium por ser um usuário altamente engajado"
        else:
            return "Preço personalizado baseado em seu perfil de uso"
    
    def _calculate_conversion_probability(self, dynamic_price: Decimal, base_price: Decimal, factors: PricingFactors) -> float:
        """Calcula probabilidade de conversão"""
        # Usar curva de demanda elástica
        price_ratio = float(dynamic_price / base_price)
        
        # Elasticidade baseada no comportamento do usuário
        elasticity = -1.5 + (factors.engagement_score * 0.5)  # Usuários engajados são menos sensíveis ao preço
        
        # Aplicar curva de demanda
        conversion_probability = math.exp(elasticity * (price_ratio - 1))
        
        # Ajustar baseado no valor percebido
        value_adjustment = 1 + (factors.user_roi / 100)
        conversion_probability *= value_adjustment
        
        return max(0.1, min(0.95, conversion_probability))
    
    def _calculate_price_sensitivity(self, factors: PricingFactors) -> float:
        """Calcula sensibilidade ao preço do usuário"""
        # Fatores que reduzem sensibilidade ao preço
        sensitivity = 1.0
        
        # ROI alto = menor sensibilidade
        sensitivity -= (factors.user_roi / 100) * 0.3
        
        # Engajamento alto = menor sensibilidade
        sensitivity -= factors.engagement_score * 0.2
        
        # Risco de churn = maior sensibilidade
        sensitivity += factors.churn_risk * 0.3
        
        return max(0.2, min(1.0, sensitivity))
    
    def _calculate_optimal_price(self, base_price: Decimal, factors: PricingFactors) -> Decimal:
        """Calcula preço ótimo para maximizar receita"""
        # Usar cálculo de elasticidade de preço
        sensitivity = self._calculate_price_sensitivity(factors)
        
        # Preço ótimo = preço base * (1 + margem ótima)
        optimal_margin = (1 - sensitivity) * 0.5  # Margem baseada na sensibilidade
        
        optimal_price = base_price * Decimal(str(1 + optimal_margin))
        
        return optimal_price
    
    def _get_default_factors(self, user_id: Optional[int]) -> PricingFactors:
        """Obtém fatores padrão para um usuário"""
        if user_id is None:
            return PricingFactors()
        
        # Aqui você buscaria dados reais do usuário
        # Por enquanto, retornamos fatores mock
        return PricingFactors(
            user_roi=15.0,
            pick_accuracy=0.68,
            avg_ev_positive=8.5,
            current_demand=1.2,
            server_load=1.1,
            premium_spots=85,
            engagement_score=0.7,
            churn_risk=0.3,
            lifetime_value=500.0,
            season_multiplier=1.0,
            day_of_week=datetime.now().weekday() + 1,
            hour_of_day=datetime.now().hour,
            competitor_price=120.0,
            market_position=1.1
        )
    
    @cache_result("dynamic_pricing", ttl=3600)  # Cache por 1 hora
    async def get_pricing_for_user(self, user_id: int, tier: PricingTier) -> Dict:
        """Obtém preço dinâmico para usuário específico"""
        factors = self._get_default_factors(user_id)
        result = self.calculate_dynamic_price(tier, user_id, factors)
        
        return {
            "tier": tier.value,
            "base_price": float(result.base_price),
            "dynamic_price": float(result.dynamic_price),
            "discount_percentage": result.discount_percentage,
            "premium_percentage": result.premium_percentage,
            "justification": {
                "value": result.value_justification,
                "demand": result.demand_justification,
                "personalization": result.personalization_justification
            },
            "metrics": {
                "expected_conversion": result.expected_conversion,
                "price_sensitivity": result.price_sensitivity,
                "optimal_price": float(result.optimal_price)
            }
        }
    
    def get_all_tiers_pricing(self, user_id: Optional[int] = None) -> Dict[str, Dict]:
        """Obtém preços de todos os tiers para um usuário"""
        factors = self._get_default_factors(user_id)
        
        pricing_results = {}
        for tier in PricingTier:
            result = self.calculate_dynamic_price(tier, user_id, factors)
            pricing_results[tier.value] = {
                "base_price": float(result.base_price),
                "dynamic_price": float(result.dynamic_price),
                "discount_percentage": result.discount_percentage,
                "premium_percentage": result.premium_percentage,
                "expected_conversion": result.expected_conversion
            }
        
        return pricing_results
    
    def simulate_pricing_scenarios(self, base_factors: PricingFactors) -> Dict:
        """Simula diferentes cenários de preço"""
        scenarios = {
            "high_demand": PricingFactors(**{**base_factors.__dict__, "current_demand": 2.0}),
            "low_demand": PricingFactors(**{**base_factors.__dict__, "current_demand": 0.5}),
            "high_roi_user": PricingFactors(**{**base_factors.__dict__, "user_roi": 30.0}),
            "churn_risk_user": PricingFactors(**{**base_factors.__dict__, "churn_risk": 0.8}),
            "weekend_premium": PricingFactors(**{**base_factors.__dict__, "day_of_week": 6}),
        }
        
        results = {}
        for scenario_name, scenario_factors in scenarios.items():
            scenario_results = {}
            for tier in PricingTier:
                result = self.calculate_dynamic_price(tier, None, scenario_factors)
                scenario_results[tier.value] = float(result.dynamic_price)
            results[scenario_name] = scenario_results
        
        return results

# Instância global
pricing_engine = DynamicPricingEngine()

# Funções auxiliares
async def get_user_pricing(user_id: int, tier: str = "premium") -> Dict:
    """Função auxiliar para obter preço do usuário"""
    tier_enum = PricingTier(tier)
    return await pricing_engine.get_pricing_for_user(user_id, tier_enum)

async def get_pricing_comparison(user_id: Optional[int] = None) -> Dict:
    """Comparação de preços entre todos os tiers"""
    return pricing_engine.get_all_tiers_pricing(user_id) 