"""
Multi-Market Analyzer - Sistema de Múltiplos Picks
Analisa todos os mercados possíveis e sempre retorna os 5 melhores picks por partida
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from app.ml.enhanced_analyzer import EnsembleFootballAnalyzer
from app.ml.value_calculator import ValueCalculator

logger = logging.getLogger(__name__)

class MarketType(Enum):
    """Tipos de mercado disponíveis"""
    MATCH_RESULT = "match_result"          # 1X2
    OVER_UNDER_GOALS = "over_under_goals"  # Over/Under 2.5, 1.5, 3.5
    BOTH_TEAMS_SCORE = "both_teams_score"  # Ambos marcam
    HANDICAP = "handicap"                  # Handicap asiático
    CORRECT_SCORE = "correct_score"        # Placar exato
    FIRST_HALF = "first_half"              # Resultado 1º tempo
    CLEAN_SHEET = "clean_sheet"            # Algum time não sofre gol
    TOTAL_CORNERS = "total_corners"        # Total de escanteios
    CARDS = "cards"                        # Total de cartões

@dataclass
class MarketPick:
    """Representação de um pick específico"""
    market_type: MarketType
    selection: str                         # "Over 2.5", "Home Win", etc.
    description: str                       # Descrição amigável
    calculated_probability: float          # Probabilidade real (0-1)
    market_odds: float                     # Odd oferecida pelo mercado
    expected_value: float                  # EV em percentual
    confidence_score: float                # Nível de confiança (0-1)
    stake_suggestion: float                # Unidades sugeridas (0-10)
    risk_level: str                        # "low", "medium", "high"
    reasoning: List[str]                   # Motivos da análise
    is_value_bet: bool                     # Se tem EV+
    market_probability: float              # Prob. implícita do mercado

@dataclass
class MatchAnalysis:
    """Análise completa de uma partida"""
    match_id: str
    home_team: str
    away_team: str
    sport: str
    all_picks: List[MarketPick]            # Todos os picks analisados
    top_picks: List[MarketPick]            # Top 5 picks
    value_picks: List[MarketPick]          # Apenas picks com EV+
    analysis_metadata: Dict
    created_at: datetime

class MultiMarketAnalyzer:
    """Analisador de múltiplos mercados por partida"""
    
    def __init__(self, sport: str = "football"):
        self.sport = sport
        self.base_analyzer = EnsembleFootballAnalyzer()
        self.value_calculator = ValueCalculator()
        
        # Configuração de mercados por esporte
        self.market_configs = {
            "football": {
                MarketType.MATCH_RESULT: self._analyze_match_result,
                MarketType.OVER_UNDER_GOALS: self._analyze_over_under,
                MarketType.BOTH_TEAMS_SCORE: self._analyze_both_teams_score,
                MarketType.HANDICAP: self._analyze_handicap,
                MarketType.FIRST_HALF: self._analyze_first_half,
                MarketType.CLEAN_SHEET: self._analyze_clean_sheet,
                MarketType.TOTAL_CORNERS: self._analyze_corners,
                MarketType.CARDS: self._analyze_cards
            }
        }
    
    def analyze_match_comprehensive(self, match_data: Dict, market_odds: Dict) -> MatchAnalysis:
        """
        Análise abrangente de todos os mercados de uma partida
        
        Args:
            match_data: Dados da partida
            market_odds: Odds de todos os mercados
            
        Returns:
            Análise completa com todos os picks
        """
        start_time = datetime.now()
        
        # Análise base das probabilidades da partida
        base_analysis = self.base_analyzer.analyze_match_advanced(match_data)
        base_probabilities = base_analysis["probabilities"]
        base_confidence = base_analysis["confidence"]
        
        all_picks = []
        
        # Analisar todos os mercados configurados para o esporte
        for market_type, analyzer_func in self.market_configs.get(self.sport, {}).items():
            try:
                market_picks = analyzer_func(
                    match_data, 
                    base_probabilities, 
                    base_confidence,
                    market_odds.get(market_type.value, {})
                )
                all_picks.extend(market_picks)
                
            except Exception as e:
                logger.warning(f"Erro ao analisar mercado {market_type.value}: {e}")
        
        # Ordenar picks por EV (do melhor para o pior)
        all_picks.sort(key=lambda x: x.expected_value, reverse=True)
        
        # Separar picks com valor (EV+) dos demais
        value_picks = [pick for pick in all_picks if pick.is_value_bet]
        top_picks = all_picks[:5]  # Sempre os 5 melhores
        
        # Metadados da análise
        analysis_metadata = {
            "base_confidence": base_confidence,
            "total_markets_analyzed": len(self.market_configs.get(self.sport, {})),
            "total_picks_generated": len(all_picks),
            "value_picks_found": len(value_picks),
            "analysis_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
            "best_ev": all_picks[0].expected_value if all_picks else 0,
            "worst_ev": all_picks[-1].expected_value if all_picks else 0
        }
        
        return MatchAnalysis(
            match_id=match_data.get("id", "unknown"),
            home_team=match_data.get("home_team", "Team A"),
            away_team=match_data.get("away_team", "Team B"), 
            sport=self.sport,
            all_picks=all_picks,
            top_picks=top_picks,
            value_picks=value_picks,
            analysis_metadata=analysis_metadata,
            created_at=datetime.now()
        )
    
    def _analyze_match_result(self, match_data: Dict, base_probs: Dict, confidence: float, odds: Dict) -> List[MarketPick]:
        """Analisa mercado 1X2 (Resultado da partida)"""
        picks = []
        
        markets = [
            ("home", "Vitória Mandante", base_probs["home"]),
            ("draw", "Empate", base_probs["draw"]), 
            ("away", "Vitória Visitante", base_probs["away"])
        ]
        
        for selection, description, probability in markets:
            market_odds = odds.get(selection, 2.0)
            
            ev = self.value_calculator.calculate_expected_value(probability, market_odds)
            stake = self.value_calculator.calculate_suggested_stake(ev, confidence)
            
            reasoning = self._generate_match_result_reasoning(
                selection, probability, confidence, match_data
            )
            
            pick = MarketPick(
                market_type=MarketType.MATCH_RESULT,
                selection=f"{description}",
                description=f"{description} - {match_data.get('home_team', 'Casa')} vs {match_data.get('away_team', 'Fora')}",
                calculated_probability=probability,
                market_odds=market_odds,
                expected_value=ev,
                confidence_score=confidence,
                stake_suggestion=stake,
                risk_level=self._classify_risk(ev, confidence, market_odds),
                reasoning=reasoning,
                is_value_bet=ev >= 5.0,
                market_probability=1/market_odds if market_odds > 0 else 0
            )
            
            picks.append(pick)
        
        return picks
    
    def _analyze_over_under(self, match_data: Dict, base_probs: Dict, confidence: float, odds: Dict) -> List[MarketPick]:
        """Analisa mercados Over/Under de gols"""
        picks = []
        
        # Calcular gols esperados
        home_goals = match_data.get("home_avg_goals", 1.5)
        away_goals = match_data.get("away_avg_goals", 1.5)
        expected_goals = home_goals + away_goals
        
        # Diferentes linhas de gols
        goal_lines = [1.5, 2.5, 3.5]
        
        for line in goal_lines:
            # Calcular probabilidades usando distribuição Poisson
            over_prob = self._calculate_over_probability(expected_goals, line)
            under_prob = 1 - over_prob
            
            # Ajustar probabilidade baseada na confiança
            adjusted_confidence = confidence * 0.9  # Slightly lower for totals
            
            for direction, prob, desc in [("over", over_prob, "Over"), ("under", under_prob, "Under")]:
                market_odds = odds.get(f"{direction}_{line}", 2.0)
                
                ev = self.value_calculator.calculate_expected_value(prob, market_odds)
                stake = self.value_calculator.calculate_suggested_stake(ev, adjusted_confidence)
                
                reasoning = self._generate_goals_reasoning(
                    direction, line, expected_goals, match_data
                )
                
                pick = MarketPick(
                    market_type=MarketType.OVER_UNDER_GOALS,
                    selection=f"{desc} {line}",
                    description=f"{desc} {line} gols na partida",
                    calculated_probability=prob,
                    market_odds=market_odds,
                    expected_value=ev,
                    confidence_score=adjusted_confidence,
                    stake_suggestion=stake,
                    risk_level=self._classify_risk(ev, adjusted_confidence, market_odds),
                    reasoning=reasoning,
                    is_value_bet=ev >= 5.0,
                    market_probability=1/market_odds if market_odds > 0 else 0
                )
                
                picks.append(pick)
        
        return picks
    
    def _analyze_both_teams_score(self, match_data: Dict, base_probs: Dict, confidence: float, odds: Dict) -> List[MarketPick]:
        """Analisa mercado Ambos Marcam"""
        picks = []
        
        # Probabilidade de cada time marcar
        home_score_prob = self._calculate_team_score_probability(match_data, "home")
        away_score_prob = self._calculate_team_score_probability(match_data, "away")
        
        # Ambos marcam = P(Home marca) × P(Away marca)
        bts_yes_prob = home_score_prob * away_score_prob
        bts_no_prob = 1 - bts_yes_prob
        
        for selection, prob, desc in [("yes", bts_yes_prob, "Sim"), ("no", bts_no_prob, "Não")]:
            market_odds = odds.get(f"bts_{selection}", 2.0)
            
            ev = self.value_calculator.calculate_expected_value(prob, market_odds)
            stake = self.value_calculator.calculate_suggested_stake(ev, confidence)
            
            reasoning = self._generate_bts_reasoning(selection, prob, match_data)
            
            pick = MarketPick(
                market_type=MarketType.BOTH_TEAMS_SCORE,
                selection=f"Ambos Marcam - {desc}",
                description=f"Ambos os times marcam: {desc}",
                calculated_probability=prob,
                market_odds=market_odds,
                expected_value=ev,
                confidence_score=confidence,
                stake_suggestion=stake,
                risk_level=self._classify_risk(ev, confidence, market_odds),
                reasoning=reasoning,
                is_value_bet=ev >= 5.0,
                market_probability=1/market_odds if market_odds > 0 else 0
            )
            
            picks.append(pick)
        
        return picks
    
    def _analyze_handicap(self, match_data: Dict, base_probs: Dict, confidence: float, odds: Dict) -> List[MarketPick]:
        """Analisa mercados de Handicap Asiático"""
        picks = []
        
        # Calcular handicaps baseado na diferença de força
        home_strength = match_data.get("home_avg_goals", 1.5) / max(match_data.get("home_avg_conceded", 1.5), 0.1)
        away_strength = match_data.get("away_avg_goals", 1.5) / max(match_data.get("away_avg_conceded", 1.5), 0.1)
        
        strength_diff = home_strength - away_strength
        
        # Definir handicaps baseado na diferença
        if abs(strength_diff) > 0.5:
            handicaps = [-1.0, -0.5, 0.0, 0.5, 1.0]
        else:
            handicaps = [-0.5, 0.0, 0.5]
        
        for handicap in handicaps:
            # Ajustar probabilidades baseado no handicap
            adjusted_home_prob = self._adjust_probability_for_handicap(
                base_probs["home"], base_probs["draw"], handicap
            )
            
            market_odds = odds.get(f"handicap_{handicap}", 2.0)
            
            ev = self.value_calculator.calculate_expected_value(adjusted_home_prob, market_odds)
            stake = self.value_calculator.calculate_suggested_stake(ev, confidence)
            
            reasoning = self._generate_handicap_reasoning(handicap, strength_diff, match_data)
            
            pick = MarketPick(
                market_type=MarketType.HANDICAP,
                selection=f"Handicap {handicap:+.1f}",
                description=f"Mandante com handicap {handicap:+.1f}",
                calculated_probability=adjusted_home_prob,
                market_odds=market_odds,
                expected_value=ev,
                confidence_score=confidence,
                stake_suggestion=stake,
                risk_level=self._classify_risk(ev, confidence, market_odds),
                reasoning=reasoning,
                is_value_bet=ev >= 5.0,
                market_probability=1/market_odds if market_odds > 0 else 0
            )
            
            picks.append(pick)
        
        return picks
    
    def _analyze_first_half(self, match_data: Dict, base_probs: Dict, confidence: float, odds: Dict) -> List[MarketPick]:
        """Analisa resultado do primeiro tempo"""
        picks = []
        
        # Probabilidades do 1º tempo são geralmente mais equilibradas
        # Ajustar probabilidades base
        ht_home_prob = base_probs["home"] * 0.8 + 0.1  # Reduzir vantagem
        ht_draw_prob = base_probs["draw"] * 1.3        # Aumentar chance empate
        ht_away_prob = base_probs["away"] * 0.8 + 0.1
        
        # Normalizar
        total = ht_home_prob + ht_draw_prob + ht_away_prob
        ht_home_prob /= total
        ht_draw_prob /= total  
        ht_away_prob /= total
        
        markets = [
            ("home", "Mandante", ht_home_prob),
            ("draw", "Empate", ht_draw_prob),
            ("away", "Visitante", ht_away_prob)
        ]
        
        for selection, description, probability in markets:
            market_odds = odds.get(f"ht_{selection}", 2.5)
            
            ev = self.value_calculator.calculate_expected_value(probability, market_odds)
            stake = self.value_calculator.calculate_suggested_stake(ev, confidence * 0.85)  # Menor confiança para HT
            
            reasoning = self._generate_first_half_reasoning(selection, probability, match_data)
            
            pick = MarketPick(
                market_type=MarketType.FIRST_HALF,
                selection=f"1º Tempo - {description}",
                description=f"Resultado do primeiro tempo: {description}",
                calculated_probability=probability,
                market_odds=market_odds,
                expected_value=ev,
                confidence_score=confidence * 0.85,
                stake_suggestion=stake,
                risk_level=self._classify_risk(ev, confidence * 0.85, market_odds),
                reasoning=reasoning,
                is_value_bet=ev >= 5.0,
                market_probability=1/market_odds if market_odds > 0 else 0
            )
            
            picks.append(pick)
        
        return picks
    
    def _analyze_clean_sheet(self, match_data: Dict, base_probs: Dict, confidence: float, odds: Dict) -> List[MarketPick]:
        """Analisa mercado de Clean Sheet"""
        picks = []
        
        # Probabilidade de clean sheet baseada na defesa
        home_cs_prob = self._calculate_clean_sheet_probability(match_data, "home")
        away_cs_prob = self._calculate_clean_sheet_probability(match_data, "away")
        
        for team, prob, desc in [("home", home_cs_prob, "Mandante"), ("away", away_cs_prob, "Visitante")]:
            market_odds = odds.get(f"cs_{team}", 3.0)
            
            ev = self.value_calculator.calculate_expected_value(prob, market_odds)
            stake = self.value_calculator.calculate_suggested_stake(ev, confidence)
            
            reasoning = self._generate_clean_sheet_reasoning(team, prob, match_data)
            
            pick = MarketPick(
                market_type=MarketType.CLEAN_SHEET,
                selection=f"Clean Sheet - {desc}",
                description=f"{desc} não sofre gols",
                calculated_probability=prob,
                market_odds=market_odds,
                expected_value=ev,
                confidence_score=confidence,
                stake_suggestion=stake,
                risk_level=self._classify_risk(ev, confidence, market_odds),
                reasoning=reasoning,
                is_value_bet=ev >= 5.0,
                market_probability=1/market_odds if market_odds > 0 else 0
            )
            
            picks.append(pick)
        
        return picks
    
    def _analyze_corners(self, match_data: Dict, base_probs: Dict, confidence: float, odds: Dict) -> List[MarketPick]:
        """Analisa total de escanteios"""
        picks = []
        
        # Estimar escanteios baseado no estilo de jogo
        expected_corners = self._calculate_expected_corners(match_data)
        
        corner_lines = [8.5, 9.5, 10.5, 11.5]
        
        for line in corner_lines:
            over_prob = self._calculate_over_probability(expected_corners, line, distribution="normal")
            under_prob = 1 - over_prob
            
            for direction, prob, desc in [("over", over_prob, "Over"), ("under", under_prob, "Under")]:
                market_odds = odds.get(f"corners_{direction}_{line}", 2.0)
                
                ev = self.value_calculator.calculate_expected_value(prob, market_odds)
                stake = self.value_calculator.calculate_suggested_stake(ev, confidence * 0.7)  # Menor confiança
                
                reasoning = self._generate_corners_reasoning(direction, line, expected_corners, match_data)
                
                pick = MarketPick(
                    market_type=MarketType.TOTAL_CORNERS,
                    selection=f"{desc} {line} escanteios",
                    description=f"{desc} {line} escanteios na partida",
                    calculated_probability=prob,
                    market_odds=market_odds,
                    expected_value=ev,
                    confidence_score=confidence * 0.7,
                    stake_suggestion=stake,
                    risk_level=self._classify_risk(ev, confidence * 0.7, market_odds),
                    reasoning=reasoning,
                    is_value_bet=ev >= 5.0,
                    market_probability=1/market_odds if market_odds > 0 else 0
                )
                
                picks.append(pick)
        
        return picks[:2]  # Retornar apenas as 2 melhores linhas
    
    def _analyze_cards(self, match_data: Dict, base_probs: Dict, confidence: float, odds: Dict) -> List[MarketPick]:
        """Analisa total de cartões"""
        picks = []
        
        # Estimar cartões baseado no histórico e importância
        expected_cards = self._calculate_expected_cards(match_data)
        
        card_lines = [3.5, 4.5, 5.5]
        
        for line in card_lines:
            over_prob = self._calculate_over_probability(expected_cards, line, distribution="normal")
            under_prob = 1 - over_prob
            
            for direction, prob, desc in [("over", over_prob, "Over"), ("under", under_prob, "Under")]:
                market_odds = odds.get(f"cards_{direction}_{line}", 2.0)
                
                ev = self.value_calculator.calculate_expected_value(prob, market_odds)
                stake = self.value_calculator.calculate_suggested_stake(ev, confidence * 0.6)  # Baixa confiança
                
                reasoning = self._generate_cards_reasoning(direction, line, expected_cards, match_data)
                
                pick = MarketPick(
                    market_type=MarketType.CARDS,
                    selection=f"{desc} {line} cartões",
                    description=f"{desc} {line} cartões na partida",
                    calculated_probability=prob,
                    market_odds=market_odds,
                    expected_value=ev,
                    confidence_score=confidence * 0.6,
                    stake_suggestion=stake,
                    risk_level=self._classify_risk(ev, confidence * 0.6, market_odds),
                    reasoning=reasoning,
                    is_value_bet=ev >= 5.0,
                    market_probability=1/market_odds if market_odds > 0 else 0
                )
                
                picks.append(pick)
        
        return picks[:2]  # Retornar apenas as 2 melhores
    
    # Métodos auxiliares de cálculo
    def _calculate_over_probability(self, expected_value: float, line: float, distribution: str = "poisson") -> float:
        """Calcula probabilidade Over usando distribuição estatística"""
        if distribution == "poisson":
            from scipy.stats import poisson
            return 1 - poisson.cdf(line, expected_value)
        else:  # normal
            from scipy.stats import norm
            # Assumir desvio padrão como 20% da média
            std = expected_value * 0.2
            return 1 - norm.cdf(line, expected_value, std)
    
    def _calculate_team_score_probability(self, match_data: Dict, team: str) -> float:
        """Calcula probabilidade de um time marcar"""
        if team == "home":
            goals_avg = match_data.get("home_avg_goals", 1.5)
            opponent_def = match_data.get("away_avg_conceded", 1.5)
        else:
            goals_avg = match_data.get("away_avg_goals", 1.5)
            opponent_def = match_data.get("home_avg_conceded", 1.5)
        
        # Ajustar pela defesa do oponente
        adjusted_goals = goals_avg * (opponent_def / 1.5)
        
        # Converter para probabilidade (distribuição Poisson)
        from scipy.stats import poisson
        return 1 - poisson.pmf(0, adjusted_goals)  # P(pelo menos 1 gol)
    
    def _adjust_probability_for_handicap(self, home_prob: float, draw_prob: float, handicap: float) -> float:
        """Ajusta probabilidade considerando handicap"""
        if handicap == 0:
            return home_prob + 0.5 * draw_prob  # Empate conta como meio ganho
        elif handicap > 0:
            # Handicap favorável ao mandante
            return home_prob + draw_prob * (0.5 + handicap * 0.3)
        else:
            # Handicap desfavorável ao mandante  
            return home_prob * (1 + handicap * 0.3)
    
    def _calculate_clean_sheet_probability(self, match_data: Dict, team: str) -> float:
        """Calcula probabilidade de clean sheet"""
        if team == "home":
            goals_conceded = match_data.get("home_avg_conceded", 1.5)
        else:
            goals_conceded = match_data.get("away_avg_conceded", 1.5)
        
        # Usar distribuição Poisson
        from scipy.stats import poisson
        return poisson.pmf(0, goals_conceded)
    
    def _calculate_expected_corners(self, match_data: Dict) -> float:
        """Estima número de escanteios"""
        # Correlação: mais ataques = mais escanteios
        home_attack = match_data.get("home_avg_goals", 1.5)
        away_attack = match_data.get("away_avg_goals", 1.5)
        
        # Fórmula empírica
        return (home_attack + away_attack) * 2.5 + 2  # Base de 2 escanteios + fator ataque
    
    def _calculate_expected_cards(self, match_data: Dict) -> float:
        """Estima número de cartões"""
        base_cards = 4.0  # Média base
        
        # Fatores que aumentam cartões
        importance = match_data.get("importance_factor", 1.0)
        rivalry = 1.2 if "clássico" in match_data.get("description", "").lower() else 1.0
        
        return base_cards * importance * rivalry
    
    def _classify_risk(self, ev: float, confidence: float, odds: float) -> str:
        """Classifica nível de risco do pick"""
        if ev >= 10 and confidence >= 0.8 and odds <= 3.0:
            return "low"
        elif ev >= 5 and confidence >= 0.7:
            return "medium"
        else:
            return "high"
    
    # Métodos de reasoning
    def _generate_match_result_reasoning(self, selection: str, probability: float, confidence: float, match_data: Dict) -> List[str]:
        """Gera explicação para resultado da partida"""
        reasons = []
        
        if selection == "home":
            reasons.append(f"Mandante com {probability*100:.1f}% de chance de vitória")
            if match_data.get("home_avg_goals", 1.5) > match_data.get("away_avg_goals", 1.5):
                reasons.append("Ataque mandante superior ao visitante")
            reasons.append("Vantagem de jogar em casa (+15% boost)")
        elif selection == "draw":
            reasons.append(f"Empate com {probability*100:.1f}% de probabilidade")
            reasons.append("Times equilibrados em força")
        else:
            reasons.append(f"Visitante com {probability*100:.1f}% de chance")
            if match_data.get("away_avg_goals", 1.5) > match_data.get("home_avg_goals", 1.5):
                reasons.append("Ataque visitante superior")
        
        reasons.append(f"Nível de confiança: {confidence*100:.0f}%")
        return reasons
    
    def _generate_goals_reasoning(self, direction: str, line: float, expected: float, match_data: Dict) -> List[str]:
        """Gera explicação para mercado de gols"""
        reasons = []
        reasons.append(f"Gols esperados na partida: {expected:.1f}")
        
        if direction == "over":
            reasons.append(f"Probabilidade de mais de {line} gols")
            if expected > line + 0.5:
                reasons.append("Média de gols favorece Over")
        else:
            reasons.append(f"Probabilidade de menos de {line} gols")
            if expected < line - 0.5:
                reasons.append("Média de gols favorece Under")
        
        # Adicionar contexto dos times
        total_avg = match_data.get("home_avg_goals", 1.5) + match_data.get("away_avg_goals", 1.5)
        reasons.append(f"Média combinada dos times: {total_avg:.1f} gols")
        
        return reasons
    
    def _generate_bts_reasoning(self, selection: str, probability: float, match_data: Dict) -> List[str]:
        """Gera explicação para Ambos Marcam"""
        reasons = []
        
        home_goals = match_data.get("home_avg_goals", 1.5)
        away_goals = match_data.get("away_avg_goals", 1.5)
        
        if selection == "yes":
            reasons.append(f"Probabilidade ambos marcarem: {probability*100:.1f}%")
            reasons.append(f"Mandante marca em média {home_goals:.1f} gols")
            reasons.append(f"Visitante marca em média {away_goals:.1f} gols")
        else:
            reasons.append(f"Probabilidade de algum não marcar: {probability*100:.1f}%")
            if home_goals < 1.0 or away_goals < 1.0:
                reasons.append("Um dos times tem ataque fraco")
        
        return reasons
    
    def _generate_handicap_reasoning(self, handicap: float, strength_diff: float, match_data: Dict) -> List[str]:
        """Gera explicação para handicap"""
        reasons = []
        reasons.append(f"Handicap {handicap:+.1f} para o mandante")
        reasons.append(f"Diferença de força calculada: {strength_diff:.2f}")
        
        if handicap < 0:
            reasons.append("Mandante favorito precisa superar desvantagem")
        elif handicap > 0:
            reasons.append("Mandante recebe vantagem no handicap")
        else:
            reasons.append("Handicap neutro - empate conta como meio ganho")
        
        return reasons
    
    def _generate_first_half_reasoning(self, selection: str, probability: float, match_data: Dict) -> List[str]:
        """Gera explicação para primeiro tempo"""
        reasons = []
        reasons.append(f"1º tempo mais equilibrado que resultado final")
        reasons.append(f"Probabilidade {selection}: {probability*100:.1f}%")
        reasons.append("Times geralmente começam mais cautelosos")
        return reasons
    
    def _generate_clean_sheet_reasoning(self, team: str, probability: float, match_data: Dict) -> List[str]:
        """Gera explicação para clean sheet"""
        reasons = []
        
        if team == "home":
            conceded = match_data.get("home_avg_conceded", 1.5)
            reasons.append(f"Mandante sofre {conceded:.1f} gols/jogo em média")
        else:
            conceded = match_data.get("away_avg_conceded", 1.5)
            reasons.append(f"Visitante sofre {conceded:.1f} gols/jogo em média")
        
        reasons.append(f"Probabilidade clean sheet: {probability*100:.1f}%")
        
        if probability > 0.3:
            reasons.append("Defesa sólida favorece clean sheet")
        else:
            reasons.append("Ataque adversário dificulta clean sheet")
        
        return reasons
    
    def _generate_corners_reasoning(self, direction: str, line: float, expected: float, match_data: Dict) -> List[str]:
        """Gera explicação para escanteios"""
        reasons = []
        reasons.append(f"Escanteios esperados: {expected:.1f}")
        
        if direction == "over":
            reasons.append(f"Mais de {line} escanteios esperados")
        else:
            reasons.append(f"Menos de {line} escanteios esperados")
        
        return reasons
    
    def _generate_cards_reasoning(self, direction: str, line: float, expected: float, match_data: Dict) -> List[str]:
        """Gera explicação para cartões"""
        reasons = []
        reasons.append(f"Cartões esperados: {expected:.1f}")
        
        importance = match_data.get("importance_factor", 1.0)
        if importance > 1.2:
            reasons.append("Jogo importante tende a ter mais cartões")
        
        if direction == "over":
            reasons.append(f"Mais de {line} cartões esperados")
        else:
            reasons.append(f"Menos de {line} cartões esperados")
        
        return reasons

# Factory function
def create_multi_market_analyzer(sport: str = "football") -> MultiMarketAnalyzer:
    """Cria analisador de múltiplos mercados"""
    return MultiMarketAnalyzer(sport) 