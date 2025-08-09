import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid

from app.models.queue import (
    QueueEntry, QueueType, QueueStatus, Appointment, AppointmentType,
    QueueManager, QRCodeSession, NotificationMethod
)

class VirtualQueueService:
    """Virtual queue management service"""
    
    def __init__(self):
        self.queue_manager = QueueManager()
        self.qr_sessions: Dict[str, QRCodeSession] = {}
        
        # Queue configuration
        self.max_advance_booking_days = 14
        self.appointment_slots_per_hour = 4  # 15-minute slots
        self.peak_hours = [(7, 9), (12, 14), (17, 19)]  # Morning, lunch, evening
        
        # Notification templates
        self.notification_templates = self._load_notification_templates()
        
        print("🎯 Virtual Queue Service initialized")

    async def initialize(self):
        print("🎯 Queue service ready")
        return True
    
    def _load_notification_templates(self) -> Dict[str, str]:
        """Load notification message templates"""
        return {
            "queue_joined": "Hi {name}! You're #{position} in line. Estimated wait: {wait_time} minutes. We'll notify you when it's your turn!",
            "queue_progress": "Hi {name}! You've moved up to #{position} in line. Estimated wait: {wait_time} minutes.",
            "ready_soon": "Hi {name}! You're next in line! Please be ready, we'll call you in about 2-3 minutes.",
            "your_turn": "Hi {name}! Your table is ready! Please come to the front desk. Table #{table}.",
            "appointment_reminder_24h": "Reminder: Your {type} appointment at Claude's Coffee Corner is tomorrow at {time}. See you then!",
            "appointment_reminder_1h": "Your {type} appointment is in 1 hour at {time}. We're looking forward to seeing you!",
            "appointment_confirmed": "Your {type} appointment is confirmed for {time}. We'll send reminders as the time approaches!",
            "order_ready": "Hi {name}! Your order is ready for pickup. Please come to the counter when convenient."
        }
    
    async def join_queue(
        self,
        customer_name: str,
        queue_type: QueueType = QueueType.WALK_IN,
        party_size: int = 1,
        customer_phone: Optional[str] = None,
        customer_email: Optional[str] = None,
        special_requests: Optional[str] = None,
        session_id: Optional[str] = None,
        order_id: Optional[str] = None
    ) -> QueueEntry:
        """Add customer to queue"""
        
        # Create queue entry
        entry = QueueEntry(
            session_id=session_id,
            queue_type=queue_type,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            party_size=party_size,
            special_requests=special_requests,
            order_id=order_id,
            has_order=bool(order_id)
        )
        
        # Set notification preferences
        if customer_phone:
            entry.notification_methods.append(NotificationMethod.SMS)
        if customer_email:
            entry.notification_methods.append(NotificationMethod.EMAIL)
        entry.notification_methods.append(NotificationMethod.IN_STORE_DISPLAY)
        
        # Calculate estimated prep time based on order
        if order_id:
            entry.estimated_prep_time = await self._calculate_prep_time(order_id)
        
        # Add to queue
        position = self.queue_manager.add_to_queue(entry)
        
        # Calculate estimated ready time
        wait_time = entry.get_estimated_wait_time(
            position - 1, 
            self.queue_manager.average_service_time
        )
        entry.estimated_ready_time = datetime.utcnow() + timedelta(minutes=wait_time)
        
        # Send welcome notification
        await self._send_notification(
            entry,
            "queue_joined",
            {
                "name": customer_name,
                "position": position,
                "wait_time": wait_time
            }
        )
        
        print(f"🎯 {customer_name} joined {queue_type.value} queue at position {position}")
        return entry
    
    async def get_queue_status(self, queue_id: str) -> Optional[Dict[str, Any]]:
        """Get current status for queue entry"""
        
        # Find the entry
        entry = None
        for queue in self.queue_manager.current_queues.values():
            for e in queue:
                if e.queue_id == queue_id:
                    entry = e
                    break
            if entry:
                break
        
        if not entry:
            return None
        
        position = self.queue_manager.get_queue_position(queue_id)
        wait_time = self.queue_manager.get_estimated_wait_time(queue_id)
        
        return {
            "queue_id": queue_id,
            "status": entry.status.value,
            "position": position,
            "estimated_wait_time": wait_time,
            "estimated_ready_time": entry.estimated_ready_time.isoformat() if entry.estimated_ready_time else None,
            "party_size": entry.party_size,
            "table_number": entry.table_number,
            "created_at": entry.created_at.isoformat(),
            "has_order": entry.has_order
        }
    
    async def update_queue_progress(self):
        """Update queue progress and send notifications"""
        
        for queue_type, queue in self.queue_manager.current_queues.items():
            for i, entry in enumerate(queue):
                if entry.status != QueueStatus.WAITING:
                    continue
                
                current_position = i + 1
                
                # Check if position changed significantly
                if (entry.current_position - current_position) >= 2:
                    entry.current_position = current_position
                    wait_time = entry.get_estimated_wait_time(
                        current_position - 1,
                        self.queue_manager.average_service_time
                    )
                    
                    # Send progress notification
                    if entry.is_ready_for_notification("progress", cooldown_minutes=5):
                        await self._send_notification(
                            entry,
                            "queue_progress",
                            {
                                "name": entry.customer_name,
                                "position": current_position,
                                "wait_time": wait_time
                            }
                        )
                
                # Notify if they're next (position 1 or 2)
                elif current_position <= 2 and entry.is_ready_for_notification("ready_soon", cooldown_minutes=10):
                    await self._send_notification(
                        entry,
                        "ready_soon",
                        {"name": entry.customer_name}
                    )
    
    async def call_next_customer(self, queue_type: QueueType) -> Optional[QueueEntry]:
        """Call next customer and assign table if needed"""
        
        entry = self.queue_manager.call_next_customer(queue_type)
        if not entry:
            return None
        
        # Assign table for dine-in
        table_number = None
        if queue_type == QueueType.DINE_IN:
            table_number = self.queue_manager.assign_table(
                entry.queue_id,
                entry.seating_preference
            )
            
        # Send notification
        await self._send_notification(
            entry,
            "your_turn",
            {
                "name": entry.customer_name,
                "table": table_number or "at the counter"
            }
        )
        
        print(f"🔔 Called {entry.customer_name} for {queue_type.value}")
        return entry
    
    async def complete_service(self, queue_id: str) -> Optional[QueueEntry]:
        """Complete service for customer"""
        
        entry = self.queue_manager.complete_service(queue_id)
        if entry:
            print(f"✅ Completed service for {entry.customer_name}")
        
        return entry
    
    async def cancel_queue_entry(self, queue_id: str, reason: str = "customer_request") -> bool:
        """Cancel queue entry"""
        
        entry = self.queue_manager.remove_from_queue(queue_id)
        if entry:
            entry.status = QueueStatus.CANCELLED
            print(f"❌ Cancelled queue entry for {entry.customer_name}: {reason}")
            return True
        return False
    
    # Appointment Management
    
    async def schedule_appointment(
        self,
        organizer_name: str,
        appointment_type: AppointmentType,
        scheduled_time: datetime,
        duration_minutes: int = 60,
        participant_count: int = 2,
        organizer_phone: Optional[str] = None,
        organizer_email: Optional[str] = None,
        special_requirements: Optional[str] = None
    ) -> Appointment:
        """Schedule a new appointment"""
        
        # Validate time slot
        if not await self._is_time_slot_available(scheduled_time, duration_minutes):
            raise ValueError("Time slot not available")
        
        appointment = Appointment(
            appointment_type=appointment_type,
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
            organizer_name=organizer_name,
            organizer_phone=organizer_phone,
            organizer_email=organizer_email,
            participant_count=participant_count,
            special_requirements=special_requirements,
            status="confirmed"
        )
        
        self.queue_manager.appointments.append(appointment)
        
        # Send confirmation
        await self._send_appointment_notification(
            appointment,
            "appointment_confirmed",
            {
                "type": appointment_type.value.replace("_", " ").title(),
                "time": scheduled_time.strftime("%B %d at %I:%M %p")
            }
        )
        
        print(f"📅 Scheduled {appointment_type.value} for {organizer_name} at {scheduled_time}")
        return appointment
    
    async def get_available_slots(
        self,
        date: datetime,
        appointment_type: AppointmentType,
        duration_minutes: int = 60
    ) -> List[datetime]:
        """Get available appointment slots for a date"""
        
        slots = []
        start_time = date.replace(hour=8, minute=0, second=0, microsecond=0)  # 8 AM
        end_time = date.replace(hour=20, minute=0, second=0, microsecond=0)   # 8 PM
        
        # Generate 15-minute slots
        current_time = start_time
        while current_time + timedelta(minutes=duration_minutes) <= end_time:
            if await self._is_time_slot_available(current_time, duration_minutes):
                slots.append(current_time)
            current_time += timedelta(minutes=15)
        
        return slots
    
    async def _is_time_slot_available(self, start_time: datetime, duration_minutes: int) -> bool:
        """Check if time slot is available"""
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Check against existing appointments
        for appointment in self.queue_manager.appointments:
            if appointment.status == "cancelled":
                continue
                
            apt_start = appointment.scheduled_time
            apt_end = apt_start + timedelta(minutes=appointment.duration_minutes)
            
            # Check for overlap
            if (start_time < apt_end and end_time > apt_start):
                return False
        
        # Check business hours
        hour = start_time.hour
        if hour < 8 or hour >= 20:  # 8 AM to 8 PM
            return False
        
        return True
    
    # QR Code Management
    
    async def generate_table_qr(self, table_number: int) -> Tuple[str, str]:
        """Generate QR code for table ordering"""
        
        # Create or update QR session
        qr_session = QRCodeSession(table_number=table_number)
        self.qr_sessions[qr_session.qr_id] = qr_session
        
        # Generate QR code URL
        base_url = "http://localhost:8000"  # In production, use actual domain
        qr_url = f"{base_url}/table/{qr_session.qr_id}"
        
        # Generate QR code image
        qr_code_data = await self._generate_qr_code_image(qr_url)
        
        print(f"📱 Generated QR code for table {table_number}")
        return qr_session.qr_id, qr_code_data
    
    async def scan_table_qr(self, qr_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Handle QR code scan"""
        
        if qr_id not in self.qr_sessions:
            return None
        
        qr_session = self.qr_sessions[qr_id]
        
        if not qr_session.scan(session_id):
            return None
        
        print(f"📱 QR scanned for table {qr_session.table_number} by session {session_id}")
        
        return {
            "table_number": qr_session.table_number,
            "session_id": session_id,
            "qr_id": qr_id,
            "can_order": True,
            "welcome_message": f"Welcome to Table {qr_session.table_number}! I'm here to help you order and answer any questions."
        }
    
    async def _generate_qr_code_image(self, url: str) -> str:
        """Generate QR code image as base64 string"""
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_data}"
    
    # Notification System
    
    async def _send_notification(
        self,
        entry: QueueEntry,
        template_name: str,
        params: Dict[str, Any]
    ):
        """Send notification to customer"""
        
        template = self.notification_templates.get(template_name, "")
        message = template.format(**params)
        
        # In production, integrate with SMS/email services
        for method in entry.notification_methods:
            if method == NotificationMethod.SMS and entry.customer_phone:
                await self._send_sms(entry.customer_phone, message)
            elif method == NotificationMethod.EMAIL and entry.customer_email:
                await self._send_email(entry.customer_email, message)
            elif method == NotificationMethod.IN_STORE_DISPLAY:
                await self._update_display(entry.queue_id, message)
        
        entry.add_notification(template_name, "multi", True)
    
    async def _send_appointment_notification(
        self,
        appointment: Appointment,
        template_name: str,
        params: Dict[str, Any]
    ):
        """Send appointment notification"""
        
        template = self.notification_templates.get(template_name, "")
        message = template.format(**params)
        
        # Send via available channels
        if appointment.organizer_phone:
            await self._send_sms(appointment.organizer_phone, message)
        if appointment.organizer_email:
            await self._send_email(appointment.organizer_email, message)
    
    async def _send_sms(self, phone: str, message: str):
        """Send SMS notification (mock implementation)"""
        print(f"📱 SMS to {phone}: {message}")
    
    async def _send_email(self, email: str, message: str):
        """Send email notification (mock implementation)"""
        print(f"📧 Email to {email}: {message}")
    
    async def _update_display(self, queue_id: str, message: str):
        """Update in-store display (mock implementation)"""
        print(f"🖥️ Display update for {queue_id}: {message}")
    
    async def _calculate_prep_time(self, order_id: str) -> int:
        """Calculate preparation time for order"""
        # Mock implementation - in production, analyze actual order
        return 5  # Default 5 minutes
    
    # Reminder System
    
    async def process_appointment_reminders(self):
        """Process appointment reminders"""
        
        now = datetime.utcnow()
        
        for appointment in self.queue_manager.appointments:
            if appointment.status != "confirmed":
                continue
            
            # 24-hour reminder
            if (not appointment.reminder_sent_24h and 
                appointment.should_send_reminder(24)):
                
                await self._send_appointment_notification(
                    appointment,
                    "appointment_reminder_24h",
                    {
                        "type": appointment.appointment_type.value.replace("_", " ").title(),
                        "time": appointment.scheduled_time.strftime("%I:%M %p")
                    }
                )
                appointment.reminder_sent_24h = True
            
            # 1-hour reminder
            if (not appointment.reminder_sent_1h and 
                appointment.should_send_reminder(1)):
                
                await self._send_appointment_notification(
                    appointment,
                    "appointment_reminder_1h",
                    {
                        "type": appointment.appointment_type.value.replace("_", " ").title(),
                        "time": appointment.scheduled_time.strftime("%I:%M %p")
                    }
                )
                appointment.reminder_sent_1h = True
    
    # Analytics and Reporting
    
    def get_queue_analytics(self) -> Dict[str, Any]:
        """Get queue analytics"""
        
        summary = self.queue_manager.get_queue_summary()
        
        # Calculate additional metrics
        total_entries = sum(len(queue) for queue in self.queue_manager.current_queues.values())
        avg_wait_time = sum(
            entry.calculate_wait_time() 
            for queue in self.queue_manager.current_queues.values()
            for entry in queue
        ) / max(total_entries, 1)
        
        return {
            "queue_summary": summary,
            "total_entries": total_entries,
            "average_wait_time": round(avg_wait_time, 1),
            "active_qr_sessions": len(self.qr_sessions),
            "upcoming_appointments": len([
                apt for apt in self.queue_manager.appointments
                if apt.scheduled_time > datetime.utcnow() and apt.status == "confirmed"
            ]),
            "peak_hour_status": self._get_peak_hour_status()
        }
    
    def _get_peak_hour_status(self) -> str:
        """Check if currently in peak hours"""
        current_hour = datetime.now().hour
        
        for start, end in self.peak_hours:
            if start <= current_hour < end:
                return "peak"
        return "normal"
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "queue_service_ready": True,
            "total_queues": len(self.queue_manager.current_queues),
            "total_customers": sum(len(q) for q in self.queue_manager.current_queues.values()),
            "qr_sessions_active": len(self.qr_sessions),
            "appointments_today": len(self.queue_manager.get_appointments_today()),
            "average_service_time": self.queue_manager.average_service_time
        }