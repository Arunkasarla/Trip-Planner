"""
schemas.py — Pydantic request/response models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    user_id: str


# ─── Trip ─────────────────────────────────────────────────────────────────────

class TripCreate(BaseModel):
    budget: float
    days: int
    interests: List[str]
    month: str
    travelers: int
    style: str
    starting_location: Optional[str] = "India"

class SlotItem(BaseModel):
    time: str
    activity: str
    place: str
    cost: float
    duration: str
    notes: str

class DayPlan(BaseModel):
    day: int
    theme: str
    slots: List[Dict[str, Any]]
    day_cost: float
    notes: str

class HotelItem(BaseModel):
    name: str
    cost_per_night: float
    rating: float
    style: str

class TripResponse(BaseModel):
    destination: str
    total_cost: float
    daily_budget: float
    hotels: List[Dict[str, Any]]
    attractions: List[str]
    itinerary: List[Dict[str, Any]]
    weather_summary: Optional[str] = None
    tips: List[str]


# ─── Chatbot ──────────────────────────────────────────────────────────────────

class ChatInput(BaseModel):
    user_message: str
    current_trip_data: Dict[str, Any]

class UpdateItineraryInput(BaseModel):
    intent_json: Dict[str, Any]
    current_trip_data: Dict[str, Any]


# ─── Save / History ───────────────────────────────────────────────────────────

class SaveTripInput(BaseModel):
    trip_data: Dict[str, Any]
    user_id: Optional[str] = None

class TripHistoryItem(BaseModel):
    id: str
    destination: str
    budget: float
    days: int
    created_at: str


# ─── Weather ──────────────────────────────────────────────────────────────────

class ForecastItem(BaseModel):
    date: str
    temp: float
    condition: str
    rain_chance: int

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    feels_like: float
    humidity: int
    condition: str
    wind_speed: float
    forecast: List[Dict[str, Any]]


# ─── Maps ─────────────────────────────────────────────────────────────────────

class MapDataResponse(BaseModel):
    city: str
    lat: float
    lon: float
    attractions: List[Dict[str, Any]]
    hotels: List[Dict[str, Any]]
