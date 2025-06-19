from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from enum import Enum

class PickStatus(str, Enum):
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    VOID = "void"
    PENDING = "pending"

class MarketType(str, Enum):
    WINNER = "winner"
    HANDICAP = "handicap"
    TOTAL = "total"
    BOTH_TEAMS_SCORE = "both_teams_score"
    CORRECT_SCORE = "correct_score"
    FIRST_HALF = "first_half"
    MAP_WINNER = "map_winner"  # E-sports

class Pick(Base):
    __tablename__ = "picks"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    
    # Informações da dica
    market = Column(String, nullable=False)  # MarketType
    selection = Column(String, nullable=False)  # Ex: "Team A", "Over 2.5", etc.
    
    # Análise de valor
    calculated_probability = Column(Float, nullable=False)  # Prob. calculada pelo modelo
    market_probability = Column(Float, nullable=False)     # Prob. implícita da odd
    expected_value = Column(Float, nullable=False)         # EV% da aposta
    confidence_score = Column(Float, nullable=False)       # Nível de confiança (0-1)
    
    # Recomendações
    min_odds = Column(Float, nullable=False)               # Odd mínima para manter EV+
    suggested_stake = Column(Float, nullable=False)        # Unidades sugeridas (0-10)
    max_stake = Column(Float, nullable=False)              # Máximo recomendado
    
    # Status e resultado
    status = Column(String, default=PickStatus.ACTIVE)
    result = Column(String)  # "win", "loss", "void"
    closing_odds = Column(Float)  # Odd final encontrada pelo usuário
    
    # Justificativa (dados para mostrar ao usuário)
    analysis_data = Column(Text)  # JSON com fatores de análise
    confidence_factors = Column(Text)  # JSON com motivos da confiança
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # Quando a dica expira
    
    # Relacionamentos
    match = relationship("Match", back_populates="picks")
    user_picks = relationship("UserPick", back_populates="pick")
    
    @property
    def ev_percentage(self) -> str:
        """Retorna EV formatado como percentual"""
        return f"{self.expected_value:.1f}%"
    
    @property
    def confidence_percentage(self) -> str:
        """Retorna confiança formatada como percentual"""
        return f"{self.confidence_score * 100:.0f}%"

class UserPick(Base):
    """Registro de quando um usuário segue uma dica"""
    __tablename__ = "user_picks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    pick_id = Column(Integer, ForeignKey("picks.id"))
    
    # Detalhes da aposta do usuário
    stake_amount = Column(Float, nullable=False)  # Valor apostado
    odds_taken = Column(Float, nullable=False)    # Odd que o usuário conseguiu
    potential_profit = Column(Float, nullable=False)  # Lucro potencial
    
    # Resultado
    is_settled = Column(Boolean, default=False)
    actual_profit = Column(Float, default=0.0)  # Lucro/prejuízo real
    
    # Timestamps
    placed_at = Column(DateTime(timezone=True), server_default=func.now())
    settled_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    user = relationship("User", back_populates="user_picks")
    pick = relationship("Pick", back_populates="user_picks") 