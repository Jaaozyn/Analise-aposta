from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from enum import Enum

class PlanType(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    PRO = "pro"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"
    FAILED = "failed"

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    MERCADOPAGO = "mercadopago"
    PAYPAL = "paypal"
    BINANCE = "binance"

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Plano
    plan_type = Column(String, nullable=False)  # PlanType
    price = Column(Float, nullable=False)
    currency = Column(String, default="BRL")
    
    # Status
    status = Column(String, default=SubscriptionStatus.PENDING)
    is_active = Column(Boolean, default=False)
    
    # Período
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    
    # Pagamento
    payment_provider = Column(String)  # PaymentProvider
    external_subscription_id = Column(String)  # ID no gateway de pagamento
    external_customer_id = Column(String)
    
    # Renovação automática
    auto_renew = Column(Boolean, default=True)
    next_billing_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    
    # Valor
    amount = Column(Float, nullable=False)
    currency = Column(String, default="BRL")
    
    # Status
    status = Column(String, nullable=False)  # "pending", "completed", "failed", "refunded"
    
    # Pagamento
    payment_provider = Column(String, nullable=False)
    external_payment_id = Column(String)  # ID da transação no gateway
    payment_method = Column(String)  # "card", "pix", "boleto", etc.
    
    # Dados adicionais
    payment_data = Column(Text)  # JSON com dados específicos do gateway
    failure_reason = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    subscription = relationship("Subscription", back_populates="payments")

class Plan(Base):
    """Definição dos planos disponíveis"""
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação
    name = Column(String, nullable=False)  # "Plano Básico", "Plano Premium"
    type = Column(String, nullable=False)  # PlanType
    description = Column(Text)
    
    # Preço
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float)  # Desconto anual
    currency = Column(String, default="BRL")
    
    # Recursos/Limites
    max_daily_picks = Column(Integer, default=5)
    max_sports = Column(Integer, default=2)  # Quantidade de esportes
    advanced_analytics = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    
    # Configurações
    is_active = Column(Boolean, default=True)
    trial_days = Column(Integer, default=0)
    
    # Features específicas (JSON)
    features = Column(Text)  # JSON com lista de features
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 