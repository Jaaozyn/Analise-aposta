"""
Enhanced ML Analyzer - Versão Profissional
Implementação de ensemble de modelos e features avançadas
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss, accuracy_score
import joblib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedValueCalculator:
    """Motor de cálculo de valor esperado com melhorias profissionais"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        
    def calculate_ev_with_confidence(self, probability: float, odds: float, confidence: float) -> Dict:
        """Calcula EV considerando nível de confiança"""
        if probability <= 0 or probability >= 1 or odds <= 1:
            return {"ev": 0.0, "adjusted_ev": 0.0, "risk_level": "high"}
        
        raw_ev = ((probability * (odds - 1)) - (1 - probability)) * 100
        
        # Ajustar EV baseado na confiança
        confidence_factor = max(0.5, confidence)  # Mínimo 50% confiança
        adjusted_ev = raw_ev * confidence_factor
        
        # Classificar risco
        risk_level = self._classify_risk(raw_ev, confidence, odds)
        
        return {
            "ev": raw_ev,
            "adjusted_ev": adjusted_ev,
            "confidence": confidence,
            "risk_level": risk_level,
            "recommendation": self._generate_recommendation(adjusted_ev, confidence)
        }
    
    def calculate_kelly_optimal(self, probability: float, odds: float, bankroll_fraction: float = 0.02) -> float:
        """Kelly Criterion com proteção contra over-betting"""
        if probability <= 0 or odds <= 1:
            return 0.0
        
        # Kelly Criterion: f = (bp - q) / b
        # onde b = odds - 1, p = probability, q = 1 - p
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Aplicar limitações de segurança
        kelly_fraction = max(0, kelly_fraction)  # Nunca negativo
        kelly_fraction = min(kelly_fraction, bankroll_fraction)  # Máximo 2% da banca
        kelly_fraction *= 0.5  # Fractional Kelly (50%) para reduzir volatilidade
        
        # Converter para escala 1-10
        stake_units = kelly_fraction * 50
        return max(0.5, min(stake_units, 10.0))
    
    def _classify_risk(self, ev: float, confidence: float, odds: float) -> str:
        """Classifica nível de risco da aposta"""
        if ev < 3 or confidence < 0.6:
            return "high"
        elif ev < 8 or confidence < 0.75 or odds > 4.0:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation(self, adjusted_ev: float, confidence: float) -> str:
        """Gera recomendação baseada em EV e confiança"""
        if adjusted_ev >= 10 and confidence >= 0.8:
            return "STRONG BUY - Alta confiança e valor"
        elif adjusted_ev >= 5 and confidence >= 0.7:
            return "BUY - Boa oportunidade"
        elif adjusted_ev >= 3 and confidence >= 0.6:
            return "WEAK BUY - Valor marginal"
        else:
            return "PASS - Sem valor suficiente"

