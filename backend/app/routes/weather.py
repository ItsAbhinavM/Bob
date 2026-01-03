from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import WeatherResponse
from app.services.weather_services import weather_service

router = APIRouter()

@router.get("/", response_model=WeatherResponse)
async def get_weather(location: str = Query(..., description="City name or location")):
    """Get current weather information for a location"""
    weather_data = await weather_service.get_weather(location)
    
    if "error" in weather_data and weather_data.get("error"):
        raise HTTPException(
            status_code=404 if "not found" in weather_data["error"].lower() else 500,
            detail=weather_data["error"]
        )
    
    return weather_data