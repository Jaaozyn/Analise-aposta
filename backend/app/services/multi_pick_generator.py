"""
Multi Pick Generator - Gerador de Múltiplos Picks
Sempre retorna 5 picks por partida + destaque para EV+
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class MarketType(Enum):
    """Tipos de mercado disponíveis"""
    MATCH_RESULT = "match_result"
    OVER_UNDER = "over_under"
    BOTH_TEAMS_SCORE = "both_teams_score"
    HANDICAP = "handicap"
    FIRST_HALF = "first_half"
    CLEAN_SHEET = "clean_sheet"
    CORNERS = "corners"
    CARDS = "cards"

@dataclass
class PickResult:
    """Resultado de um pick"""
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
    priority_score: float  # Para ranking

class MultiPickGenerator:
    """Gerador que sempre retorna 5 picks por partida"""
    
    def __init__(self):
        self.min_picks_per_match = 5
        
    async def generate_picks_for_match(self, match_data: Dict, market_odds: Dict) -> Dict:
        """
        Gera picks para uma partida - SEMPRE 5 picks
        
        Returns:
            {
                "value_picks": [...],      # Picks com EV+
                "top_picks": [...],        # Top 5 sempre
                "all_picks": [...],        # Todos analisados
                "summary": {...}           # Resumo
            }
        """
        
        # Gerar todos os picks possíveis
        all_picks = []
        
        # 1. Match Result (1X2)
        match_result_picks = self._generate_match_result_picks(match_data, market_odds)
        all_picks.extend(match_result_picks)
        
        # 2. Over/Under Goals
        goals_picks = self._generate_over_under_picks(match_data, market_odds)
        all_picks.extend(goals_picks)
        
        # 3. Both Teams Score
        bts_picks = self._generate_bts_picks(match_data, market_odds)
        all_picks.extend(bts_picks)
        
        # 4. Handicap
        handicap_picks = self._generate_handicap_picks(match_data, market_odds)
        all_picks.extend(handicap_picks)
        
        # 5. First Half
        first_half_picks = self._generate_first_half_picks(match_data, market_odds)
        all_picks.extend(first_half_picks)
        
        # 6. Clean Sheet
        clean_sheet_picks = self._generate_clean_sheet_picks(match_data, market_odds)
        all_picks.extend(clean_sheet_picks)
        
        # Ordenar por prioridade (EV primeiro, depois por confidence)
        all_picks.sort(key=lambda x: x.priority_score, reverse=True)
        
        # Separar picks com valor
        value_picks = [pick for pick in all_picks if pick.is_value_bet]
        
        # Garantir pelo menos 5 picks (top 5)
        top_picks = all_picks[:self.min_picks_per_match]
        
        # Se tiver menos de 5, adicionar mais mercados
        if len(all_picks) < self.min_picks_per_match:
            additional_picks = self._generate_additional_picks(match_data, market_odds)
            all_picks.extend(additional_picks)
            top_picks = all_picks[:self.min_picks_per_match]
        
        return {
            "value_picks": value_picks,
            "top_picks": top_picks,
            "all_picks": all_picks,
            "summary": {
                "total_picks_analyzed": len(all_picks),
                "value_picks_found": len(value_picks),
                "best_ev": value_picks[0].expected_value if value_picks else top_picks[0].expected_value,
                "recommendation": self._get_match_recommendation(value_picks, top_picks)
            }
        }
    
    def _generate_match_result_picks(self, match_data: Dict, market_odds: Dict) -> List[PickResult]:
        """Gera picks para resultado da partida (1X2)"""
        picks = []
        
        # Calcular probabilidades base
        home_strength = self._calculate_team_strength(match_data, "home")
        away_strength = self._calculate_team_strength(match_data, "away")
        
        # Normalizar probabilidades
        total_strength = home_strength + away_strength + 1.0  # +1 para empate
        home_prob = home_strength / total_strength
        away_prob = away_strength / total_strength
        draw_prob = 1.0 / total_strength
        
        # Ajustar para somar 1
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total
        
        confidence = 0.75  # Confidence base para 1X2
        
        # Home Win
        home_odds = market_odds.get("home_win", 2.0)
        home_ev = self._calculate_ev(home_prob, home_odds)
        
        picks.append(PickResult(
            market_type="match_result",
            selection="Vitória Mandante",
            description=f"{match_data.get('home_team', 'Casa')} vence",
            calculated_probability=home_prob,
            market_odds=home_odds,
            expected_value=home_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(home_ev, confidence),
            risk_level=self._classify_risk(home_ev, confidence),
            reasoning=self._get_home_win_reasoning(match_data, home_prob),
            is_value_bet=home_ev >= 5.0,
            market_probability=1/home_odds,
            priority_score=self._calculate_priority(home_ev, confidence)
        ))
        
        # Draw
        draw_odds = market_odds.get("draw", 3.0)
        draw_ev = self._calculate_ev(draw_prob, draw_odds)
        
        picks.append(PickResult(
            market_type="match_result",
            selection="Empate", 
            description="Partida termina empatada",
            calculated_probability=draw_prob,
            market_odds=draw_odds,
            expected_value=draw_ev,
            confidence_score=confidence * 0.9,  # Empate é mais difícil de prever
            stake_suggestion=self._calculate_stake(draw_ev, confidence * 0.9),
            risk_level=self._classify_risk(draw_ev, confidence * 0.9),
            reasoning=self._get_draw_reasoning(match_data, draw_prob),
            is_value_bet=draw_ev >= 5.0,
            market_probability=1/draw_odds,
            priority_score=self._calculate_priority(draw_ev, confidence * 0.9)
        ))
        
        # Away Win
        away_odds = market_odds.get("away_win", 3.5)
        away_ev = self._calculate_ev(away_prob, away_odds)
        
        picks.append(PickResult(
            market_type="match_result", 
            selection="Vitória Visitante",
            description=f"{match_data.get('away_team', 'Fora')} vence",
            calculated_probability=away_prob,
            market_odds=away_odds,
            expected_value=away_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(away_ev, confidence),
            risk_level=self._classify_risk(away_ev, confidence),
            reasoning=self._get_away_win_reasoning(match_data, away_prob),
            is_value_bet=away_ev >= 5.0,
            market_probability=1/away_odds,
            priority_score=self._calculate_priority(away_ev, confidence)
        ))
        
        return picks
    
    def _generate_over_under_picks(self, match_data: Dict, market_odds: Dict) -> List[PickResult]:
        """Gera picks para Over/Under gols"""
        picks = []
        
        # Calcular gols esperados
        home_goals = match_data.get("home_avg_goals", 1.5)
        away_goals = match_data.get("away_avg_goals", 1.5)
        expected_goals = home_goals + away_goals
        
        confidence = 0.80  # Boa confidence para totais
        
        # Over 2.5 Goals
        over_25_prob = self._calculate_over_probability(expected_goals, 2.5)
        over_25_odds = market_odds.get("over_2_5", 2.0)
        over_25_ev = self._calculate_ev(over_25_prob, over_25_odds)
        
        picks.append(PickResult(
            market_type="over_under",
            selection="Over 2.5 Goals",
            description="Mais de 2.5 gols na partida",
            calculated_probability=over_25_prob,
            market_odds=over_25_odds,
            expected_value=over_25_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(over_25_ev, confidence),
            risk_level=self._classify_risk(over_25_ev, confidence),
            reasoning=self._get_over_reasoning(expected_goals, 2.5, match_data),
            is_value_bet=over_25_ev >= 5.0,
            market_probability=1/over_25_odds,
            priority_score=self._calculate_priority(over_25_ev, confidence)
        ))
        
        # Under 2.5 Goals
        under_25_prob = 1 - over_25_prob
        under_25_odds = market_odds.get("under_2_5", 2.0)
        under_25_ev = self._calculate_ev(under_25_prob, under_25_odds)
        
        picks.append(PickResult(
            market_type="over_under",
            selection="Under 2.5 Goals",
            description="Menos de 2.5 gols na partida",
            calculated_probability=under_25_prob,
            market_odds=under_25_odds,
            expected_value=under_25_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(under_25_ev, confidence),
            risk_level=self._classify_risk(under_25_ev, confidence),
            reasoning=self._get_under_reasoning(expected_goals, 2.5, match_data),
            is_value_bet=under_25_ev >= 5.0,
            market_probability=1/under_25_odds,
            priority_score=self._calculate_priority(under_25_ev, confidence)
        ))
        
        return picks
    
    def _generate_bts_picks(self, match_data: Dict, market_odds: Dict) -> List[PickResult]:
        """Gera picks para Ambos Marcam"""
        picks = []
        
        # Probabilidade de cada time marcar
        home_score_prob = self._team_scores_probability(match_data, "home")
        away_score_prob = self._team_scores_probability(match_data, "away")
        
        # Ambos marcam = P(Home marca) × P(Away marca)
        bts_yes_prob = home_score_prob * away_score_prob
        bts_no_prob = 1 - bts_yes_prob
        
        confidence = 0.75
        
        # Both Teams Score - Yes
        bts_yes_odds = market_odds.get("bts_yes", 1.8)
        bts_yes_ev = self._calculate_ev(bts_yes_prob, bts_yes_odds)
        
        picks.append(PickResult(
            market_type="both_teams_score",
            selection="Ambos Marcam - Sim",
            description="Ambos os times marcam",
            calculated_probability=bts_yes_prob,
            market_odds=bts_yes_odds,
            expected_value=bts_yes_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(bts_yes_ev, confidence),
            risk_level=self._classify_risk(bts_yes_ev, confidence),
            reasoning=self._get_bts_yes_reasoning(match_data, home_score_prob, away_score_prob),
            is_value_bet=bts_yes_ev >= 5.0,
            market_probability=1/bts_yes_odds,
            priority_score=self._calculate_priority(bts_yes_ev, confidence)
        ))
        
        # Both Teams Score - No
        bts_no_odds = market_odds.get("bts_no", 2.2)
        bts_no_ev = self._calculate_ev(bts_no_prob, bts_no_odds)
        
        picks.append(PickResult(
            market_type="both_teams_score",
            selection="Ambos Marcam - Não",
            description="Pelo menos um time não marca",
            calculated_probability=bts_no_prob,
            market_odds=bts_no_odds,
            expected_value=bts_no_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(bts_no_ev, confidence),
            risk_level=self._classify_risk(bts_no_ev, confidence),
            reasoning=self._get_bts_no_reasoning(match_data, bts_no_prob),
            is_value_bet=bts_no_ev >= 5.0,
            market_probability=1/bts_no_odds,
            priority_score=self._calculate_priority(bts_no_ev, confidence)
        ))
        
        return picks
    
    def _generate_handicap_picks(self, match_data: Dict, market_odds: Dict) -> List[PickResult]:
        """Gera picks para Handicap"""
        picks = []
        
        # Calcular diferença de força para definir handicap
        home_strength = self._calculate_team_strength(match_data, "home")
        away_strength = self._calculate_team_strength(match_data, "away")
        strength_diff = home_strength - away_strength
        
        # Definir handicap baseado na diferença
        if strength_diff > 0.3:
            handicap = -0.5  # Home favorito
        elif strength_diff < -0.3:
            handicap = 0.5   # Away favorito
        else:
            handicap = 0.0   # Equilibrado
        
        # Calcular probabilidade ajustada
        adjusted_prob = self._adjust_prob_for_handicap(match_data, handicap)
        
        handicap_odds = market_odds.get(f"handicap_{handicap}", 2.0)
        handicap_ev = self._calculate_ev(adjusted_prob, handicap_odds)
        
        confidence = 0.70  # Handicap é mais complexo
        
        picks.append(PickResult(
            market_type="handicap",
            selection=f"Handicap {handicap:+.1f}",
            description=f"Mandante com handicap {handicap:+.1f}",
            calculated_probability=adjusted_prob,
            market_odds=handicap_odds,
            expected_value=handicap_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(handicap_ev, confidence),
            risk_level=self._classify_risk(handicap_ev, confidence),
            reasoning=self._get_handicap_reasoning(match_data, handicap, strength_diff),
            is_value_bet=handicap_ev >= 5.0,
            market_probability=1/handicap_odds,
            priority_score=self._calculate_priority(handicap_ev, confidence)
        ))
        
        return picks
    
    def _generate_first_half_picks(self, match_data: Dict, market_odds: Dict) -> List[PickResult]:
        """Gera picks para Primeiro Tempo"""
        picks = []
        
        # Primeiro tempo é mais equilibrado
        home_strength = self._calculate_team_strength(match_data, "home") * 0.8
        away_strength = self._calculate_team_strength(match_data, "away") * 0.8
        
        total_strength = home_strength + away_strength + 1.5  # Mais chance de empate
        ht_home_prob = home_strength / total_strength
        ht_draw_prob = 1.5 / total_strength  # Empate mais provável
        ht_away_prob = away_strength / total_strength
        
        confidence = 0.65  # Menor confidence para HT
        
        # HT Draw (mais provável)
        ht_draw_odds = market_odds.get("ht_draw", 2.5)
        ht_draw_ev = self._calculate_ev(ht_draw_prob, ht_draw_odds)
        
        picks.append(PickResult(
            market_type="first_half",
            selection="1º Tempo - Empate",
            description="Empate no primeiro tempo",
            calculated_probability=ht_draw_prob,
            market_odds=ht_draw_odds,
            expected_value=ht_draw_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(ht_draw_ev, confidence),
            risk_level=self._classify_risk(ht_draw_ev, confidence),
            reasoning=self._get_ht_reasoning(match_data, ht_draw_prob),
            is_value_bet=ht_draw_ev >= 5.0,
            market_probability=1/ht_draw_odds,
            priority_score=self._calculate_priority(ht_draw_ev, confidence)
        ))
        
        return picks
    
    def _generate_clean_sheet_picks(self, match_data: Dict, market_odds: Dict) -> List[PickResult]:
        """Gera picks para Clean Sheet"""
        picks = []
        
        # Probabilidade de clean sheet baseada na defesa
        home_cs_prob = self._calculate_clean_sheet_prob(match_data, "home")
        away_cs_prob = self._calculate_clean_sheet_prob(match_data, "away")
        
        confidence = 0.70
        
        # Escolher o melhor clean sheet
        if home_cs_prob > away_cs_prob:
            cs_prob = home_cs_prob
            team = "Mandante"
            cs_odds = market_odds.get("home_clean_sheet", 3.0)
        else:
            cs_prob = away_cs_prob
            team = "Visitante"
            cs_odds = market_odds.get("away_clean_sheet", 3.5)
        
        cs_ev = self._calculate_ev(cs_prob, cs_odds)
        
        picks.append(PickResult(
            market_type="clean_sheet",
            selection=f"Clean Sheet - {team}",
            description=f"{team} não sofre gols",
            calculated_probability=cs_prob,
            market_odds=cs_odds,
            expected_value=cs_ev,
            confidence_score=confidence,
            stake_suggestion=self._calculate_stake(cs_ev, confidence),
            risk_level=self._classify_risk(cs_ev, confidence),
            reasoning=self._get_cs_reasoning(match_data, team, cs_prob),
            is_value_bet=cs_ev >= 5.0,
            market_probability=1/cs_odds,
            priority_score=self._calculate_priority(cs_ev, confidence)
        ))
        
        return picks
    
    def _generate_additional_picks(self, match_data: Dict, market_odds: Dict) -> List[PickResult]:
        """Gera picks adicionais se necessário para atingir 5"""
        picks = []
        
        # Corners
        expected_corners = self._calculate_expected_corners(match_data)
        corners_over_prob = self._calculate_over_probability(expected_corners, 9.5)
        corners_odds = market_odds.get("corners_over_9_5", 2.0)
        corners_ev = self._calculate_ev(corners_over_prob, corners_odds)
        
        picks.append(PickResult(
            market_type="corners",
            selection="Over 9.5 Escanteios",
            description="Mais de 9.5 escanteios na partida",
            calculated_probability=corners_over_prob,
            market_odds=corners_odds,
            expected_value=corners_ev,
            confidence_score=0.60,  # Baixa confidence
            stake_suggestion=self._calculate_stake(corners_ev, 0.60),
            risk_level=self._classify_risk(corners_ev, 0.60),
            reasoning=["Estimativa baseada no estilo de jogo dos times", f"Escanteios esperados: {expected_corners:.1f}"],
            is_value_bet=corners_ev >= 5.0,
            market_probability=1/corners_odds,
            priority_score=self._calculate_priority(corners_ev, 0.60)
        ))
        
        # Cards
        expected_cards = self._calculate_expected_cards(match_data)
        cards_over_prob = self._calculate_over_probability(expected_cards, 4.5)
        cards_odds = market_odds.get("cards_over_4_5", 2.2)
        cards_ev = self._calculate_ev(cards_over_prob, cards_odds)
        
        picks.append(PickResult(
            market_type="cards",
            selection="Over 4.5 Cartões", 
            description="Mais de 4.5 cartões na partida",
            calculated_probability=cards_over_prob,
            market_odds=cards_odds,
            expected_value=cards_ev,
            confidence_score=0.55,  # Muito baixa confidence
            stake_suggestion=self._calculate_stake(cards_ev, 0.55),
            risk_level=self._classify_risk(cards_ev, 0.55),
            reasoning=["Estimativa baseada na importância da partida", f"Cartões esperados: {expected_cards:.1f}"],
            is_value_bet=cards_ev >= 5.0,
            market_probability=1/cards_odds,
            priority_score=self._calculate_priority(cards_ev, 0.55)
        ))
        
        return picks
    
    # Métodos auxiliares de cálculo
    def _calculate_team_strength(self, match_data: Dict, team: str) -> float:
        """Calcula força do time"""
        if team == "home":
            goals_for = match_data.get("home_avg_goals", 1.5)
            goals_against = match_data.get("home_avg_conceded", 1.5)
            home_boost = 1.15  # Fator casa
        else:
            goals_for = match_data.get("away_avg_goals", 1.5)
            goals_against = match_data.get("away_avg_conceded", 1.5)
            home_boost = 1.0
        
        # Força = (ataque / defesa_oponente) × home_boost
        strength = (goals_for / max(goals_against, 0.1)) * home_boost
        return strength
    
    def _calculate_ev(self, probability: float, odds: float) -> float:
        """Calcula Expected Value"""
        if probability <= 0 or odds <= 1:
            return -100.0
        
        ev = ((probability * (odds - 1)) - (1 - probability)) * 100
        return ev
    
    def _calculate_stake(self, ev: float, confidence: float) -> float:
        """Calcula stake sugerido"""
        if ev < 0:
            return 0.0
        
        # Kelly modificado
        kelly = (ev / 100) * confidence * 0.5  # Fractional Kelly
        stake_units = kelly * 50  # Converter para escala 1-10
        return max(0.0, min(stake_units, 10.0))
    
    def _classify_risk(self, ev: float, confidence: float) -> str:
        """Classifica risco"""
        if ev >= 8 and confidence >= 0.75:
            return "low"
        elif ev >= 3 and confidence >= 0.65:
            return "medium"
        else:
            return "high"
    
    def _calculate_priority(self, ev: float, confidence: float) -> float:
        """Calcula score de prioridade para ranking"""
        if ev >= 5.0:  # Value bet
            return ev * confidence * 2  # Boost para value bets
        else:
            return ev * confidence  # Score normal
    
    def _calculate_over_probability(self, expected: float, line: float) -> float:
        """Calcula probabilidade Over usando Poisson"""
        # Simplificado - em produção usaria scipy.stats.poisson
        if expected <= line:
            return 0.35  # Baixa chance
        elif expected > line + 1:
            return 0.65  # Alta chance
        else:
            return 0.50  # Equilibrado
    
    def _team_scores_probability(self, match_data: Dict, team: str) -> float:
        """Probabilidade de um time marcar"""
        if team == "home":
            goals_avg = match_data.get("home_avg_goals", 1.5)
        else:
            goals_avg = match_data.get("away_avg_goals", 1.5)
        
        # Simplificação: P(score) = 1 - P(0 goals)
        # P(0 goals) ≈ e^(-λ) onde λ = goals_avg
        import math
        prob_no_goals = math.exp(-goals_avg)
        return 1 - prob_no_goals
    
    def _adjust_prob_for_handicap(self, match_data: Dict, handicap: float) -> float:
        """Ajusta probabilidade para handicap"""
        # Simplificação baseada no handicap
        base_home_prob = 0.45  # Probabilidade base casa
        
        if handicap == 0:
            return base_home_prob + 0.25  # Empate = meio ganho
        elif handicap > 0:
            return base_home_prob + (handicap * 0.2)  # Boost para handicap positivo
        else:
            return base_home_prob + (handicap * 0.2)  # Penalidade para handicap negativo
    
    def _calculate_clean_sheet_prob(self, match_data: Dict, team: str) -> float:
        """Probabilidade de clean sheet"""
        if team == "home":
            goals_conceded = match_data.get("home_avg_conceded", 1.5)
        else:
            goals_conceded = match_data.get("away_avg_conceded", 1.5)
        
        # P(clean sheet) = P(0 goals sofridos)
        import math
        return math.exp(-goals_conceded)
    
    def _calculate_expected_corners(self, match_data: Dict) -> float:
        """Estima escanteios"""
        home_attack = match_data.get("home_avg_goals", 1.5)
        away_attack = match_data.get("away_avg_goals", 1.5)
        return (home_attack + away_attack) * 2.5 + 2
    
    def _calculate_expected_cards(self, match_data: Dict) -> float:
        """Estima cartões"""
        importance = match_data.get("importance_factor", 1.0)
        return 4.0 * importance
    
    def _get_match_recommendation(self, value_picks: List[PickResult], top_picks: List[PickResult]) -> str:
        """Gera recomendação da partida"""
        if len(value_picks) >= 3:
            return "🔥 EXCELENTE - Múltiplas oportunidades de valor"
        elif len(value_picks) >= 2:
            return "✅ BOM - Algumas oportunidades sólidas"
        elif len(value_picks) >= 1:
            return "⚠️ MODERADO - Uma oportunidade de valor"
        else:
            return "❌ EVITAR - Nenhum valor matemático encontrado"
    
    # Métodos de reasoning
    def _get_home_win_reasoning(self, match_data: Dict, prob: float) -> List[str]:
        return [
            f"Probabilidade calculada: {prob*100:.1f}%",
            "Vantagem de jogar em casa (+15%)",
            f"Força ofensiva: {match_data.get('home_avg_goals', 1.5):.1f} gols/jogo"
        ]
    
    def _get_draw_reasoning(self, match_data: Dict, prob: float) -> List[str]:
        return [
            f"Probabilidade de empate: {prob*100:.1f}%",
            "Times equilibrados em força",
            "Resultado comum neste tipo de confronto"
        ]
    
    def _get_away_win_reasoning(self, match_data: Dict, prob: float) -> List[str]:
        return [
            f"Probabilidade calculada: {prob*100:.1f}%",
            f"Ataque visitante: {match_data.get('away_avg_goals', 1.5):.1f} gols/jogo",
            "Superando desvantagem de jogar fora"
        ]
    
    def _get_over_reasoning(self, expected: float, line: float, match_data: Dict) -> List[str]:
        return [
            f"Gols esperados: {expected:.1f}",
            f"Linha Over {line}",
            f"Média combinada: {match_data.get('home_avg_goals', 1.5) + match_data.get('away_avg_goals', 1.5):.1f}"
        ]
    
    def _get_under_reasoning(self, expected: float, line: float, match_data: Dict) -> List[str]:
        return [
            f"Gols esperados: {expected:.1f}",
            f"Linha Under {line}",
            "Defesas sólidas favorecem Under"
        ]
    
    def _get_bts_yes_reasoning(self, match_data: Dict, home_prob: float, away_prob: float) -> List[str]:
        return [
            f"Casa marca: {home_prob*100:.1f}%",
            f"Fora marca: {away_prob*100:.1f}%",
            "Ambos ataques efetivos"
        ]
    
    def _get_bts_no_reasoning(self, match_data: Dict, prob: float) -> List[str]:
        return [
            f"Probabilidade: {prob*100:.1f}%",
            "Defesas sólidas ou ataques ineficazes",
            "Pelo menos um não marca"
        ]
    
    def _get_handicap_reasoning(self, match_data: Dict, handicap: float, strength_diff: float) -> List[str]:
        return [
            f"Handicap: {handicap:+.1f}",
            f"Diferença de força: {strength_diff:.2f}",
            "Ajuste baseado na diferença de qualidade"
        ]
    
    def _get_ht_reasoning(self, match_data: Dict, prob: float) -> List[str]:
        return [
            f"Probabilidade empate 1ºT: {prob*100:.1f}%",
            "Primeiro tempo mais cauteloso",
            "Times se estudam no início"
        ]
    
    def _get_cs_reasoning(self, match_data: Dict, team: str, prob: float) -> List[str]:
        return [
            f"Probabilidade clean sheet: {prob*100:.1f}%",
            f"{team} com defesa sólida",
            "Baseado na média de gols sofridos"
        ] 