class EnsembleFootballAnalyzer(EnhancedValueCalculator):
    """Analisador de futebol com ensemble de modelos"""
    
    def __init__(self):
        super().__init__()
        self.models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'logistic': LogisticRegression(random_state=42)
        }
        self.scaler = StandardScaler()
        
    def analyze_match_advanced(self, match_data: Dict) -> Dict:
        """Análise avançada com ensemble de modelos"""
        
        # Extrair features avançadas
        features = self._extract_advanced_features(match_data)
        
        # Se modelos não estão treinados, usar análise estatística
        if not self._models_trained():
            return self._statistical_analysis(match_data)
        
        # Fazer predições com ensemble
        predictions = self._ensemble_predict(features)
        
        # Calcular confiança baseada na concordância dos modelos
        confidence = self._calculate_model_agreement(predictions)
        
        # Probabilidades finais (média ponderada)
        final_probabilities = {
            "home": np.mean([p["home"] for p in predictions.values()]),
            "draw": np.mean([p["draw"] for p in predictions.values()]),
            "away": np.mean([p["away"] for p in predictions.values()])
        }
        
        # Adicionar metadados de análise
        analysis_metadata = {
            "model_agreement": confidence,
            "feature_importance": self._get_feature_importance(),
            "analysis_timestamp": datetime.now().isoformat(),
            "models_used": list(self.models.keys())
        }
        
        return {
            "probabilities": final_probabilities,
            "confidence": confidence,
            "metadata": analysis_metadata
        }
    
    def _extract_advanced_features(self, match_data: Dict) -> np.ndarray:
        """Extrai features avançadas para ML"""
        features = []
        
        # Features básicas
        features.extend([
            match_data.get("home_avg_goals", 1.5),
            match_data.get("away_avg_goals", 1.5),
            match_data.get("home_avg_conceded", 1.5),
            match_data.get("away_avg_conceded", 1.5)
        ])
        
        # Features de eficiência
        home_goal_diff = match_data.get("home_avg_goals", 1.5) - match_data.get("home_avg_conceded", 1.5)
        away_goal_diff = match_data.get("away_avg_goals", 1.5) - match_data.get("away_avg_conceded", 1.5)
        features.extend([home_goal_diff, away_goal_diff])
        
        # Features de forma recente (ponderada)
        home_form = self._calculate_weighted_form(match_data.get("home_form", ""))
        away_form = self._calculate_weighted_form(match_data.get("away_form", ""))
        features.extend([home_form, away_form])
        
        # Features de força relativa
        relative_strength = home_goal_diff - away_goal_diff
        features.append(relative_strength)
        
        # Features de motivação/contexto
        features.extend([
            match_data.get("home_position", 10) / 20,  # Posição na tabela normalizada
            match_data.get("away_position", 10) / 20,
            match_data.get("importance_factor", 1.0)   # Importância da partida
        ])
        
        # Features de H2H
        h2h_features = self._extract_h2h_features(match_data.get("h2h_data", ""))
        features.extend(h2h_features)
        
        return np.array(features).reshape(1, -1)
    
    def _calculate_weighted_form(self, form_data: str) -> float:
        """Calcula forma recente com peso decrescente para jogos mais antigos"""
        if not form_data:
            return 0.5
        
        try:
            import json
            form = json.loads(form_data) if isinstance(form_data, str) else form_data
            
            if not form:
                return 0.5
            
            # Pesos decrescentes: jogo mais recente tem peso maior
            weights = [0.4, 0.3, 0.2, 0.1][:len(form)]
            
            weighted_score = 0
            total_weight = 0
            
            for i, result in enumerate(form[:4]):  # Últimos 4 jogos
                weight = weights[i] if i < len(weights) else 0.05
                
                if result.get("result") == "W":
                    score = 1.0
                elif result.get("result") == "D":
                    score = 0.5
                else:
                    score = 0.0
                
                weighted_score += score * weight
                total_weight += weight
            
            return weighted_score / total_weight if total_weight > 0 else 0.5
            
        except Exception:
            return 0.5
    
    def _extract_h2h_features(self, h2h_data: str) -> List[float]:
        """Extrai features do histórico H2H"""
        try:
            import json
            h2h = json.loads(h2h_data) if isinstance(h2h_data, str) else h2h_data
            
            if not h2h:
                return [0.5, 0.5, 0.5]
            
            total = len(h2h)
            home_wins = len([r for r in h2h if r.get("winner") == "home"])
            draws = len([r for r in h2h if r.get("winner") == "draw"])
            
            # Normalizar por total de jogos
            return [
                home_wins / total if total > 0 else 0.5,
                draws / total if total > 0 else 0.2,
                (total - home_wins - draws) / total if total > 0 else 0.3
            ]
            
        except Exception:
            return [0.5, 0.2, 0.3]
    
    def _ensemble_predict(self, features: np.ndarray) -> Dict:
        """Faz predições com todos os modelos do ensemble"""
        predictions = {}
        
        for name, model in self.models.items():
            try:
                # Normalizar features se necessário
                if name == 'logistic':
                    features_scaled = self.scaler.transform(features)
                else:
                    features_scaled = features
                
                proba = model.predict_proba(features_scaled)[0]
                
                predictions[name] = {
                    "home": float(proba[0]),
                    "draw": float(proba[1]) if len(proba) > 2 else 0.2,
                    "away": float(proba[-1])
                }
                
            except Exception as e:
                logger.warning(f"Erro na predição do modelo {name}: {e}")
                # Fallback para probabilidades neutras
                predictions[name] = {"home": 0.4, "draw": 0.25, "away": 0.35}
        
        return predictions
    
    def _calculate_model_agreement(self, predictions: Dict) -> float:
        """Calcula concordância entre modelos (confidence score)"""
        if not predictions:
            return 0.5
        
        # Calcular variância das predições
        home_preds = [p["home"] for p in predictions.values()]
        draw_preds = [p["draw"] for p in predictions.values()]
        away_preds = [p["away"] for p in predictions.values()]
        
        # Baixa variância = alta concordância = alta confiança
        avg_variance = (
            np.var(home_preds) + 
            np.var(draw_preds) + 
            np.var(away_preds)
        ) / 3
        
        # Converter variância em score de confiança (0-1)
        confidence = max(0.3, 1 - (avg_variance * 10))
        
        return min(1.0, confidence)
    
    def _statistical_analysis(self, match_data: Dict) -> Dict:
        """Análise estatística quando modelos ML não estão disponíveis"""
        
        # Força dos times
        home_strength = match_data.get("home_avg_goals", 1.5) / max(match_data.get("home_avg_conceded", 1.5), 0.1)
        away_strength = match_data.get("away_avg_goals", 1.5) / max(match_data.get("away_avg_conceded", 1.5), 0.1)
        
        # Aplicar fator casa
        home_strength *= 1.15
        
        # Ajustes por forma recente
        home_form = self._calculate_weighted_form(match_data.get("home_form", ""))
        away_form = self._calculate_weighted_form(match_data.get("away_form", ""))
        
        home_strength *= (0.5 + home_form)
        away_strength *= (0.5 + away_form)
        
        # Normalizar probabilidades
        total_strength = home_strength + away_strength + 1.0
        
        probabilities = {
            "home": home_strength / total_strength,
            "draw": 1.0 / total_strength,
            "away": away_strength / total_strength
        }
        
        # Confidence baseada na diferença de força
        strength_diff = abs(home_strength - away_strength)
        confidence = min(0.9, 0.6 + (strength_diff * 0.1))
        
        return {
            "probabilities": probabilities,
            "confidence": confidence,
            "metadata": {
                "method": "statistical",
                "home_strength": home_strength,
                "away_strength": away_strength
            }
        }
    
    def _models_trained(self) -> bool:
        """Verifica se os modelos estão treinados"""
        # Simplificado - em produção, verificar se modelos existem no disco
        return False
    
    def _get_feature_importance(self) -> Dict:
        """Retorna importância das features (quando disponível)"""
        return {
            "goals_avg": 0.25,
            "form_recent": 0.20,
            "home_advantage": 0.15,
            "goal_difference": 0.15,
            "h2h": 0.10,
            "position": 0.10,
            "context": 0.05
        }

# Factory melhorada
def create_enhanced_analyzer(sport: str):
    """Factory para criar analisador melhorado"""
    sport = sport.lower()
    
    if sport == "football":
        return EnsembleFootballAnalyzer()
    elif sport == "basketball":
        # TODO: Implementar EnsembleBasketballAnalyzer
        return EnhancedValueCalculator()
    elif sport in ["cs2", "valorant"]:
        # TODO: Implementar EnsembleEsportsAnalyzer
        return EnhancedValueCalculator()
    else:
        return EnhancedValueCalculator() 