from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from enum import Enum

class SportType(str, Enum):
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    CS2 = "cs2"
    VALORANT = "valorant"

class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID da API externa
    
    # Informações básicas
    sport = Column(String, nullable=False)  # SportType
    league = Column(String, nullable=False)
    season = Column(String)
    
    # Times/Equipes
    team_home = Column(String, nullable=False)
    team_away = Column(String, nullable=False)
    team_home_id = Column(String)
    team_away_id = Column(String)
    
    # Data e status
    match_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default=MatchStatus.SCHEDULED)
    
    # Resultados (preenchidos após a partida)
    score_home = Column(Integer)
    score_away = Column(Integer)
    winner = Column(String)  # "home", "away", "draw"
    
    # Dados para análise
    home_form = Column(Text)  # JSON com últimos resultados
    away_form = Column(Text)  # JSON com últimos resultados
    h2h_data = Column(Text)   # JSON com histórico H2H
    
    # Estatísticas específicas por esporte
    # Futebol/Basquete
    home_avg_goals = Column(Float)
    away_avg_goals = Column(Float)
    home_avg_conceded = Column(Float)
    away_avg_conceded = Column(Float)
    
    # E-sports
    map_pool = Column(Text)   # JSON com mapas/arenas
    format_info = Column(String)  # BO1, BO3, BO5, etc.
    
    # Odds e análise
    has_analysis = Column(Boolean, default=False)
    analysis_completed = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    picks = relationship("Pick", back_populates="match")
    odds = relationship("MatchOdds", back_populates="match")

class MatchOdds(Base):
    __tablename__ = "match_odds"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    
    # Casa de apostas
    bookmaker = Column(String, nullable=False)
    market = Column(String, nullable=False)  # "winner", "handicap", "total", etc.
    
    # Odds
    home_odds = Column(Float)
    away_odds = Column(Float)
    draw_odds = Column(Float)
    
    # Para mercados especiais
    line = Column(Float)  # Handicap ou linha de totais
    over_odds = Column(Float)
    under_odds = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    match = relationship("Match", back_populates="odds") 