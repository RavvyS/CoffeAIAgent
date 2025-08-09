import stripe
import json
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import shortuuid

from app.models.payment import (
    Order, OrderItem, PaymentIntent, PaymentStatus, 
    PaymentMethod, OrderStatus, PaymentRequest, 
    PaymentResponse, Receipt
)
from app.utils.config import settings

class PaymentService:
    """Payment processing service using Stripe"""
    
    def __init__(self):
        # Initialize Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        
        # Payment configuration
        self.currency = "usd"
        self.automatic_payment_methods = {
            "enabled": True,
            "allow_redirects": "never"
        }
        
        print(f"💳 Payment service initialized with Stripe")
    
    async def initialize(self):
        """Initialize payment service"""
        print("💳 Payment service ready")
        return True
    
    async def create_order(self, session_id: str, customer_id: Optional[str] = None) -> Order:
        """Create a new order"""
        order_id = f"order_{shortuuid.uuid()}"
        
        order = Order(
            order_id=order_id,
            session_id=session_id,
            customer_id=customer_id
        )
        
        return order
    
    async def add_item_to_order(
        self, 
        order: Order, 
        menu_item: Dict[str, Any], 
        size: str = "medium",
        quantity: int = 1,
        customizations: list = None
    ) -> Order:
        """Add item to order"""
        
        item_id = f"item_{uuid.uuid4().hex[:8]}"
        
        # Get price based on size (if multiple sizes available)
        price = Decimal(str(menu_item.get("price", 0)))
        
        # Add size premium if applicable
        size_premiums = {
            "small": Decimal('0.00'),
            "medium": Decimal('0.00'),
            "large": Decimal('0.50'),
            "extra_large": Decimal('1.00')
        }
        price += size_premiums.get(size.lower(), Decimal('0.00'))
        
        # Add customization costs
        if customizations:
            customization_cost = Decimal('0.60') * len([c for c in customizations if "milk" in c.lower()])
            price += customization_cost
        
        order_item = OrderItem(
            id=item_id,
            menu_item_id=menu_item.get("id", "unknown"),
            name=menu_item.get("name", "Unknown Item"),
            size=size,
            price=price,
            quantity=quantity,
            customizations=customizations or []
        )
        
        order.add_item(order_item)
        return order
    
    async def update_order_customer_info(
        self, 
        order: Order, 
        customer_info: Dict[str, str]
    ) -> Order:
        """Update customer information for order"""
        order.customer_name = customer_info.get("name")
        order.customer_phone = customer_info.get("phone")
        order.customer_email = customer_info.get("email")
        order.delivery_address = customer_info.get("address")
        order.table_number = customer_info.get("table_number")
        
        order.updated_at = datetime.utcnow()
        return order
    
    async def create_payment_intent(
        self, 
        order: Order, 
        tip_amount: Decimal = Decimal('0.00')
    ) -> PaymentIntent:
        """Create Stripe payment intent for order"""
        
        # Update tip amount
        order.tip_amount = tip_amount
        order.calculate_totals()
        
        # Convert to cents for Stripe
        amount_cents = int(order.total_amount * 100)
        
        try:
            # Create Stripe payment intent
            stripe_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=self.currency,
                automatic_payment_methods=self.automatic_payment_methods,
                metadata={
                    "order_id": order.order_id,
                    "session_id": order.session_id,
                    "customer_id": order.customer_id or "guest"
                }
            )
            
            # Create our payment intent model
            payment_intent = PaymentIntent(
                payment_intent_id=stripe_intent["id"],
                client_secret=stripe_intent["client_secret"],
                amount=amount_cents,
                currency=self.currency,
                status=PaymentStatus.PENDING
            )
            
            # Update order
            order.payment_intent = payment_intent
            order.payment_status = PaymentStatus.PENDING
            order.status = OrderStatus.PENDING_PAYMENT
            order.updated_at = datetime.utcnow()
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            print(f"❌ Stripe error creating payment intent: {str(e)}")
            raise Exception(f"Payment processing error: {str(e)}")
    
    async def confirm_payment(
        self, 
        payment_intent_id: str,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Confirm payment intent"""
        
        try:
            if payment_method_id:
                # Confirm with payment method
                result = stripe.PaymentIntent.confirm(
                    payment_intent_id,
                    payment_method=payment_method_id
                )
            else:
                # Just retrieve current status
                result = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "id": result["id"],
                "status": result["status"],
                "client_secret": result.get("client_secret"),
                "next_action": result.get("next_action")
            }
            
        except stripe.error.StripeError as e:
            print(f"❌ Stripe error confirming payment: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get payment service status"""
        return {
            "stripe_configured": bool(settings.STRIPE_SECRET_KEY),
            "webhook_configured": bool(settings.STRIPE_WEBHOOK_SECRET),
            "currency": self.currency,
            "service_ready": bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET)
        }

class MockPaymentService(PaymentService):
    """Mock payment service for development/testing"""
    
    def __init__(self):
        print("💳 Mock payment service initialized (no real payments)")
        self.currency = "usd"
    
    async def initialize(self):
        """Initialize mock payment service"""
        print("💳 Mock payment service ready")
        return True
    
    async def create_payment_intent(
        self, 
        order: Order, 
        tip_amount: Decimal = Decimal('0.00')
    ) -> PaymentIntent:
        """Create mock payment intent"""
        
        order.tip_amount = tip_amount
        order.calculate_totals()
        
        # Create mock payment intent
        payment_intent = PaymentIntent(
            payment_intent_id=f"pi_mock_{uuid.uuid4().hex[:16]}",
            client_secret=f"pi_mock_{uuid.uuid4().hex[:16]}_secret",
            amount=int(order.total_amount * 100),
            currency=self.currency,
            status=PaymentStatus.PENDING
        )
        
        order.payment_intent = payment_intent
        order.payment_status = PaymentStatus.PENDING
        order.status = OrderStatus.PENDING_PAYMENT
        
        return payment_intent
    
    async def confirm_payment(
        self, 
        payment_intent_id: str,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock payment confirmation - always succeeds"""
        
        # Simulate processing delay
        await asyncio.sleep(1)
        
        return {
            "id": payment_intent_id,
            "status": "succeeded",
            "client_secret": f"{payment_intent_id}_secret"
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get mock service status"""
        return {
            "stripe_configured": False,
            "webhook_configured": False,
            "currency": self.currency,
            "service_ready": True,
            "mock_mode": True
        }