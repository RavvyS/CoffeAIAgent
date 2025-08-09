import google.generativeai as genai
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from app.utils.config import settings

class AIService:
    """AI service for natural conversation using Gemini Flash"""
    
    def __init__(self):
        self.model = None
        self.initialized = False
        
        # AI configuration
        self.config = settings.get_ai_config()
        self.shop_info = settings.get_shop_info()
        
        # Initialize if API key is available
        if self.config["api_key"]:
            self._initialize_ai()
    
    def _initialize_ai(self):
        """Initialize Gemini AI client"""
        try:
            # Configure the API key
            genai.configure(api_key=self.config["api_key"])
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name=self.config["model"],
                generation_config={
                    "temperature": self.config["temperature"],
                    "max_output_tokens": self.config["max_tokens"],
                }
            )
            
            self.initialized = True
            print(f"🤖 AI service initialized with model: {self.config['model']}")
            
        except Exception as e:
            print(f"❌ Failed to initialize AI service: {str(e)}")
            self.initialized = False
    
    async def test_connection(self) -> bool:
        """Test AI service connection"""
        if not self.initialized:
            return False
        
        try:
            # Simple test prompt
            response = self.model.generate_content("Hello, can you respond with 'AI service working'?")
            return "working" in response.text.lower()
        except:
            return False
    
    def _build_system_prompt(self, context: dict, menu: dict) -> str:
        """Build context-aware system prompt for the AI"""
        
        # Extract relevant context
        conversation_history = context.get("conversation_history", [])[-5:]  # Last 5 messages
        customer_preferences = context.get("customer_preferences", {})
        current_order = context.get("current_order", {"items": [], "total": 0.0})
        weather = context.get("weather", {})
        mood_indicators = context.get("mood_indicators", [])
        
        # Build weather context
        weather_context = ""
        if weather:
            weather_desc = weather.get("description", "").lower()
            temp = weather.get("temperature")
            if temp:
                weather_context = f"Current weather: {weather_desc}, {temp}°F. "
        
        # Build order context
        order_context = ""
        if current_order["items"]:
            items_list = [item["name"] for item in current_order["items"]]
            order_context = f"Current order: {', '.join(items_list)} (${current_order['total']:.2f}). "
        
        # Build conversation context
        history_context = ""
        if conversation_history:
            recent_messages = []
            for msg in conversation_history[-3:]:
                role = "Customer" if msg["role"] == "user" else "You"
                recent_messages.append(f"{role}: {msg['content']}")
            history_context = f"Recent conversation: {' | '.join(recent_messages)}"
        
        # Build mood context
        mood_context = ""
        if mood_indicators:
            mood_context = f"Customer seems: {', '.join(mood_indicators)}. "
        
        # Available menu items (simplified for context)
        menu_highlights = []
        if menu.get("categories"):
            for category in menu["categories"][:3]:  # Top 3 categories
                if category.get("items"):
                    popular_items = [item["name"] for item in category["items"][:2]]
                    menu_highlights.extend(popular_items)
        
        system_prompt = f"""You are a friendly, knowledgeable AI assistant for {self.shop_info['name']}, a coffee shop in {self.shop_info['location']}. 

PERSONALITY & TONE:
- Be warm, conversational, and genuinely helpful
- Match the customer's energy level - if they're in a hurry, be efficient; if they want to chat, be engaging
- Use natural language, avoid being overly formal or robotic
- Show enthusiasm for coffee and creating great experiences

CURRENT CONTEXT:
{weather_context}{order_context}{mood_context}
{history_context}

MENU HIGHLIGHTS: {', '.join(menu_highlights[:6])}

YOUR CAPABILITIES:
1. Help customers browse and order from our menu
2. Make personalized recommendations based on weather, mood, and preferences
3. Answer questions about ingredients, allergens, and customizations
4. Handle order modifications and special requests
5. Provide friendly conversation while staying focused on service
6. Guide customers through the ordering process to payment

GUIDELINES:
- If customer mentions dietary restrictions or allergies, prioritize safety and offer suitable alternatives
- For weather-based recommendations: Cold weather → hot drinks, Hot weather → cold drinks, Rainy → comfort drinks
- If customer seems stressed or having a bad day, suggest calming options like herbal teas or comfort foods
- If they're celebrating something, suggest special or indulgent options
- Always confirm order details before suggesting checkout
- If you're unsure about something, it's okay to say so and offer to check with staff
- Keep responses concise unless the customer wants detailed information

Remember: You're here to make their coffee shop experience delightful and personal!"""

        return system_prompt
    
    async def generate_response(self, message: str, context: dict, menu: dict) -> dict:
        """Generate AI response based on user message and context"""
        
        if not self.initialized:
            return {
                "message": "I apologize, but I'm having trouble connecting to my AI service right now. Please try again in a moment.",
                "error": True
            }
        
        try:
            # Build system prompt with current context
            system_prompt = self._build_system_prompt(context, menu)
            
            # Create full prompt
            full_prompt = f"{system_prompt}\n\nCustomer: {message}\n\nAssistant:"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            ai_message = response.text.strip()
            
            # Analyze the conversation for context updates
            context_updates = self._analyze_conversation(message, ai_message, context)
            
            # Generate suggestions based on conversation
            suggestions = self._generate_suggestions(message, ai_message, context, menu)
            
            return {
                "message": ai_message,
                "context_updates": context_updates,
                "suggestions": suggestions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ AI service error: {str(e)}")
            return {
                "message": "I apologize, but I'm having trouble processing your request right now. Could you please try rephrasing your question?",
                "error": True,
                "error_details": str(e) if settings.DEBUG else None
            }
    
    def _analyze_conversation(self, user_message: str, ai_response: str, context: dict) -> dict:
        """Analyze conversation to extract context updates"""
        updates = {}
        
        user_lower = user_message.lower()
        ai_lower = ai_response.lower()
        
        # Detect dietary preferences/restrictions
        dietary_keywords = {
            "vegan": "vegan",
            "vegetarian": "vegetarian", 
            "lactose": "lactose_intolerant",
            "dairy-free": "dairy_free",
            "gluten": "gluten_free",
            "nut": "nut_allergy",
            "sugar": "low_sugar"
        }
        
        current_prefs = context.get("customer_preferences", {})
        for keyword, pref in dietary_keywords.items():
            if keyword in user_lower and pref not in current_prefs:
                if "customer_preferences" not in updates:
                    updates["customer_preferences"] = current_prefs.copy()
                updates["customer_preferences"][pref] = True
        
        # Detect mood indicators
        mood_keywords = {
            "tired": "tired",
            "stressed": "stressed", 
            "rush": "in_hurry",
            "hurry": "in_hurry",
            "celebrating": "celebratory",
            "happy": "happy",
            "sad": "needs_comfort",
            "cold": "wants_warmth",
            "hot": "wants_cooling"
        }
        
        detected_moods = []
        for keyword, mood in mood_keywords.items():
            if keyword in user_lower:
                detected_moods.append(mood)
        
        if detected_moods:
            updates["mood_indicators"] = detected_moods
        
        # Detect order intent
        order_keywords = ["order", "get", "have", "want", "like"]
        if any(keyword in user_lower for keyword in order_keywords):
            updates["context_flags"] = context.get("context_flags", {}).copy()
            updates["context_flags"]["order_intent"] = True
        
        return updates
    
    def _generate_suggestions(self, user_message: str, ai_response: str, context: dict, menu: dict) -> List[str]:
        """Generate helpful suggestions based on conversation"""
        suggestions = []
        
        user_lower = user_message.lower()
        current_order = context.get("current_order", {"items": []})
        
        # If no items in order yet, suggest popular items
        if not current_order["items"]:
            if any(word in user_lower for word in ["recommend", "suggest", "popular", "good"]):
                suggestions.extend([
                    "See our popular drinks",
                    "View today's specials", 
                    "Browse by category"
                ])
        
        # If items in order, suggest order actions
        elif current_order["items"]:
            suggestions.extend([
                "Add another item",
                "Review my order",
                "Ready to checkout"
            ])
        
        # Weather-based suggestions
        weather = context.get("weather", {})
        if weather:
            temp = weather.get("temperature", 70)
            if temp < 50:
                suggestions.append("Hot seasonal drinks")
            elif temp > 80:
                suggestions.append("Iced refreshers")
        
        # Mood-based suggestions
        mood_indicators = context.get("mood_indicators", [])
        if "stressed" in mood_indicators:
            suggestions.append("Calming herbal teas")
        elif "celebratory" in mood_indicators:
            suggestions.append("Special celebration drinks")
        
        # Remove duplicates and limit to 4 suggestions
        return list(dict.fromkeys(suggestions))[:4]
    
    async def generate_menu_description(self, item: dict) -> str:
        """Generate appealing description for menu item"""
        if not self.initialized:
            return item.get("description", "Delicious coffee shop item")
        
        try:
            prompt = f"""Write a brief, appealing description (1-2 sentences) for this coffee shop menu item:
            
Name: {item.get('name', 'Unknown')}
Category: {item.get('category', 'Beverage')}
Price: ${item.get('price', 0):.2f}
Ingredients: {item.get('ingredients', [])}

Make it sound delicious and inviting, mentioning key flavors or characteristics."""

            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Error generating menu description: {str(e)}")
            return item.get("description", "A delightful coffee shop favorite")
    
    def get_service_status(self) -> dict:
        """Get current service status"""
        return {
            "initialized": self.initialized,
            "model": self.config["model"] if self.initialized else None,
            "api_key_configured": bool(self.config["api_key"]),
            "last_check": datetime.utcnow().isoformat()
        }