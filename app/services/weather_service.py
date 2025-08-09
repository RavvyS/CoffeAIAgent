import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

from app.utils.config import settings

class WeatherService:
    """Weather service for getting current conditions to make menu recommendations"""
    
    def __init__(self):
        self.config = settings.get_weather_config()
        self.cache = {}
        self.cache_duration = 600  # 10 minutes cache
        
        # Weather to menu mapping
        self.weather_recommendations = {
            "cold": {
                "temperature_threshold": 50,
                "drinks": ["Hot Coffee", "Cappuccino", "Hot Chocolate", "Chai Latte"],
                "foods": ["Warm Pastries", "Soup", "Hot Sandwiches"]
            },
            "hot": {
                "temperature_threshold": 80,
                "drinks": ["Iced Coffee", "Cold Brew", "Frappés", "Smoothies"],
                "foods": ["Salads", "Cold Sandwiches", "Ice Cream"]
            },
            "rainy": {
                "conditions": ["rain", "drizzle", "thunderstorm"],
                "drinks": ["Hot Tea", "Chai Latte", "Hot Chocolate"],
                "foods": ["Comfort Food", "Warm Pastries", "Soup"]
            },
            "sunny": {
                "conditions": ["clear", "sunny"],
                "drinks": ["Cold Brew", "Iced Tea", "Smoothies", "Fruit Drinks"],
                "foods": ["Light Salads", "Fresh Pastries"]
            }
        }
    
    async def get_current_weather(self, city: Optional[str] = None) -> Dict:
        """Get current weather data"""
        
        if not self.config["enabled"]:
            return self._get_mock_weather()
        
        city = city or self.config["default_city", "New York"]
        cache_key = f"weather_{city}"
        
        # Check cache first
        cached_data = self._get_cached_weather(cache_key)
        if cached_data:
            return cached_data
        
        try:
            async with httpx.AsyncClient() as client:
                # Get current weather from OpenWeatherMap
                url = f"{self.config['api_url']}/weather"
                params = {
                    "q": city,
                    "appid": self.config["api_key"],
                    "units": "imperial"  # Fahrenheit
                }
                
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                
                weather_data = response.json()
                processed_data = self._process_weather_data(weather_data)
                
                # Cache the result
                self._cache_weather(cache_key, processed_data)
                
                return processed_data
                
        except Exception as e:
            print(f"❌ Weather API error: {str(e)}")
            # Return mock data as fallback
            return self._get_mock_weather()
    
    def _process_weather_data(self, raw_data: dict) -> dict:
        """Process raw weather API response into useful format"""
        try:
            main = raw_data.get("main", {})
            weather = raw_data.get("weather", [{}])[0]
            
            temperature = main.get("temp", 70)
            condition = weather.get("main", "Clear").lower()
            description = weather.get("description", "clear sky")
            
            # Determine weather category for recommendations
            weather_category = self._categorize_weather(temperature, condition)
            
            return {
                "temperature": round(temperature),
                "condition": condition,
                "description": description,
                "feels_like": round(main.get("feels_like", temperature)),
                "humidity": main.get("humidity", 50),
                "city": raw_data.get("name", "Unknown"),
                "category": weather_category,
                "recommendations": self._get_weather_recommendations(weather_category, temperature),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "openweathermap"
            }
            
        except Exception as e:
            print(f"❌ Error processing weather data: {str(e)}")
            return self._get_mock_weather()
    
    def _categorize_weather(self, temperature: float, condition: str) -> str:
        """Categorize weather for menu recommendations"""
        
        # Temperature-based categorization
        if temperature <= self.weather_recommendations["cold"]["temperature_threshold"]:
            return "cold"
        elif temperature >= self.weather_recommendations["hot"]["temperature_threshold"]:
            return "hot"
        
        # Condition-based categorization
        condition_lower = condition.lower()
        
        if any(rain_cond in condition_lower for rain_cond in self.weather_recommendations["rainy"]["conditions"]):
            return "rainy"
        elif any(sunny_cond in condition_lower for sunny_cond in self.weather_recommendations["sunny"]["conditions"]):
            return "sunny"
        
        # Default to mild weather
        return "mild"
    
    def _get_weather_recommendations(self, category: str, temperature: float) -> dict:
        """Get menu recommendations based on weather"""
        recommendations = {
            "drinks": [],
            "foods": [],
            "message": ""
        }
        
        if category == "cold":
            recommendations["drinks"] = self.weather_recommendations["cold"]["drinks"]
            recommendations["foods"] = self.weather_recommendations["cold"]["foods"]
            recommendations["message"] = f"It's chilly out there ({temperature}°F)! How about something warm to heat you up?"
            
        elif category == "hot":
            recommendations["drinks"] = self.weather_recommendations["hot"]["drinks"]
            recommendations["foods"] = self.weather_recommendations["hot"]["foods"]
            recommendations["message"] = f"It's quite warm today ({temperature}°F)! Perfect weather for something cool and refreshing!"
            
        elif category == "rainy":
            recommendations["drinks"] = self.weather_recommendations["rainy"]["drinks"]
            recommendations["foods"] = self.weather_recommendations["rainy"]["foods"]
            recommendations["message"] = "Looks like it's raining! Perfect weather for something comforting and warm."
            
        elif category == "sunny":
            recommendations["drinks"] = self.weather_recommendations["sunny"]["drinks"]
            recommendations["foods"] = self.weather_recommendations["sunny"]["foods"]
            recommendations["message"] = f"Beautiful sunny day ({temperature}°F)! Great weather for something light and refreshing!"
            
        else:  # mild weather
            recommendations["drinks"] = ["Coffee", "Tea", "Specialty Drinks"]
            recommendations["foods"] = ["Pastries", "Sandwiches", "Snacks"]
            recommendations["message"] = f"Nice weather today ({temperature}°F)! What sounds good to you?"
        
        return recommendations
    
    def _get_cached_weather(self, cache_key: str) -> Optional[dict]:
        """Get weather data from cache if still valid"""
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            cache_age = datetime.utcnow() - cached_item["cached_at"]
            
            if cache_age.total_seconds() < self.cache_duration:
                return cached_item["data"]
            else:
                # Remove expired cache
                del self.cache[cache_key]
        
        return None
    
    def _cache_weather(self, cache_key: str, data: dict):
        """Cache weather data"""
        self.cache[cache_key] = {
            "data": data,
            "cached_at": datetime.utcnow()
        }
        
        # Clean up old cache entries (keep only last 10)
        if len(self.cache) > 10:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["cached_at"])
            del self.cache[oldest_key]
    
    def _get_mock_weather(self) -> dict:
        """Return mock weather data when API is unavailable"""
        # Generate realistic mock data based on current time
        hour = datetime.now().hour
        
        # Simulate daily temperature variation
        base_temp = 70
        if 6 <= hour <= 18:  # Daytime
            temperature = base_temp + (hour - 12) * 2  # Peak at 2 PM
        else:  # Nighttime
            temperature = base_temp - 10
        
        return {
            "temperature": round(max(40, min(85, temperature))),
            "condition": "clear",
            "description": "simulated weather",
            "feels_like": round(temperature - 2),
            "humidity": 50,
            "city": self.config.get("default_city", "New York"),
            "category": "mild",
            "recommendations": {
                "drinks": ["Coffee", "Tea", "Specialty Drinks"],
                "foods": ["Pastries", "Sandwiches", "Snacks"],
                "message": "What sounds good to you today?"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock"
        }
    
    async def get_weather_for_recommendation(self, preference: Optional[str] = None) -> str:
        """Get weather-appropriate recommendation message"""
        weather_data = await self.get_current_weather()
        
        if preference and preference.lower() in ["hot", "cold", "warm", "cool"]:
            # User specified temperature preference
            if preference.lower() in ["hot", "warm"]:
                return "Perfect! I'll recommend some of our hot beverages."
            else:
                return "Great choice! Let me suggest some refreshing cold options."
        
        # Use weather-based recommendation
        return weather_data.get("recommendations", {}).get("message", "What sounds good to you?")
    
    def get_service_status(self) -> dict:
        """Get weather service status"""
        return {
            "enabled": self.config["enabled"],
            "api_configured": bool(self.config["api_key"]),
            "cache_size": len(self.cache),
            "last_update": max([item["cached_at"] for item in self.cache.values()], default=None),
            "default_city": self.config["default_city"]
        }