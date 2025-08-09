from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid

class QueueType(str, Enum):
    """Types of queues available"""
    WALK_IN = "walk_in"
    APPOINTMENT = "appointment"
    DELIVERY = "delivery"
    TAKEAWAY = "takeaway"
    DINE_IN = "dine_in"

class QueueStatus(str, Enum):
    """Status of queue entries"""
    WAITING = "waiting"
    CALLED = "called"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AppointmentType(str, Enum):
    """Types of appointments"""
    COFFEE_MEETING = "coffee_meeting"
    COFFEE_DATE = "coffee_date"
    BUSINESS_MEETING = "business_meeting"
    STUDY_SESSION = "study_session"
    CASUAL_MEETUP = "casual_meetup"
    THERAPY_SESSION = "therapy_session"  # For emotional support
    PICKUP_ORDER = "pickup_order"

class NotificationMethod(str, Enum):
    """Ways to notify customers"""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    IN_STORE_DISPLAY = "in_store_display"

class QueueEntry(BaseModel):
    """Individual entry in the queue"""
    queue_id: str = Field(default_factory=lambda: f"q_{uuid.uuid4().hex[:8]}")
    session_id: Optional[str] = None
    customer_id: Optional[str] = None
    
    # Queue details
    queue_type: QueueType = QueueType.WALK_IN
    status: QueueStatus = QueueStatus.WAITING
    priority: int = Field(default=0, ge=0, le=10)  # 0=normal, 10=highest priority
    
    # Customer information
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    party_size: int = Field(default=1, ge=1, le=12)
    
    # Order information
    order_id: Optional[str] = None
    has_order: bool = False
    order_value: float = 0.0
    estimated_prep_time: int = Field(default=5)  # minutes
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_ready_time: Optional[datetime] = None
    called_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Position tracking
    original_position: int = 0
    current_position: int = 0
    
    # Special requirements
    special_requests: Optional[str] = None
    accessibility_needs: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    
    # Notification preferences
    notification_methods: List[NotificationMethod] = Field(default_factory=list)
    notifications_sent: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Table assignment (for dine-in)
    table_number: Optional[int] = None
    seating_preference: Optional[str] = None  # "window", "quiet", "counter"
    
    def calculate_wait_time(self) -> int:
        """Calculate current wait time in minutes"""
        if self.completed_at:
            return int((self.completed_at - self.created_at).total_seconds() / 60)
        return int((datetime.utcnow() - self.created_at).total_seconds() / 60)
    
    def get_estimated_wait_time(self, queue_ahead: int = 0, avg_service_time: int = 5) -> int:
        """Estimate wait time based on queue position"""
        return queue_ahead * avg_service_time + self.estimated_prep_time
    
    def is_ready_for_notification(self, notification_type: str, cooldown_minutes: int = 5) -> bool:
        """Check if ready for notification (with cooldown)"""
        recent_notifications = [
            n for n in self.notifications_sent 
            if n.get("type") == notification_type and 
            datetime.fromisoformat(n.get("sent_at", "")) > 
            datetime.utcnow() - timedelta(minutes=cooldown_minutes)
        ]
        return len(recent_notifications) == 0
    
    def add_notification(self, notification_type: str, method: str, success: bool = True):
        """Record notification sent"""
        self.notifications_sent.append({
            "type": notification_type,
            "method": method,
            "sent_at": datetime.utcnow().isoformat(),
            "success": success
        })
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class Appointment(BaseModel):
    """Scheduled appointment"""
    appointment_id: str = Field(default_factory=lambda: f"apt_{uuid.uuid4().hex[:8]}")
    queue_entry_id: Optional[str] = None
    
    # Appointment details
    appointment_type: AppointmentType
    scheduled_time: datetime
    duration_minutes: int = Field(default=60, ge=15, le=240)
    
    # Participants
    organizer_name: str
    organizer_phone: Optional[str] = None
    organizer_email: Optional[str] = None
    participant_count: int = Field(default=2, ge=1, le=8)
    participant_names: List[str] = Field(default_factory=list)
    
    # Preferences
    seating_preference: Optional[str] = None
    atmosphere_preference: Optional[str] = None  # "quiet", "social", "business"
    special_requirements: Optional[str] = None
    
    # Booking details
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    status: str = "pending"  # pending, confirmed, cancelled, completed
    
    # Reminders
    reminder_sent_24h: bool = False
    reminder_sent_1h: bool = False
    
    def get_buffer_time(self) -> timedelta:
        """Get recommended buffer time before appointment"""
        buffer_map = {
            AppointmentType.COFFEE_DATE: 15,
            AppointmentType.BUSINESS_MEETING: 10,
            AppointmentType.THERAPY_SESSION: 20,
            AppointmentType.COFFEE_MEETING: 10
        }
        return timedelta(minutes=buffer_map.get(self.appointment_type, 10))
    
    def should_send_reminder(self, hours_before: int) -> bool:
        """Check if reminder should be sent"""
        time_until = self.scheduled_time - datetime.utcnow()
        target_time = timedelta(hours=hours_before)
        
        # Send if we're within the target window (±15 minutes)
        return abs(time_until - target_time) < timedelta(minutes=15)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class QueueManager(BaseModel):
    """Queue management system state"""
    current_queues: Dict[QueueType, List[QueueEntry]] = Field(default_factory=dict)
    appointments: List[Appointment] = Field(default_factory=list)
    
    # Queue settings
    max_queue_size: int = 50
    average_service_time: int = 5  # minutes
    
    # Operating hours
    opening_time: str = "06:00"
    closing_time: str = "21:00"
    
    # Table management (for dine-in)
    total_tables: int = 20
    available_tables: List[int] = Field(default_factory=lambda: list(range(1, 21)))
    occupied_tables: Dict[int, str] = Field(default_factory=dict)  # table_num: queue_id
    
    # Analytics
    daily_stats: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Initialize queue types
        for queue_type in QueueType:
            if queue_type not in self.current_queues:
                self.current_queues[queue_type] = []
    
    def add_to_queue(self, entry: QueueEntry) -> int:
        """Add entry to appropriate queue and return position"""
        queue = self.current_queues[entry.queue_type]
        
        # Calculate position based on priority and creation time
        position = len(queue)
        for i, existing_entry in enumerate(queue):
            if entry.priority > existing_entry.priority:
                position = i
                break
        
        entry.original_position = position + 1
        entry.current_position = position + 1
        queue.insert(position, entry)
        
        # Update positions for all entries
        self._update_positions(entry.queue_type)
        
        return position + 1
    
    def remove_from_queue(self, queue_id: str) -> Optional[QueueEntry]:
        """Remove entry from queue"""
        for queue_type, queue in self.current_queues.items():
            for i, entry in enumerate(queue):
                if entry.queue_id == queue_id:
                    removed_entry = queue.pop(i)
                    self._update_positions(queue_type)
                    return removed_entry
        return None
    
    def get_queue_position(self, queue_id: str) -> Optional[int]:
        """Get current position in queue"""
        for queue in self.current_queues.values():
            for i, entry in enumerate(queue):
                if entry.queue_id == queue_id:
                    return i + 1
        return None
    
    def get_estimated_wait_time(self, queue_id: str) -> Optional[int]:
        """Get estimated wait time for queue entry"""
        for queue in self.current_queues.values():
            for i, entry in enumerate(queue):
                if entry.queue_id == queue_id:
                    return entry.get_estimated_wait_time(i, self.average_service_time)
        return None
    
    def call_next_customer(self, queue_type: QueueType) -> Optional[QueueEntry]:
        """Call next customer in queue"""
        queue = self.current_queues[queue_type]
        if queue:
            next_customer = queue[0]
            next_customer.status = QueueStatus.CALLED
            next_customer.called_at = datetime.utcnow()
            return next_customer
        return None
    
    def complete_service(self, queue_id: str, table_number: Optional[int] = None) -> Optional[QueueEntry]:
        """Mark service as complete and remove from queue"""
        entry = self.remove_from_queue(queue_id)
        if entry:
            entry.status = QueueStatus.COMPLETED
            entry.completed_at = datetime.utcnow()
            
            # Free up table if applicable
            if table_number and table_number in self.occupied_tables:
                self.available_tables.append(table_number)
                del self.occupied_tables[table_number]
                
        return entry
    
    def assign_table(self, queue_id: str, preference: Optional[str] = None) -> Optional[int]:
        """Assign table to customer"""
        if not self.available_tables:
            return None
        
        # Simple table assignment (could be enhanced with preferences)
        table_number = self.available_tables.pop(0)
        self.occupied_tables[table_number] = queue_id
        
        # Update queue entry
        for queue in self.current_queues.values():
            for entry in queue:
                if entry.queue_id == queue_id:
                    entry.table_number = table_number
                    break
        
        return table_number
    
    def _update_positions(self, queue_type: QueueType):
        """Update positions for all entries in queue"""
        queue = self.current_queues[queue_type]
        for i, entry in enumerate(queue):
            entry.current_position = i + 1
    
    def get_queue_summary(self) -> Dict[str, Any]:
        """Get summary of all queues"""
        summary = {}
        total_waiting = 0
        
        for queue_type, queue in self.current_queues.items():
            waiting_count = len([e for e in queue if e.status == QueueStatus.WAITING])
            called_count = len([e for e in queue if e.status == QueueStatus.CALLED])
            preparing_count = len([e for e in queue if e.status == QueueStatus.PREPARING])
            
            total_waiting += waiting_count
            
            summary[queue_type.value] = {
                "total": len(queue),
                "waiting": waiting_count,
                "called": called_count,
                "preparing": preparing_count,
                "estimated_wait": waiting_count * self.average_service_time
            }
        
        # Overall summary
        summary["overall"] = {
            "total_waiting": total_waiting,
            "available_tables": len(self.available_tables),
            "occupied_tables": len(self.occupied_tables),
            "average_wait_time": total_waiting * self.average_service_time
        }
        
        return summary
    
    def get_appointments_today(self) -> List[Appointment]:
        """Get today's appointments"""
        today = datetime.now().date()
        return [
            apt for apt in self.appointments
            if apt.scheduled_time.date() == today
        ]
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class QRCodeSession(BaseModel):
    """QR code session for table ordering"""
    qr_id: str = Field(default_factory=lambda: f"qr_{uuid.uuid4().hex[:12]}")
    table_number: int
    session_id: Optional[str] = None
    
    # QR code details
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=8))
    
    # Usage tracking
    scans: int = 0
    last_scanned_at: Optional[datetime] = None
    active_sessions: List[str] = Field(default_factory=list)
    
    # Table status
    occupied: bool = False
    customer_name: Optional[str] = None
    party_size: Optional[int] = None
    
    def is_valid(self) -> bool:
        """Check if QR code is still valid"""
        return datetime.utcnow() < self.expires_at
    
    def scan(self, session_id: str) -> bool:
        """Record QR code scan"""
        if not self.is_valid():
            return False
        
        self.scans += 1
        self.last_scanned_at = datetime.utcnow()
        
        if session_id not in self.active_sessions:
            self.active_sessions.append(session_id)
        
        return True
    
    def occupy_table(self, customer_name: str, party_size: int):
        """Mark table as occupied"""
        self.occupied = True
        self.customer_name = customer_name
        self.party_size = party_size
    
    def free_table(self):
        """Free up the table"""
        self.occupied = False
        self.customer_name = None
        self.party_size = None
        self.active_sessions = []
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }