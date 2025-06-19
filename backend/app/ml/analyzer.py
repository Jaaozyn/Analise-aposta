import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ValueCalculator:
    """Motor de cálculo de valor esperado"""
    
    def calculate_ev(self, probability: float, odds: float) -> float:
        """Calcula Valor Esperado: EV = (P * (Odds - 1)) - (1 - P)"""
        if probability <= 0 or probability >= 1 or odds <= 1:
            return 0.0
        return ((probability * (odds - 1)) - (1 - probability)) * 100
    
    def is_value_bet(self, probability: float, odds: float, min_ev: float = 5.0) -> bool:
        """Verifica se é aposta de valor"""
        return self.calculate_ev(probability, odds) >= min_ev
    
    def suggest_stake(self, ev: float, confidence: float) -> float:
        """Sugere unidades de aposta (Kelly modificado)"""
        if ev <= 0:
            return 0.0
        kelly = (ev / 100) * confidence
        return min(max(kelly * 25, 0.5), 10.0)  # Entre 0.5 e 10 unidades

class FootballAnalyzer(ValueCalculator):
    """Analisador de Futebol"""
    
    def analyze_match(self, match_data: Dict) -> Dict[str, float]:
        """Calcula probabilidades básicas para futebol"""
        # Força dos times baseada em gols
        home_strength = match_data.get("home_avg_goals", 1.5) / max(match_data.get("home_avg_conceded", 1.5), 0.1)
        away_strength = match_data.get("away_avg_goals", 1.5) / max(match_data.get("away_avg_conceded", 1.5), 0.1)
        
        # Fator casa
        home_strength *= 1.15
        
        # Normalizar
        total = home_strength + away_strength + 1.0
        return {
            "home": home_strength / total,
            "draw": 1.0 / total,
            "away": away_strength / total
        }

class BasketballAnalyzer(ValueCalculator):
    """Analisador de Basquete"""
    
    def analyze_match(self, match_data: Dict) -> Dict[str, float]:
        """Calcula probabilidades para basquete"""
        home_eff = match_data.get("home_avg_points", 100) / max(match_data.get("home_avg_conceded", 100), 1)
        away_eff = match_data.get("away_avg_points", 100) / max(match_data.get("away_avg_conceded", 100), 1)
        
        home_eff *= 1.08  # Fator casa
        total = home_eff + away_eff
        
        return {
            "home": home_eff / total,
            "away": away_eff / total
        }

class EsportsAnalyzer(ValueCalculator):
    """Analisador de E-sports"""
    
    def analyze_match(self, match_data: Dict) -> Dict[str, float]:
        """Calcula probabilidades para e-sports"""
        home_wr = match_data.get("home_winrate", 0.5)
        away_wr = match_data.get("away_winrate", 0.5)
        
        total = home_wr + away_wr
        if total == 0:
            return {"home": 0.5, "away": 0.5}
        
        return {
            "home": home_wr / total,
            "away": away_wr / total
        }

def create_analyzer(sport: str):
    """Factory para criar analisador"""
    sport = sport.lower()
    if sport == "football":
        return FootballAnalyzer()
    elif sport == "basketball":
        return BasketballAnalyzer()
    elif sport in ["cs2", "valorant"]:
        return EsportsAnalyzer()
    else:
        return ValueCalculator() 