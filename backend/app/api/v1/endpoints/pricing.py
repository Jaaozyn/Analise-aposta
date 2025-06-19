"""
Pricing Endpoints - Sistema de Preços Dinâmicos
Endpoints para obter preços personalizados baseados em múltiplos fatores
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.dynamic_pricing import pricing_engine, PricingTier, PricingFactors, get_user_pricing, get_pricing_comparison
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.rate_limiter import limiter, RateLimits

router = APIRouter()

@router.get("/tiers", response_model=Dict[str, Any])
@limiter.limit(RateLimits.PUBLIC_GENERAL)
async def get_pricing_tiers(request):
    """
    📋 Lista todos os tiers de preço disponíveis
    """
    return {
        "message": "Tiers de preço QuantumBet",
        "tiers": {
            "basic": {
                "name": "Basic",
                "description": "Picks básicos com análise fundamental",
                "base_price": 49.00,
                "features": [
                    "Até 20 picks por mês",
                    "Análise básica de EV+",
                    "Suporte por email",
                    "Dashboard básico"
                ]
            },
            "premium": {
                "name": "Premium",
                "description": "Picks avançados com ML e análises detalhadas",
                "base_price": 99.00,
                "features": [
                    "Picks ilimitados",
                    "Análise ML avançada",
                    "Backtesting histórico",
                    "Alertas em tempo real",
                    "Suporte prioritário"
                ]
            },
            "professional": {
                "name": "Professional",
                "description": "Solução completa para apostadores profissionais",
                "base_price": 149.00,
                "features": [
                    "Tudo do Premium",
                    "Análise de portfólio",
                    "Gestão de banca avançada",
                    "Insights personalizados",
                    "API access"
                ]
            },
            "enterprise": {
                "name": "Enterprise",
                "description": "Para grupos e organizações",
                "base_price": 199.00,
                "features": [
                    "Tudo do Professional",
                    "Múltiplos usuários",
                    "Consultoria personalizada",
                    "Dashboard customizado",
                    "SLA garantido"
                ]
            }
        }
    }

@router.get("/dynamic/{tier}")
@limiter.limit(RateLimits.USER_DATA)
async def get_dynamic_pricing(
    request,
    tier: str,
    current_user: User = Depends(get_current_user)
):
    """
    💰 Obtém preço dinâmico personalizado para um tier específico
    """
    try:
        tier_enum = PricingTier(tier)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Tier inválido. Opções: {[t.value for t in PricingTier]}"
        )
    
    pricing_result = await get_user_pricing(current_user.id, tier)
    
    return {
        "user_id": current_user.id,
        "tier": tier,
        "pricing": pricing_result,
        "message": "Preço personalizado calculado com base no seu histórico e valor percebido",
        "valid_until": (datetime.now().replace(hour=23, minute=59, second=59)).isoformat()
    }

@router.get("/comparison")
@limiter.limit(RateLimits.USER_DATA)
async def get_pricing_comparison_endpoint(
    request,
    current_user: User = Depends(get_current_user)
):
    """
    📊 Comparação de preços dinâmicos entre todos os tiers
    """
    comparison = await get_pricing_comparison(current_user.id)
    
    # Calcular economia em cada tier
    for tier_name, tier_data in comparison.items():
        savings = tier_data["base_price"] - tier_data["dynamic_price"]
        tier_data["savings_amount"] = savings
        tier_data["savings_percentage"] = (savings / tier_data["base_price"]) * 100 if tier_data["base_price"] > 0 else 0
    
    return {
        "user_id": current_user.id,
        "comparison": comparison,
        "recommendation": _get_tier_recommendation(comparison, current_user),
        "message": "Preços personalizados baseados no seu perfil de uso"
    }

@router.get("/factors")
@limiter.limit(RateLimits.USER_DATA)
async def get_pricing_factors(
    request,
    current_user: User = Depends(get_current_user)
):
    """
    🔍 Fatores que influenciam seu preço personalizado
    """
    # Obter fatores do usuário (mock por enquanto)
    factors = pricing_engine._get_default_factors(current_user.id)
    
    return {
        "user_id": current_user.id,
        "factors": {
            "value_delivered": {
                "user_roi": factors.user_roi,
                "pick_accuracy": factors.pick_accuracy * 100,
                "avg_ev_positive": factors.avg_ev_positive,
                "impact": "Maior ROI = preços premium por valor entregue"
            },
            "demand_supply": {
                "current_demand": factors.current_demand,
                "premium_spots": factors.premium_spots,
                "server_load": factors.server_load,
                "impact": "Alta demanda = preços premium por escassez"
            },
            "user_behavior": {
                "engagement_score": factors.engagement_score * 100,
                "churn_risk": factors.churn_risk * 100,
                "lifetime_value": factors.lifetime_value,
                "impact": "Maior engajamento = preços personalizados"
            },
            "temporal": {
                "season_multiplier": factors.season_multiplier,
                "day_of_week": factors.day_of_week,
                "hour_of_day": factors.hour_of_day,
                "impact": "Fins de semana e horários premium = preços ajustados"
            }
        },
        "message": "Estes fatores determinam seu preço personalizado"
    }

@router.post("/simulate")
@limiter.limit(RateLimits.USER_DATA)
async def simulate_pricing_scenarios(
    request,
    scenario_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    🧪 Simula diferentes cenários de preço
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem simular cenários")
    
    try:
        # Criar fatores customizados baseados nos dados fornecidos
        base_factors = pricing_engine._get_default_factors(None)
        
        # Atualizar fatores com dados fornecidos
        for key, value in scenario_data.items():
            if hasattr(base_factors, key):
                setattr(base_factors, key, value)
        
        # Executar simulação
        simulation_results = pricing_engine.simulate_pricing_scenarios(base_factors)
        
        return {
            "simulation_results": simulation_results,
            "input_factors": scenario_data,
            "message": "Simulação de cenários de preço executada"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na simulação: {str(e)}")

@router.get("/analytics")
@limiter.limit(RateLimits.USER_DATA)
async def get_pricing_analytics(
    request,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    📈 Analytics de preços e conversão
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem ver analytics")
    
    # Mock data - em produção viria do banco de dados
    return {
        "period": f"Últimos {days} dias",
        "pricing_analytics": {
            "average_discount": 12.5,
            "average_premium": 8.3,
            "conversion_rate": {
                "basic": 15.2,
                "premium": 8.7,
                "professional": 4.1,
                "enterprise": 2.3
            },
            "revenue_impact": {
                "total_revenue": 125000,
                "dynamic_pricing_lift": 22.8,
                "missed_revenue": 8500
            },
            "user_segments": {
                "high_value": {"count": 45, "avg_price": 165.50},
                "at_risk": {"count": 23, "avg_price": 82.30},
                "new_users": {"count": 167, "avg_price": 71.20}
            }
        },
        "recommendations": [
            "Aumentar preços para usuários high-value em 15%",
            "Aplicar desconto de retenção para usuários at-risk",
            "Criar promoção especial para novos usuários"
        ]
    }

def _get_tier_recommendation(comparison: Dict, user: User) -> Dict:
    """Gera recomendação de tier baseada no perfil do usuário"""
    # Lógica de recomendação baseada em múltiplos fatores
    
    # Para usuários com bom ROI, recomendar tier superior
    if user.total_roi > 20:
        recommended_tier = "professional"
        reason = "Seu ROI excepcional indica que você maximizaria o valor do tier Professional"
    elif user.total_roi > 10:
        recommended_tier = "premium"
        reason = "Seu ROI consistente sugere que o tier Premium é ideal para você"
    else:
        recommended_tier = "basic"
        reason = "Comece com o tier Basic e upgrade conforme seus resultados melhoram"
    
    # Calcular ROI potencial
    recommended_pricing = comparison.get(recommended_tier, {})
    monthly_cost = recommended_pricing.get("dynamic_price", 0)
    potential_monthly_roi = user.balance * (user.total_roi / 100) / 12  # ROI mensal estimado
    
    return {
        "recommended_tier": recommended_tier,
        "reason": reason,
        "monthly_cost": monthly_cost,
        "potential_monthly_roi": potential_monthly_roi,
        "roi_multiple": potential_monthly_roi / monthly_cost if monthly_cost > 0 else 0,
        "value_proposition": f"Cada R$ {monthly_cost:.0f} investido pode gerar R$ {potential_monthly_roi:.0f} de ROI"
    } 