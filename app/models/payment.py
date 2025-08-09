from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

class PaymentStatus(str, Enum):
    """Payment status options"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    """Payment method types"""
    CARD = "card"
    CASH = "cash"
    MOBILE = "mobile"
    GIFT_CARD = "gift_card"
    STORE_CREDIT = "store_credit"

class OrderStatus(str, Enum):
    """Order status throughout the process"""
    CART = "cart"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderType(str, Enum):
    """Order type options"""
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"

class PaymentIntent(BaseModel):
    """Stripe payment intent data"""
    payment_intent_id: str
    client_secret: str
    amount: int  # Amount in cents
    currency: str = "usd"
    status: PaymentStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class OrderItem(BaseModel):
    """Individual item in an order"""
    id: str
    menu_item_id: str
    name: str
    size: str = "medium"
    price: Decimal
    quantity: int = 1
    customizations: List[str] = Field(default_factory=list)
    special_instructions: Optional[str] = None
    
    def get_total_price(self) -> Decimal:
        """Calculate total price for this item"""
        return self.price * self.quantity

class Order(BaseModel):
    """Complete order model"""
    order_id: str
    session_id: str
    customer_id: Optional[str] = None
    
    # Order details
    items: List[OrderItem] = Field(default_factory=list)
    order_type: OrderType = OrderType.DINE_IN
    status: OrderStatus = OrderStatus.CART
    
    # Pricing
    subtotal: Decimal = Decimal('0.00')
    tax_rate: Decimal = Decimal('0.08')  # 8% default tax
    tax_amount: Decimal = Decimal('0.00')
    tip_amount: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    
    # Payment
    payment_method: Optional[PaymentMethod] = None
    payment_intent: Optional[PaymentIntent] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Delivery/pickup info
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    delivery_address: Optional[str] = None
    table_number: Optional[int] = None
    
    # Special requests
    special_instructions: Optional[str] = None
    estimated_ready_time: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def calculate_totals(self):
        """Calculate all order totals"""
        # Calculate subtotal
        self.subtotal = sum(item.get_total_price() for item in self.items)
        
        # Calculate tax
        self.tax_amount = (self.subtotal * self.tax_rate).quantize(Decimal('0.01'))
        
        # Calculate total
        self.total_amount = (
            self.subtotal + 
            self.tax_amount + 
            self.tip_amount - 
            self.discount_amount
        ).quantize(Decimal('0.01'))
        
        self.updated_at = datetime.utcnow()
    
    def add_item(self, item: OrderItem):
        """Add item to order"""
        # Check if same item already exists
        for existing_item in self.items:
            if (existing_item.menu_item_id == item.menu_item_id and 
                existing_item.size == item.size and 
                existing_item.customizations == item.customizations):
                existing_item.quantity += item.quantity
                self.calculate_totals()
                return
        
        # Add new item
        self.items.append(item)
        self.calculate_totals()
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from order"""
        original_count = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        
        if len(self.items) < original_count:
            self.calculate_totals()
            return True
        return False
    
    def update_item_quantity(self, item_id: str, quantity: int) -> bool:
        """Update item quantity"""
        for item in self.items:
            if item.id == item_id:
                if quantity <= 0:
                    return self.remove_item(item_id)
                item.quantity = quantity
                self.calculate_totals()
                return True
        return False
    
    def clear_items(self):
        """Clear all items from order"""
        self.items = []
        self.calculate_totals()
    
    def get_total_items(self) -> int:
        """Get total number of items"""
        return sum(item.quantity for item in self.items)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "order_id": self.order_id,
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "size": item.size,
                    "price": float(item.price),
                    "quantity": item.quantity,
                    "customizations": item.customizations,
                    "total": float(item.get_total_price())
                }
                for item in self.items
            ],
            "order_type": self.order_type.value,
            "status": self.status.value,
            "subtotal": float(self.subtotal),
            "tax_amount": float(self.tax_amount),
            "tip_amount": float(self.tip_amount),
            "total_amount": float(self.total_amount),
            "payment_status": self.payment_status.value,
            "customer_info": {
                "name": self.customer_name,
                "phone": self.customer_phone,
                "email": self.customer_email
            },
            "created_at": self.created_at.isoformat(),
            "estimated_ready_time": self.estimated_ready_time.isoformat() if self.estimated_ready_time else None
        }
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d)
        }

class PaymentRequest(BaseModel):
    """Payment request from client"""
    order_id: str
    payment_method: PaymentMethod
    tip_amount: Optional[Decimal] = Decimal('0.00')
    customer_info: Optional[Dict[str, str]] = None

class PaymentResponse(BaseModel):
    """Payment response to client"""
    success: bool
    payment_intent_id: Optional[str] = None
    client_secret: Optional[str] = None
    order: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    requires_action: bool = False

class Receipt(BaseModel):
    """Order receipt model"""
    receipt_id: str
    order_id: str
    order: Order
    
    # Receipt details
    receipt_number: str
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    cashier_name: str = "AI Assistant"
    
    # Shop info
    shop_name: str = "Claude's Coffee Corner"
    shop_address: str = "123 Coffee Street, Downtown"
    shop_phone: str = "(555) 123-BREW"
    
    def generate_receipt_text(self) -> str:
        """Generate formatted receipt text"""
        lines = []
        lines.append("=" * 40)
        lines.append(f"{self.shop_name.center(40)}")
        lines.append(f"{self.shop_address.center(40)}")
        lines.append(f"{self.shop_phone.center(40)}")
        lines.append("=" * 40)
        lines.append(f"Receipt #: {self.receipt_number}")
        lines.append(f"Order #: {self.order_id}")
        lines.append(f"Date: {self.issued_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Cashier: {self.cashier_name}")
        lines.append("-" * 40)
        
        # Items
        for item in self.order.items:
            lines.append(f"{item.name} x{item.quantity}")
            if item.size != "medium":
                lines.append(f"  Size: {item.size}")
            if item.customizations:
                lines.append(f"  {', '.join(item.customizations)}")
            lines.append(f"  ${float(item.get_total_price()):.2f}")
            lines.append("")
        
        lines.append("-" * 40)
        lines.append(f"Subtotal: ${float(self.order.subtotal):.2f}")
        lines.append(f"Tax: ${float(self.order.tax_amount):.2f}")
        if self.order.tip_amount > 0:
            lines.append(f"Tip: ${float(self.order.tip_amount):.2f}")
        if self.order.discount_amount > 0:
            lines.append(f"Discount: -${float(self.order.discount_amount):.2f}")
        lines.append("=" * 40)
        lines.append(f"TOTAL: ${float(self.order.total_amount):.2f}")
        lines.append("=" * 40)
        lines.append("Thank you for visiting!")
        lines.append("Have a wonderful day! ☕")
        
        return "\n".join(lines)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d)
        }