import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

from app.models.emotional_support import (
    EmotionalState, MoodIntensity, SupportType, EmotionalIndicators,
    DrinkRecommendation, EmotionalResponse, TherapeuticMenu, EmotionalJourney
)

class EmotionalSupportService:
    """Service for emotional analysis and support recommendations"""
    
    def __init__(self):
        # Initialize emotion detection patterns
        self.emotion_patterns = self._load_emotion_patterns()
        self.therapeutic_menu = self._create_therapeutic_menu()
        self.active_journeys: Dict[str, EmotionalJourney] = {}
        
        # Support response templates
        self.support_templates = self._load_support_templates()
        
        print("🧠 Emotional Support Service initialized")
    
    def _load_emotion_patterns(self) -> Dict[EmotionalState, Dict[str, List[str]]]:
        """Load emotion detection patterns"""
        return {
            EmotionalState.STRESSED: {
                "keywords": [
                    "stressed", "stress", "overwhelmed", "pressure", "deadline",
                    "busy", "hectic", "chaotic", "frantic", "rushing", "panic",
                    "anxious", "worried", "tension", "burnt out", "exhausted"
                ],
                "phrases": [
                    "too much", "can't handle", "falling behind", "no time",
                    "going crazy", "losing it", "breaking down", "at my limit"
                ],
                "context": ["work", "school", "exam", "meeting", "project"]
            },
            EmotionalState.SAD: {
                "keywords": [
                    "sad", "depressed", "down", "blue", "upset", "crying",
                    "hurt", "disappointed", "heartbroken", "lonely", "empty"
                ],
                "phrases": [
                    "feeling down", "not good", "having a hard time",
                    "going through", "tough day", "bad news", "miss"
                ],
                "context": ["breakup", "loss", "rejection", "failure"]
            },
            EmotionalState.ANXIOUS: {
                "keywords": [
                    "anxious", "nervous", "worried", "scared", "afraid",
                    "panic", "uneasy", "restless", "jittery", "on edge"
                ],
                "phrases": [
                    "freaking out", "what if", "worried about", "scared that",
                    "can't stop thinking", "nervous about"
                ],
                "context": ["interview", "presentation", "date", "test"]
            },
            EmotionalState.TIRED: {
                "keywords": [
                    "tired", "exhausted", "sleepy", "drained", "weary",
                    "fatigue", "worn out", "beat", "sluggish", "lethargic"
                ],
                "phrases": [
                    "no energy", "can't keep", "barely awake", "need sleep",
                    "running on empty", "dead tired"
                ],
                "context": ["late night", "early morning", "long day", "insomnia"]
            },
            EmotionalState.HAPPY: {
                "keywords": [
                    "happy", "great", "amazing", "awesome", "fantastic",
                    "excited", "thrilled", "delighted", "cheerful", "joyful"
                ],
                "phrases": [
                    "feeling good", "in a good mood", "things are great",
                    "going well", "couldn't be better"
                ],
                "context": ["celebration", "success", "achievement", "good news"]
            },
            EmotionalState.EXCITED: {
                "keywords": [
                    "excited", "pumped", "thrilled", "enthusiastic", "hyped",
                    "eager", "anticipating", "can't wait", "looking forward"
                ],
                "phrases": [
                    "so excited", "can't wait", "pumped up", "really looking forward",
                    "absolutely thrilled"
                ],
                "context": ["vacation", "party", "date", "event", "trip"]
            },
            EmotionalState.ANGRY: {
                "keywords": [
                    "angry", "mad", "furious", "pissed", "annoyed", "irritated",
                    "frustrated", "outraged", "livid", "heated"
                ],
                "phrases": [
                    "so angry", "really mad", "can't believe", "fed up",
                    "had enough", "driving me crazy"
                ],
                "context": ["traffic", "work", "people", "situation"]
            },
            EmotionalState.CELEBRATORY: {
                "keywords": [
                    "celebrating", "party", "birthday", "anniversary",
                    "graduation", "promotion", "success", "achievement"
                ],
                "phrases": [
                    "just got", "finally", "we did it", "made it",
                    "dream come true", "best day ever"
                ],
                "context": ["graduation", "job", "wedding", "baby", "award"]
            }
        }
    
    def _create_therapeutic_menu(self) -> TherapeuticMenu:
        """Create therapeutic menu with mood-based recommendations"""
        return TherapeuticMenu(
            stress_relief=[
                DrinkRecommendation(
                    drink_name="Chamomile Tea",
                    category="tea",
                    price=3.25,
                    emotional_benefit="Natural stress relief and relaxation",
                    reasoning="Chamomile has natural calming properties that help reduce stress and anxiety",
                    caffeine_level="none",
                    calming_factor=9,
                    comfort_factor=7
                ),
                DrinkRecommendation(
                    drink_name="Lavender Latte",
                    category="specialty",
                    price=5.25,
                    emotional_benefit="Soothing and stress-reducing",
                    reasoning="Lavender is known for its calming effects and can help ease tension",
                    customizations=["oat milk", "honey"],
                    caffeine_level="low",
                    calming_factor=8,
                    comfort_factor=8
                )
            ],
            energy_boost=[
                DrinkRecommendation(
                    drink_name="Double Shot Americano",
                    category="hot_coffee",
                    price=4.25,
                    emotional_benefit="Quick energy boost and mental clarity",
                    reasoning="High caffeine content helps combat fatigue and increase alertness",
                    caffeine_level="high",
                    energy_factor=10,
                    comfort_factor=6
                ),
                DrinkRecommendation(
                    drink_name="Matcha Latte",
                    category="specialty",
                    price=5.50,
                    emotional_benefit="Sustained energy without jitters",
                    reasoning="Matcha provides steady energy and L-theanine for calm focus",
                    caffeine_level="medium",
                    energy_factor=8,
                    calming_factor=6
                )
            ],
            comfort=[
                DrinkRecommendation(
                    drink_name="Hot Chocolate",
                    category="specialty",
                    price=4.25,
                    emotional_benefit="Warm comfort and mood boost",
                    reasoning="Chocolate releases endorphins and provides emotional comfort",
                    customizations=["whipped cream", "marshmallows"],
                    caffeine_level="low",
                    comfort_factor=10,
                    calming_factor=7
                ),
                DrinkRecommendation(
                    drink_name="Vanilla Chai Latte",
                    category="tea",
                    price=4.75,
                    emotional_benefit="Warming spices for emotional comfort",
                    reasoning="Warming spices like cinnamon and cardamom can lift spirits",
                    customizations=["extra spicy", "oat milk"],
                    caffeine_level="medium",
                    comfort_factor=9,
                    calming_factor=6
                )
            ],
            celebration=[
                DrinkRecommendation(
                    drink_name="Caramel Macchiato",
                    category="specialty",
                    price=5.75,
                    emotional_benefit="Indulgent treat for special moments",
                    reasoning="Sweet and rich flavors perfect for celebrating achievements",
                    customizations=["extra caramel", "whipped cream"],
                    caffeine_level="medium",
                    comfort_factor=8,
                    energy_factor=7
                ),
                DrinkRecommendation(
                    drink_name="Signature Frappuccino",
                    category="cold_coffee",
                    price=6.25,
                    emotional_benefit="Fun and festive celebration drink",
                    reasoning="Indulgent and Instagram-worthy for special occasions",
                    customizations=["whipped cream", "extra shot"],
                    caffeine_level="medium",
                    comfort_factor=7,
                    energy_factor=6
                )
            ],
            calming=[
                DrinkRecommendation(
                    drink_name="Herbal Tea Blend",
                    category="tea",
                    price=3.00,
                    emotional_benefit="Deep relaxation and peace",
                    reasoning="Caffeine-free herbs promote relaxation and mental calm",
                    caffeine_level="none",
                    calming_factor=10,
                    comfort_factor=6
                ),
                DrinkRecommendation(
                    drink_name="Golden Milk Latte",
                    category="specialty",
                    price=5.25,
                    emotional_benefit="Anti-inflammatory comfort",
                    reasoning="Turmeric and spices have calming, anti-inflammatory properties",
                    customizations=["coconut milk", "honey"],
                    caffeine_level="none",
                    calming_factor=8,
                    comfort_factor=7
                )
            ],
            focus=[
                DrinkRecommendation(
                    drink_name="Green Tea",
                    category="tea",
                    price=2.75,
                    emotional_benefit="Clear focus without anxiety",
                    reasoning="L-theanine in green tea promotes calm alertness",
                    caffeine_level="low",
                    energy_factor=6,
                    calming_factor=7
                )
            ]
        )
    
    def _load_support_templates(self) -> Dict[SupportType, List[str]]:
        """Load emotional support response templates"""
        return {
            SupportType.COMFORT: [
                "I can hear that you're going through a tough time right now. Sometimes a warm, comforting drink can provide a little solace. Would you like me to suggest something that might help you feel a bit better?",
                "That sounds really difficult. I'm sorry you're dealing with that. Let me recommend something that might bring you a moment of comfort.",
                "I understand this is a challenging moment for you. Sometimes a little self-care, like treating yourself to something warm and comforting, can make a small difference."
            ],
            SupportType.CALMING: [
                "It sounds like things are feeling pretty intense right now. Taking a moment to breathe and having something calming might help you feel more centered. Would you like a recommendation?",
                "I can sense the stress in what you're sharing. Sometimes slowing down with a calming drink can help reset your mindset. Let me suggest something soothing.",
                "That level of stress sounds overwhelming. A calming beverage and a few deep breaths might help you feel more grounded."
            ],
            SupportType.ENERGIZING: [
                "It sounds like you could use a gentle energy boost! Let me suggest something that might help you feel more alert and ready to tackle what's ahead.",
                "Fatigue can be so draining. Would you like something that could help restore your energy levels?",
                "Sometimes we all need a little pick-me-up. I have some great options that might help you feel more energized."
            ],
            SupportType.CELEBRATION: [
                "That's wonderful news! This calls for something special to celebrate your achievement. Let me suggest some indulgent options perfect for marking this moment.",
                "Congratulations! This is definitely worth celebrating. How about something festive to commemorate this success?",
                "What an exciting milestone! Let's find you something delightful to toast this accomplishment."
            ],
            SupportType.GROUNDING: [
                "When everything feels chaotic, sometimes focusing on simple, grounding experiences can help. Let me suggest something that might help you feel more centered.",
                "It sounds like you need a moment to pause and reconnect with yourself. A mindful beverage choice might help you feel more grounded.",
                "That's a lot to handle. Sometimes taking a moment for yourself with something soothing can help you regain your balance."
            ]
        }
    
    async def analyze_emotion(
        self, 
        message: str, 
        conversation_history: List[Dict] = None,
        context: Dict[str, Any] = None
    ) -> EmotionalIndicators:
        """Analyze emotional state from message and context"""
        
        message_lower = message.lower()
        detected_emotions = []
        
        # Analyze each emotion pattern
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            indicators = []
            
            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in message_lower:
                    score += 2
                    indicators.append(keyword)
            
            # Check phrases
            for phrase in patterns["phrases"]:
                if phrase in message_lower:
                    score += 3
                    indicators.append(phrase)
            
            # Check context words
            for context_word in patterns["context"]:
                if context_word in message_lower:
                    score += 1
                    indicators.append(f"context:{context_word}")
            
            if score > 0:
                detected_emotions.append((emotion, score, indicators))
        
        # Sort by score and determine primary emotion
        detected_emotions.sort(key=lambda x: x[1], reverse=True)
        
        if detected_emotions:
            primary_emotion = detected_emotions[0][0]
            confidence = min(detected_emotions[0][1] / 10.0, 1.0)
            secondary_emotions = [e[0] for e in detected_emotions[1:3]]
            
            # Determine intensity based on language patterns
            intensity = self._determine_intensity(message_lower, detected_emotions[0][2])
            
        else:
            primary_emotion = EmotionalState.NEUTRAL
            secondary_emotions = []
            confidence = 0.3
            intensity = MoodIntensity.LOW
        
        # Create emotional indicators
        indicators = EmotionalIndicators(
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            intensity=intensity,
            confidence=confidence,
            context_factors={
                "message_length": len(message),
                "conversation_context": conversation_history[-2:] if conversation_history else [],
                "external_context": context or {}
            }
        )
        
        # Add specific indicator lists
        if primary_emotion == EmotionalState.STRESSED:
            indicators.stress_indicators = [i for i in detected_emotions[0][2] if not i.startswith("context:")]
        elif primary_emotion == EmotionalState.CELEBRATORY:
            indicators.celebration_indicators = [i for i in detected_emotions[0][2] if not i.startswith("context:")]
        elif primary_emotion == EmotionalState.SAD:
            indicators.sadness_indicators = [i for i in detected_emotions[0][2] if not i.startswith("context:")]
        elif primary_emotion in [EmotionalState.TIRED, EmotionalState.EXCITED]:
            indicators.energy_indicators = [i for i in detected_emotions[0][2] if not i.startswith("context:")]
        
        return indicators
    
    def _determine_intensity(self, message: str, indicators: List[str]) -> MoodIntensity:
        """Determine emotional intensity from language patterns"""
        
        # Intensity amplifiers
        high_intensity_words = [
            "extremely", "incredibly", "absolutely", "completely", "totally",
            "really really", "so so", "very very", "!!!", "can't even"
        ]
        
        medium_intensity_words = [
            "very", "really", "quite", "pretty", "fairly", "!!"
        ]
        
        # Check for amplifiers
        for amplifier in high_intensity_words:
            if amplifier in message:
                return MoodIntensity.HIGH
        
        for amplifier in medium_intensity_words:
            if amplifier in message:
                return MoodIntensity.MEDIUM
        
        # Check number of indicators
        if len(indicators) >= 3:
            return MoodIntensity.HIGH
        elif len(indicators) >= 2:
            return MoodIntensity.MEDIUM
        else:
            return MoodIntensity.LOW
    
    async def generate_emotional_response(
        self, 
        emotion_indicators: EmotionalIndicators,
        menu_data: Dict[str, Any],
        session_id: str
    ) -> EmotionalResponse:
        """Generate appropriate emotional support response"""
        
        support_type = emotion_indicators.get_support_type()
        
        # Get base response template
        templates = self.support_templates.get(support_type, [])
        base_message = templates[0] if templates else "I understand how you're feeling."
        
        # Get drink recommendations
        drink_recommendations = self.therapeutic_menu.get_recommendations_for_emotion(
            emotion_indicators.primary_emotion, count=2
        )
        
        # Generate comfort suggestions based on emotion
        comfort_suggestions = self._generate_comfort_suggestions(emotion_indicators)
        
        # Generate breathing exercise for high stress/anxiety
        breathing_exercise = None
        if emotion_indicators.primary_emotion in [EmotionalState.STRESSED, EmotionalState.ANXIOUS]:
            breathing_exercise = "Try this: Breathe in slowly for 4 counts, hold for 4, breathe out for 6. Repeat 3 times."
        
        # Generate positive affirmation
        affirmation = self._generate_affirmation(emotion_indicators.primary_emotion)
        
        # Determine empathy level
        empathy_level = 8 if emotion_indicators.needs_support() else 5
        
        # Create response
        response = EmotionalResponse(
            message=base_message,
            emotional_tone=support_type.value,
            support_type=support_type,
            empathy_level=empathy_level,
            drink_recommendations=drink_recommendations,
            comfort_suggestions=comfort_suggestions,
            breathing_exercise=breathing_exercise,
            positive_affirmation=affirmation,
            suggest_follow_up=emotion_indicators.intensity in [MoodIntensity.HIGH, MoodIntensity.EXTREME]
        )
        
        # Track emotional journey
        await self._update_emotional_journey(session_id, emotion_indicators, response)
        
        return response
    
    def _generate_comfort_suggestions(self, emotion_indicators: EmotionalIndicators) -> List[str]:
        """Generate comfort suggestions based on emotional state"""
        
        suggestions_map = {
            EmotionalState.STRESSED: [
                "Take a few deep breaths",
                "Find a quiet corner to sit and relax",
                "Consider taking a short walk after your coffee",
                "Try to focus on one thing at a time"
            ],
            EmotionalState.ANXIOUS: [
                "Ground yourself by noticing 5 things you can see around you",
                "Remember that this feeling will pass",
                "Focus on your breathing",
                "Find a comfortable spot to sit"
            ],
            EmotionalState.SAD: [
                "Be gentle with yourself today",
                "Consider calling a friend or loved one",
                "It's okay to feel sad - your feelings are valid",
                "Small acts of self-care can help"
            ],
            EmotionalState.TIRED: [
                "Listen to your body's need for rest",
                "Try to get some natural light",
                "Stay hydrated throughout the day",
                "Consider a power nap if possible"
            ],
            EmotionalState.OVERWHELMED: [
                "Break tasks into smaller, manageable pieces",
                "It's okay to ask for help",
                "Take things one step at a time",
                "Prioritize what's most important today"
            ]
        }
        
        return suggestions_map.get(emotion_indicators.primary_emotion, [
            "Take a moment for yourself",
            "Practice self-compassion",
            "Remember that you're doing your best"
        ])
    
    def _generate_affirmation(self, emotion: EmotionalState) -> str:
        """Generate positive affirmation based on emotional state"""
        
        affirmations = {
            EmotionalState.STRESSED: "You have handled difficult situations before, and you can handle this too.",
            EmotionalState.ANXIOUS: "You are safe in this moment, and you have the strength to face what comes.",
            EmotionalState.SAD: "Your feelings are valid, and it's okay to take time to heal.",
            EmotionalState.TIRED: "Rest is not a luxury, it's necessary. You deserve to recharge.",
            EmotionalState.OVERWHELMED: "You don't have to do everything at once. Take it one step at a time.",
            EmotionalState.HAPPY: "Your joy is beautiful and worth celebrating.",
            EmotionalState.EXCITED: "Your enthusiasm is contagious and wonderful.",
            EmotionalState.CELEBRATORY: "You've earned this moment of celebration. Enjoy it fully."
        }
        
        return affirmations.get(emotion, "You are worthy of kindness, especially from yourself.")
    
    async def _update_emotional_journey(
        self, 
        session_id: str, 
        emotion_indicators: EmotionalIndicators,
        response: EmotionalResponse
    ):
        """Update or create emotional journey for session"""
        
        if session_id not in self.active_journeys:
            self.active_journeys[session_id] = EmotionalJourney(session_id=session_id)
        
        journey = self.active_journeys[session_id]
        journey.add_emotion_reading(emotion_indicators)
        journey.add_support_response(response)
    
    async def get_emotional_journey(self, session_id: str) -> Optional[EmotionalJourney]:
        """Get emotional journey for session"""
        return self.active_journeys.get(session_id)
    
    async def end_emotional_journey(self, session_id: str, satisfaction_rating: Optional[int] = None):
        """End emotional journey and get summary"""
        if session_id in self.active_journeys:
            journey = self.active_journeys[session_id]
            journey.session_end = datetime.utcnow()
            journey.overall_satisfaction = satisfaction_rating
            
            summary = journey.get_journey_summary()
            
            # Clean up (in production, you'd save this to database)
            del self.active_journeys[session_id]
            
            return summary
        return None
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get emotional support service status"""
        return {
            "active_journeys": len(self.active_journeys),
            "emotion_patterns_loaded": len(self.emotion_patterns),
            "therapeutic_menu_items": sum([
                len(self.therapeutic_menu.stress_relief),
                len(self.therapeutic_menu.energy_boost),
                len(self.therapeutic_menu.comfort),
                len(self.therapeutic_menu.celebration),
                len(self.therapeutic_menu.calming),
                len(self.therapeutic_menu.focus)
            ]),
            "support_templates": len(self.support_templates),
            "service_ready": True
        }
    async def analyze_message(self, message: str, context: dict = None) -> dict:
        """Analyze message for emotional content - Simple version"""
        try:
            message_lower = message.lower()
            
            # Simple emotion detection
            stress_words = ['stressed', 'overwhelmed', 'anxious', 'pressure', 'busy', 'hectic', 'tired']
            sadness_words = ['sad', 'down', 'depressed', 'upset', 'hurt', 'disappointed', 'rough day']
            happy_words = ['happy', 'great', 'amazing', 'excited', 'wonderful', 'fantastic', 'celebrating']
            
            detected_moods = []
            support_needed = False
            
            if any(word in message_lower for word in stress_words):
                detected_moods.append('stressed')
                support_needed = True
            
            if any(word in message_lower for word in sadness_words):
                detected_moods.append('sad')
                support_needed = True
                
            if any(word in message_lower for word in happy_words):
                detected_moods.append('happy')
            
            if not detected_moods:
                detected_moods = ['neutral']
            
            return {
                "support_needed": support_needed,
                "detected_moods": detected_moods,
                "confidence": 0.8 if support_needed else 0.3,
                "support_type": "calming" if support_needed else "neutral"
            }
            
        except Exception as e:
            print(f"❌ Error in emotional analysis: {str(e)}")
            return {
                "support_needed": False,
                "detected_moods": ["neutral"],
                "confidence": 0.0
            }

    async def enhance_response(self, ai_response: dict, emotional_response: dict) -> dict:
        """Enhance AI response with emotional support"""
        try:
            if not emotional_response.get("support_needed"):
                return ai_response
            
            # Add supportive messages
            support_messages = {
                "stressed": "I can sense you're feeling stressed. Let me suggest something comforting that might help you relax. 💙",
                "sad": "I'm sorry you're having a difficult time. Sometimes a warm, comforting drink can provide a little solace. 🫂",
                "anxious": "I understand you're feeling anxious. Taking a moment to breathe and having something calming might help. 🌸"
            }
            
            detected_moods = emotional_response.get("detected_moods", [])
            if detected_moods and detected_moods[0] in support_messages:
                support_msg = support_messages[detected_moods[0]]
                ai_response["message"] = support_msg + "\n\n" + ai_response.get("message", "")
                
                # Add emotional support data
                ai_response["emotional_support"] = {
                    "detected_mood": detected_moods[0],
                    "support_provided": True,
                    "breathing_exercise": "Try this: Breathe in slowly for 4 counts, hold for 4, breathe out for 6. Repeat 3 times." if detected_moods[0] in ['stressed', 'anxious'] else None
                }
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Error enhancing response: {str(e)}")
            return ai_response