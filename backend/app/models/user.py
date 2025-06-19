from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    
    # Status da conta
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Gestão de Banca
    initial_bankroll = Column(Float, default=0.0)
    current_bankroll = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    total_bets = Column(Integer, default=0)
    winning_bets = Column(Integer, default=0)
    
    # Preferências
    preferred_sports = Column(Text)  # JSON string com esportes preferidos
    risk_level = Column(String, default="medium")  # low, medium, high
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relacionamentos
    subscriptions = relationship("Subscription", back_populates="user")
    user_picks = relationship("UserPick", back_populates="user")
    
    @property
    def roi(self) -> float:
        """Calcular ROI (Return on Investment)"""
        if self.initial_bankroll > 0:
            return (self.total_profit / self.initial_bankroll) * 100
        return 0.0
    
    @property
    def win_rate(self) -> float:
        """Calcular taxa de acerto"""
        if self.total_bets > 0:
            return (self.winning_bets / self.total_bets) * 100
        return 0.0 