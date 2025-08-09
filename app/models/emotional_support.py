import json
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import asyncio

# Removed the circular import that was causing issues:
# from app.services.emotional_support_service import EmotionalSupportService

class EmotionalState(str, Enum):
    """Primary emotional states"""
    HAPPY = "happy"
    SAD = "sad"
    STRESSED = "stressed"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    TIRED = "tired"
    ANGRY = "angry"
    NEUTRAL = "neutral"
    OVERWHELMED = "overwhelmed"
    RELAXED = "relaxed"
    NOSTALGIC = "nostalgic"
    CELEBRATORY = "celebratory"

class MoodIntensity(str, Enum):
    """Intensity levels for emotions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class SupportType(str, Enum):
    """Types of emotional support to provide"""
    COMFORT = "comfort"
    ENCOURAGEMENT = "encouragement"
    CELEBRATION = "celebration"
    CALMING = "calming"
    ENERGIZING = "energizing"
    LISTENING = "listening"
    DISTRACTION = "distraction"
    GROUNDING = "grounding"

class EmotionalIndicators(BaseModel):
    """Detected emotional indicators from conversation"""
    primary_emotion: EmotionalState
    secondary_emotions: List[EmotionalState] = Field(default_factory=list)
    intensity: MoodIntensity = MoodIntensity.MEDIUM
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # Context clues
    stress_indicators: List[str] = Field(default_factory=list)
    celebration_indicators: List[str] = Field(default_factory=list)
    sadness_indicators: List[str] = Field(default_factory=list)
    energy_indicators: List[str] = Field(default_factory=list)
    
    # Time context
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    context_factors: Dict[str, Any] = Field(default_factory=dict)
    
    def get_dominant_emotion(self) -> EmotionalState:
        """Get the most prominent emotion"""
        return self.primary_emotion
    
    def needs_support(self) -> bool:
        """Determine if customer needs emotional support"""
        negative_emotions = [
            EmotionalState.SAD, EmotionalState.STRESSED, 
            EmotionalState.ANXIOUS, EmotionalState.ANGRY,
            EmotionalState.OVERWHELMED
        ]
        return (
            self.primary_emotion in negative_emotions or
            any(emotion in negative_emotions for emotion in self.secondary_emotions)
        )
    
    def get_support_type(self) -> SupportType:
        """Determine appropriate support type"""
        emotion_map = {
            EmotionalState.STRESSED: SupportType.CALMING,
            EmotionalState.ANXIOUS: SupportType.GROUNDING,
            EmotionalState.SAD: SupportType.COMFORT,
            EmotionalState.ANGRY: SupportType.CALMING,
            EmotionalState.TIRED: SupportType.ENERGIZING,
            EmotionalState.OVERWHELMED: SupportType.GROUNDING,
            EmotionalState.EXCITED: SupportType.CELEBRATION,
            EmotionalState.HAPPY: SupportType.CELEBRATION,
            EmotionalState.CELEBRATORY: SupportType.CELEBRATION
        }
        return emotion_map.get(self.primary_emotion, SupportType.LISTENING)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class DrinkRecommendation(BaseModel):
    """Mood-based drink recommendation"""
    drink_name: str
    category: str
    price: float
    emotional_benefit: str
    reasoning: str
    customizations: List[str] = Field(default_factory=list)
    
    # Therapeutic properties
    caffeine_level: str = "medium"  # none, low, medium, high
    comfort_factor: int = Field(ge=1, le=10, default=5)
    energy_factor: int = Field(ge=1, le=10, default=5)
    calming_factor: int = Field(ge=1, le=10, default=5)

class EmotionalResponse(BaseModel):
    """AI response with emotional support"""
    message: str
    emotional_tone: str
    support_type: SupportType
    empathy_level: int = Field(ge=1, le=10, default=5)
    
    # Recommendations
    drink_recommendations: List[DrinkRecommendation] = Field(default_factory=list)
    comfort_suggestions: List[str] = Field(default_factory=list)
    
    # Follow-up actions
    suggest_follow_up: bool = False
    follow_up_topics: List[str] = Field(default_factory=list)
    
    # Mindfulness elements
    breathing_exercise: Optional[str] = None
    positive_affirmation: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class TherapeuticMenu(BaseModel):
    """Menu organized by therapeutic benefits"""
    
    # Stress relief drinks
    stress_relief: List[DrinkRecommendation] = Field(default_factory=list)
    
    # Energy boosting drinks
    energy_boost: List[DrinkRecommendation] = Field(default_factory=list)
    
    # Comfort drinks
    comfort: List[DrinkRecommendation] = Field(default_factory=list)
    
    # Celebration drinks
    celebration: List[DrinkRecommendation] = Field(default_factory=list)
    
    # Focus and clarity
    focus: List[DrinkRecommendation] = Field(default_factory=list)
    
    # Calming and relaxation
    calming: List[DrinkRecommendation] = Field(default_factory=list)
    
    def get_recommendations_for_emotion(
        self, 
        emotion: EmotionalState, 
        count: int = 3
    ) -> List[DrinkRecommendation]:
        """Get drink recommendations for specific emotion"""
        
        emotion_mapping = {
            EmotionalState.STRESSED: self.stress_relief + self.calming,
            EmotionalState.ANXIOUS: self.calming + self.comfort,
            EmotionalState.SAD: self.comfort + self.energy_boost,
            EmotionalState.TIRED: self.energy_boost + self.focus,
            EmotionalState.OVERWHELMED: self.calming + self.stress_relief,
            EmotionalState.HAPPY: self.celebration + self.energy_boost,
            EmotionalState.EXCITED: self.celebration + self.energy_boost,
            EmotionalState.CELEBRATORY: self.celebration,
            EmotionalState.ANGRY: self.calming + self.stress_relief,
            EmotionalState.NEUTRAL: self.focus + self.comfort
        }
        
        recommendations = emotion_mapping.get(emotion, self.comfort)
        return recommendations[:count]

class EmotionalJourney(BaseModel):
    """Track customer's emotional journey throughout session"""
    session_id: str
    customer_id: Optional[str] = None
    
    # Emotional timeline
    emotion_history: List[EmotionalIndicators] = Field(default_factory=list)
    support_provided: List[EmotionalResponse] = Field(default_factory=list)
    
    # Journey metrics
    initial_emotion: Optional[EmotionalState] = None
    current_emotion: Optional[EmotionalState] = None
    emotion_trend: str = "stable"  # improving, declining, stable, volatile
    
    # Intervention effectiveness
    successful_interventions: int = 0
    total_interventions: int = 0
    
    # Session summary
    session_start: datetime = Field(default_factory=datetime.utcnow)
    session_end: Optional[datetime] = None
    overall_satisfaction: Optional[int] = None  # 1-10 scale
    
    def add_emotion_reading(self, emotion: EmotionalIndicators):
        """Add new emotion reading to journey"""
        if not self.initial_emotion:
            self.initial_emotion = emotion.primary_emotion
        
        self.emotion_history.append(emotion)
        self.current_emotion = emotion.primary_emotion
        self._update_trend()
    
    def add_support_response(self, response: EmotionalResponse):
        """Add support response to journey"""
        self.support_provided.append(response)
        self.total_interventions += 1
    
    def mark_intervention_success(self):
        """Mark the last intervention as successful"""
        self.successful_interventions += 1
    
    def _update_trend(self):
        """Update emotional trend based on recent readings"""
        if len(self.emotion_history) < 2:
            self.emotion_trend = "stable"
            return
        
        # Simple trend analysis based on last few readings
        recent_emotions = self.emotion_history[-3:]
        
        positive_emotions = [
            EmotionalState.HAPPY, EmotionalState.EXCITED, 
            EmotionalState.RELAXED, EmotionalState.CELEBRATORY
        ]
        negative_emotions = [
            EmotionalState.SAD, EmotionalState.STRESSED,
            EmotionalState.ANXIOUS, EmotionalState.ANGRY,
            EmotionalState.OVERWHELMED
        ]
        
        positive_count = sum(1 for e in recent_emotions if e.primary_emotion in positive_emotions)
        negative_count = sum(1 for e in recent_emotions if e.primary_emotion in negative_emotions)
        
        if positive_count > negative_count:
            self.emotion_trend = "improving"
        elif negative_count > positive_count:
            self.emotion_trend = "declining"
        else:
            self.emotion_trend = "stable"
    
    def get_journey_summary(self) -> Dict[str, Any]:
        """Get summary of emotional journey"""
        duration = (
            (self.session_end or datetime.utcnow()) - self.session_start
        ).total_seconds() / 60  # in minutes
        
        effectiveness = (
            self.successful_interventions / self.total_interventions
            if self.total_interventions > 0 else 0
        )
        
        return {
            "session_duration_minutes": round(duration, 1),
            "initial_emotion": self.initial_emotion.value if self.initial_emotion else None,
            "final_emotion": self.current_emotion.value if self.current_emotion else None,
            "emotion_trend": self.emotion_trend,
            "interventions_provided": self.total_interventions,
            "intervention_effectiveness": round(effectiveness, 2),
            "emotional_stability": len(set(e.primary_emotion for e in self.emotion_history[-5:])),
            "support_types_used": list(set(r.support_type for r in self.support_provided))
        }
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }