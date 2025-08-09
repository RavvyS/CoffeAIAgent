import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings:
    APP_NAME: str = "Coffee Shop AI Agent"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Fixed Redis settings
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
 # Redis settings - Fixed version
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")  # For Redis Cloud
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    
    # Safe integer parsing for Redis port and DB
    _redis_port = os.getenv("REDIS_PORT", "6379")
    REDIS_PORT: int = int(_redis_port) if _redis_port.isdigit() else 6379
    
    _redis_db = os.getenv("REDIS_DB", "0") 
    REDIS_DB: int = int(_redis_db) if _redis_db.isdigit() else 0
    
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # AI settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Other settings
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    SHOP_NAME: str = os.getenv("SHOP_NAME", "Claude's Coffee Corner")
    SHOP_LOCATION: str = os.getenv("SHOP_LOCATION", "Downtown")
    ALLOWED_ORIGINS: list = ["*"]
    MAX_REQUESTS_PER_MINUTE: int = 30
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    
    def get_ai_config(self):
        return {"api_key": self.GEMINI_API_KEY, "model": self.GEMINI_MODEL, "max_tokens": 1000, "temperature": 0.7}
    
    def get_weather_config(self):
        return {"api_key": self.WEATHER_API_KEY, "enabled": bool(self.WEATHER_API_KEY)}
    
    def get_shop_info(self):
        return {"name": self.SHOP_NAME, "location": self.SHOP_LOCATION}

settings = Settings()