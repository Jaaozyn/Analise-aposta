import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
from sklearn.preprocessing import StandardScaler
import joblib
import logging

logger = logging.getLogger(__name__)

class ValueCalculator:
    """
    Motor de Análise Probabilística e de Valor (O "Cérebro")
    
    Calcula probabilidades justas e identifica apostas de valor positivo (EV+)
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = {}
        
    def calculate_expected_value(
        self, 
        calculated_probability: float, 
        market_odds: float
    ) -> float:
        """
        Calcula o Valor Esperado (EV) de uma aposta
        
        Fórmula: EV = (Probabilidade de Ganhar * (Odd Decimal - 1)) - (Probabilidade de Perder)
        
        Args:
            calculated_probability: Probabilidade calculada pelo modelo (0-1)
            market_odds: Odd decimal oferecida pelo mercado
            
        Returns:
            Valor esperado em percentual
        """
        if calculated_probability <= 0 or calculated_probability >= 1:
            return 0.0
            
        if market_odds <= 1.0:
            return 0.0
        
        # Probabilidade de perder
        prob_lose = 1 - calculated_probability
        
        # Cálculo do EV
        ev = (calculated_probability * (market_odds - 1)) - prob_lose
        
        # Converter para percentual
        return ev * 100
    
    def calculate_market_probability(self, odds: float) -> float:
        """
        Calcula a probabilidade implícita das odds do mercado
        
        Args:
            odds: Odd decimal
            
        Returns:
            Probabilidade implícita (0-1)
        """
        if odds <= 1.0:
            return 0.0
        return 1 / odds
    
    def is_value_bet(
        self, 
        calculated_probability: float, 
        market_odds: float,
        min_ev_threshold: float = 5.0
    ) -> bool:
        """
        Verifica se uma aposta tem valor positivo
        
        Args:
            calculated_probability: Probabilidade calculada pelo modelo
            market_odds: Odd oferecida pelo mercado
            min_ev_threshold: EV mínimo para considerar como valor (%)
            
        Returns:
            True se a aposta tem EV+ acima do threshold
        """
        ev = self.calculate_expected_value(calculated_probability, market_odds)
        return ev >= min_ev_threshold
    
    def calculate_suggested_stake(
        self, 
        expected_value: float,
        confidence_level: float,
        bankroll_percentage: float = 2.0
    ) -> float:
        """
        Calcula a unidade de aposta sugerida usando Kelly Criterion modificado
        
        Args:
            expected_value: Valor esperado da aposta (%)
            confidence_level: Nível de confiança do modelo (0-1)
            bankroll_percentage: % máximo da banca por aposta
            
        Returns:
            Unidades sugeridas (0-10 escala)
        """
        if expected_value <= 0:
            return 0.0
        
        # Kelly Criterion básico
        ev_decimal = expected_value / 100
        kelly_fraction = ev_decimal * confidence_level
        
        # Limitar a no máximo 2% da banca (gestão conservadora)
        kelly_fraction = min(kelly_fraction, bankroll_percentage / 100)
        
        # Converter para escala de 1-10 unidades
        stake_units = kelly_fraction * 50  # Multiplicador para escala
        stake_units = max(0.5, min(stake_units, 10.0))  # Entre 0.5 e 10
        
        return round(stake_units, 1)

class FootballAnalyzer(ValueCalculator):
    """Analisador específico para Futebol"""
    
    def __init__(self):
        super().__init__()
        self.sport = "football"
        
    def calculate_match_probabilities(self, match_data: Dict) -> Dict[str, float]:
        """
        Calcula probabilidades para uma partida de futebol
        
        Args:
            match_data: Dados da partida
            
        Returns:
            Dicionário com probabilidades {home, draw, away}
        """
        try:
            # Extrair features da partida
            features = self._extract_football_features(match_data)
            
            # Carregar modelo treinado
            model = self._load_model("football_winner")
            
            if model is None:
                # Fallback: usar cálculo estatístico simples
                return self._calculate_simple_probabilities(match_data)
            
            # Fazer predição
            probabilities = model.predict_proba([features])[0]
            
            return {
                "home": float(probabilities[0]),
                "draw": float(probabilities[1]),
                "away": float(probabilities[2])
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular probabilidades de futebol: {e}")
            return self._calculate_simple_probabilities(match_data)
    
    def _extract_football_features(self, match_data: Dict) -> List[float]:
        """Extrai features para o modelo de ML"""
        features = []
        
        # Features básicas
        features.extend([
            match_data.get("home_avg_goals", 1.5),
            match_data.get("away_avg_goals", 1.5),
            match_data.get("home_avg_conceded", 1.5),
            match_data.get("away_avg_conceded", 1.5),
        ])
        
        # Forma recente (últimos 5 jogos)
        home_form = self._parse_form(match_data.get("home_form", ""))
        away_form = self._parse_form(match_data.get("away_form", ""))
        
        features.extend([
            home_form.get("wins", 0) / 5,
            home_form.get("draws", 0) / 5,
            home_form.get("losses", 0) / 5,
            away_form.get("wins", 0) / 5,
            away_form.get("draws", 0) / 5,
            away_form.get("losses", 0) / 5,
        ])
        
        # H2H (histórico)
        h2h = self._parse_h2h(match_data.get("h2h_data", ""))
        features.extend([
            h2h.get("home_wins", 0) / max(h2h.get("total_games", 1), 1),
            h2h.get("draws", 0) / max(h2h.get("total_games", 1), 1),
            h2h.get("away_wins", 0) / max(h2h.get("total_games", 1), 1),
        ])
        
        return features
    
    def _parse_form(self, form_data: str) -> Dict:
        """Parse dos dados de forma recente"""
        if not form_data:
            return {"wins": 0, "draws": 0, "losses": 0}
        
        try:
            form = json.loads(form_data) if isinstance(form_data, str) else form_data
            return {
                "wins": len([r for r in form if r.get("result") == "W"]),
                "draws": len([r for r in form if r.get("result") == "D"]),
                "losses": len([r for r in form if r.get("result") == "L"])
            }
        except:
            return {"wins": 0, "draws": 0, "losses": 0}
    
    def _parse_h2h(self, h2h_data: str) -> Dict:
        """Parse dos dados históricos H2H"""
        if not h2h_data:
            return {"home_wins": 0, "draws": 0, "away_wins": 0, "total_games": 0}
        
        try:
            h2h = json.loads(h2h_data) if isinstance(h2h_data, str) else h2h_data
            total = len(h2h)
            home_wins = len([r for r in h2h if r.get("winner") == "home"])
            draws = len([r for r in h2h if r.get("winner") == "draw"])
            away_wins = len([r for r in h2h if r.get("winner") == "away"])
            
            return {
                "home_wins": home_wins,
                "draws": draws,
                "away_wins": away_wins,
                "total_games": total
            }
        except:
            return {"home_wins": 0, "draws": 0, "away_wins": 0, "total_games": 0}
    
    def _calculate_simple_probabilities(self, match_data: Dict) -> Dict[str, float]:
        """Cálculo estatístico simples quando o modelo ML não está disponível"""
        
        # Força dos times baseada em médias de gols
        home_strength = match_data.get("home_avg_goals", 1.5) / max(match_data.get("home_avg_conceded", 1.5), 0.1)
        away_strength = match_data.get("away_avg_goals", 1.5) / max(match_data.get("away_avg_conceded", 1.5), 0.1)
        
        # Fator casa (vantagem estatística)
        home_advantage = 1.15
        home_strength *= home_advantage
        
        # Normalizar probabilidades
        total_strength = home_strength + away_strength + 1.0  # +1 para empate
        
        home_prob = home_strength / total_strength
        away_prob = away_strength / total_strength
        draw_prob = 1.0 / total_strength
        
        # Ajustar para somar 100%
        total = home_prob + draw_prob + away_prob
        
        return {
            "home": home_prob / total,
            "draw": draw_prob / total,
            "away": away_prob / total
        }
    
    def _load_model(self, model_name: str):
        """Carrega modelo treinado do disco"""
        try:
            if model_name not in self.models:
                model_path = f"models/{model_name}.joblib"
                self.models[model_name] = joblib.load(model_path)
            return self.models[model_name]
        except:
            logger.warning(f"Modelo {model_name} não encontrado")
            return None

class BasketballAnalyzer(ValueCalculator):
    """Analisador específico para Basquetebol"""
    
    def __init__(self):
        super().__init__()
        self.sport = "basketball"
    
    def calculate_match_probabilities(self, match_data: Dict) -> Dict[str, float]:
        """Calcula probabilidades para basquete (sem empate)"""
        
        # Features específicas do basquete
        home_ppg = match_data.get("home_avg_points", 100)
        away_ppg = match_data.get("away_avg_points", 100)
        home_opp_ppg = match_data.get("home_avg_conceded", 100)
        away_opp_ppg = match_data.get("away_avg_conceded", 100)
        
        # Eficiência ofensiva/defensiva
        home_off_eff = home_ppg / 100
        home_def_eff = 100 / home_opp_ppg
        away_off_eff = away_ppg / 100
        away_def_eff = 100 / away_opp_ppg
        
        # Força combinada
        home_strength = (home_off_eff + home_def_eff) / 2
        away_strength = (away_off_eff + away_def_eff) / 2
        
        # Fator casa para basquete
        home_strength *= 1.08
        
        # Probabilidades
        total_strength = home_strength + away_strength
        home_prob = home_strength / total_strength
        away_prob = away_strength / total_strength
        
        return {
            "home": home_prob,
            "away": away_prob
        }

class EsportsAnalyzer(ValueCalculator):
    """Analisador para e-Sports (CS2, Valorant)"""
    
    def __init__(self, game: str):
        super().__init__()
        self.sport = game.lower()
        
    def calculate_match_probabilities(self, match_data: Dict) -> Dict[str, float]:
        """Calcula probabilidades para e-sports"""
        
        # Win rate geral
        home_winrate = match_data.get("home_winrate", 0.5)
        away_winrate = match_data.get("away_winrate", 0.5)
        
        # Forma recente (mais importante em e-sports)
        home_recent = self._calculate_recent_form(match_data.get("home_form", ""))
        away_recent = self._calculate_recent_form(match_data.get("away_form", ""))
        
        # Peso maior para forma recente
        home_strength = (home_winrate * 0.3) + (home_recent * 0.7)
        away_strength = (away_winrate * 0.3) + (away_recent * 0.7)
        
        # Normalizar
        total = home_strength + away_strength
        if total > 0:
            home_prob = home_strength / total
            away_prob = away_strength / total
        else:
            home_prob = away_prob = 0.5
        
        return {
            "home": home_prob,
            "away": away_prob
        }
    
    def _calculate_recent_form(self, form_data: str) -> float:
        """Calcula forma recente para e-sports"""
        if not form_data:
            return 0.5
        
        try:
            form = json.loads(form_data) if isinstance(form_data, str) else form_data
            recent_results = form[-5:]  # Últimos 5 jogos
            wins = len([r for r in recent_results if r.get("result") == "W"])
            return wins / len(recent_results) if recent_results else 0.5
        except:
            return 0.5

# Factory para criar analisadores
def create_analyzer(sport: str):
    """Factory para criar o analisador correto baseado no esporte"""
    sport = sport.lower()
    
    if sport == "football":
        return FootballAnalyzer()
    elif sport == "basketball":
        return BasketballAnalyzer()
    elif sport in ["cs2", "valorant"]:
        return EsportsAnalyzer(sport)
    else:
        raise ValueError(f"Esporte '{sport}' não suportado") 