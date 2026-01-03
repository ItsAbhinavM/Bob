import httpx
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    async def get_weather(self, location: str) -> Dict:
        """Fetch current weather data for a given location"""
        if not self.api_key:
            return {
                "error": "Weather API key not configured",
                "location": location,
                "temperature": 0,
                "condition": "unknown",
                "description": "Weather service unavailable",
                "humidity": 0,
                "wind_speed": 0,
                "suggestion": "Unable to fetch weather data"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "q": location,
                    "appid": self.api_key,
                    "units": "metric"
                }
                
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                weather_info = {
                    "location": data["name"],
                    "temperature": data["main"]["temp"],
                    "condition": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "suggestion": self._generate_suggestion(data)
                }
                
                return weather_info
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "error": f"Location '{location}' not found",
                    "location": location,
                    "temperature": 0,
                    "condition": "unknown",
                    "description": "Location not found",
                    "humidity": 0,
                    "wind_speed": 0,
                    "suggestion": "Please provide a valid city name"
                }
            raise
        except Exception as e:
            return {
                "error": str(e),
                "location": location,
                "temperature": 0,
                "condition": "unknown",
                "description": "Error fetching weather",
                "humidity": 0,
                "wind_speed": 0,
                "suggestion": "Unable to fetch weather data at this time"
            }
    
    def _generate_suggestion(self, weather_data: Dict) -> str:
        """Generate a helpful suggestion based on weather conditions"""
        condition = weather_data["weather"][0]["main"].lower()
        temp = weather_data["main"]["temp"]
        
        suggestions = []
        
        if temp > 30:
            suggestions.append("It's quite hot! Stay hydrated and consider indoor activities.")
        elif temp > 20:
            suggestions.append("Perfect weather for outdoor activities!")
        elif temp > 10:
            suggestions.append("Pleasant weather, but bring a light jacket.")
        elif temp > 0:
            suggestions.append("It's cold! Dress warmly.")
        else:
            suggestions.append("It's freezing! Bundle up and stay warm.")
        
        if "rain" in condition:
            suggestions.append("Don't forget your umbrella!")
        elif "snow" in condition:
            suggestions.append("Snow expected! Drive carefully.")
        elif "cloud" in condition:
            suggestions.append("Cloudy skies today.")
        elif "clear" in condition or "sun" in condition:
            suggestions.append("Clear skies ahead!")
        
        return " ".join(suggestions)

weather_service = WeatherService()