import stripe
import mercadopago
import paypalrestsdk
from typing import Dict, Optional, Any
from enum import Enum
from decimal import Decimal
import logging

from app.core.config import settings
from app.models.subscription import Payment, PaymentProvider
from app.models.user import User

logger = logging.getLogger(__name__)

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentService:
    """Serviço unificado de pagamentos"""
    
    def __init__(self):
        self._setup_providers()
    
    def _setup_providers(self):
        """Configurar provedores de pagamento"""
        # Stripe
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # MercadoPago
        if settings.MERCADOPAGO_ACCESS_TOKEN:
            self.mp = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        # PayPal
        if settings.PAYPAL_CLIENT_ID and settings.PAYPAL_CLIENT_SECRET:
            paypalrestsdk.configure({
                "mode": settings.PAYPAL_MODE,
                "client_id": settings.PAYPAL_CLIENT_ID,
                "client_secret": settings.PAYPAL_CLIENT_SECRET
            })
    
    async def create_payment_intent(
        self,
        amount: float,
        currency: str,
        provider: PaymentProvider,
        user: User,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Criar intenção de pagamento"""
        
        try:
            if provider == PaymentProvider.STRIPE:
                return await self._create_stripe_payment(amount, currency, user, metadata)
            
            elif provider == PaymentProvider.MERCADOPAGO:
                return await self._create_mercadopago_payment(amount, currency, user, metadata)
            
            elif provider == PaymentProvider.PAYPAL:
                return await self._create_paypal_payment(amount, currency, user, metadata)
            
            elif provider == PaymentProvider.BINANCE:
                return await self._create_binance_payment(amount, currency, user, metadata)
            
            else:
                raise ValueError(f"Provider {provider} não suportado")
                
        except Exception as e:
            logger.error(f"Erro ao criar payment intent: {e}")
            raise
    
    async def _create_stripe_payment(
        self, 
        amount: float, 
        currency: str, 
        user: User, 
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Criar pagamento Stripe"""
        
        try:
            # Converter para centavos
            amount_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                customer=user.email,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            
            return {
                "provider": PaymentProvider.STRIPE,
                "payment_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": amount,
                "currency": currency,
                "payment_url": None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erro Stripe: {e}")
            raise
    
    async def _create_mercadopago_payment(
        self, 
        amount: float, 
        currency: str, 
        user: User, 
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Criar pagamento MercadoPago (PIX, Cartão, Boleto)"""
        
        try:
            preference_data = {
                "items": [
                    {
                        "title": "Assinatura QuantumBet",
                        "quantity": 1,
                        "unit_price": float(amount),
                        "currency_id": currency
                    }
                ],
                "payer": {
                    "name": user.full_name or user.username,
                    "email": user.email
                },
                "payment_methods": {
                    "excluded_payment_methods": [],
                    "excluded_payment_types": [],
                    "installments": 12
                },
                "back_urls": {
                    "success": f"{settings.FRONTEND_URL}/payment/success",
                    "failure": f"{settings.FRONTEND_URL}/payment/failure",
                    "pending": f"{settings.FRONTEND_URL}/payment/pending"
                },
                "auto_return": "approved",
                "external_reference": metadata.get("subscription_id") if metadata else None
            }
            
            preference_response = self.mp.preference().create(preference_data)
            preference = preference_response["response"]
            
            return {
                "provider": PaymentProvider.MERCADOPAGO,
                "payment_id": preference["id"],
                "client_secret": None,
                "status": "pending",
                "amount": amount,
                "currency": currency,
                "payment_url": preference["init_point"],
                "sandbox_url": preference.get("sandbox_init_point")
            }
            
        except Exception as e:
            logger.error(f"Erro MercadoPago: {e}")
            raise
    
    async def _create_paypal_payment(
        self, 
        amount: float, 
        currency: str, 
        user: User, 
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Criar pagamento PayPal"""
        
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": f"{settings.FRONTEND_URL}/payment/paypal/success",
                    "cancel_url": f"{settings.FRONTEND_URL}/payment/paypal/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "Assinatura QuantumBet",
                            "sku": "quantum-subscription",
                            "price": str(amount),
                            "currency": currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": "Assinatura mensal QuantumBet"
                }]
            })
            
            if payment.create():
                # Extrair URL de aprovação
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return {
                    "provider": PaymentProvider.PAYPAL,
                    "payment_id": payment.id,
                    "client_secret": None,
                    "status": payment.state,
                    "amount": amount,
                    "currency": currency,
                    "payment_url": approval_url
                }
            else:
                raise Exception(f"Erro ao criar pagamento PayPal: {payment.error}")
                
        except Exception as e:
            logger.error(f"Erro PayPal: {e}")
            raise
    
    async def _create_binance_payment(
        self, 
        amount: float, 
        currency: str, 
        user: User, 
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Criar pagamento Binance Pay (Crypto)"""
        
        # Implementação simplificada - na prática precisaria da API oficial
        try:
            # Converter para USDT (exemplo)
            usdt_amount = amount / 5.0  # Taxa de conversão fictícia
            
            return {
                "provider": PaymentProvider.BINANCE,
                "payment_id": f"binance_{user.id}_{int(amount * 100)}",
                "client_secret": None,
                "status": "pending",
                "amount": usdt_amount,
                "currency": "USDT",
                "payment_url": f"https://pay.binance.com/checkout/{user.id}",
                "crypto_address": "0x742d35Cc6639C0532fDb81776a1C1f0e2A0D00F3",  # Fictício
                "crypto_amount": usdt_amount
            }
            
        except Exception as e:
            logger.error(f"Erro Binance Pay: {e}")
            raise
    
    async def verify_payment(
        self, 
        payment_id: str, 
        provider: PaymentProvider
    ) -> Dict[str, Any]:
        """Verificar status de pagamento"""
        
        try:
            if provider == PaymentProvider.STRIPE:
                return await self._verify_stripe_payment(payment_id)
            
            elif provider == PaymentProvider.MERCADOPAGO:
                return await self._verify_mercadopago_payment(payment_id)
            
            elif provider == PaymentProvider.PAYPAL:
                return await self._verify_paypal_payment(payment_id)
            
            elif provider == PaymentProvider.BINANCE:
                return await self._verify_binance_payment(payment_id)
            
            else:
                raise ValueError(f"Provider {provider} não suportado")
                
        except Exception as e:
            logger.error(f"Erro ao verificar pagamento: {e}")
            raise
    
    async def _verify_stripe_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verificar pagamento Stripe"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_id)
            return {
                "payment_id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency.upper(),
                "paid": intent.status == "succeeded"
            }
        except stripe.error.StripeError as e:
            logger.error(f"Erro ao verificar Stripe: {e}")
            raise
    
    async def _verify_mercadopago_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verificar pagamento MercadoPago"""
        try:
            payment_response = self.mp.payment().get(payment_id)
            payment = payment_response["response"]
            
            return {
                "payment_id": payment["id"],
                "status": payment["status"],
                "amount": payment["transaction_amount"],
                "currency": payment["currency_id"],
                "paid": payment["status"] == "approved"
            }
        except Exception as e:
            logger.error(f"Erro ao verificar MercadoPago: {e}")
            raise
    
    async def _verify_paypal_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verificar pagamento PayPal"""
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            return {
                "payment_id": payment.id,
                "status": payment.state,
                "amount": float(payment.transactions[0].amount.total),
                "currency": payment.transactions[0].amount.currency,
                "paid": payment.state == "approved"
            }
        except Exception as e:
            logger.error(f"Erro ao verificar PayPal: {e}")
            raise
    
    async def _verify_binance_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verificar pagamento Binance Pay"""
        # Implementação simplificada
        return {
            "payment_id": payment_id,
            "status": "pending",
            "amount": 0,
            "currency": "USDT",
            "paid": False
        }
    
    async def refund_payment(
        self, 
        payment_id: str, 
        provider: PaymentProvider,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Estornar pagamento"""
        
        try:
            if provider == PaymentProvider.STRIPE:
                return await self._refund_stripe_payment(payment_id, amount)
            
            elif provider == PaymentProvider.MERCADOPAGO:
                return await self._refund_mercadopago_payment(payment_id, amount)
            
            else:
                raise ValueError(f"Estorno não suportado para {provider}")
                
        except Exception as e:
            logger.error(f"Erro ao estornar pagamento: {e}")
            raise
    
    async def _refund_stripe_payment(
        self, 
        payment_id: str, 
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Estornar pagamento Stripe"""
        try:
            refund_data = {"payment_intent": payment_id}
            if amount:
                refund_data["amount"] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_data)
            
            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,
                "currency": refund.currency.upper()
            }
        except stripe.error.StripeError as e:
            logger.error(f"Erro ao estornar Stripe: {e}")
            raise
    
    async def _refund_mercadopago_payment(
        self, 
        payment_id: str, 
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Estornar pagamento MercadoPago"""
        try:
            refund_data = {}
            if amount:
                refund_data["amount"] = amount
            
            refund_response = self.mp.refund().create(payment_id, refund_data)
            refund = refund_response["response"]
            
            return {
                "refund_id": refund["id"],
                "status": refund["status"],
                "amount": refund.get("amount", 0),
                "currency": "BRL"
            }
        except Exception as e:
            logger.error(f"Erro ao estornar MercadoPago: {e}")
            raise

# Instância global
payment_service = PaymentService() 