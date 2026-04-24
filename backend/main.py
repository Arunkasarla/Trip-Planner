"""
main.py — FastAPI application with all routes
"""
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from database import engine, get_db, Base
import models, schemas
from auth import hash_password, verify_password, create_access_token, get_current_user, get_optional_user
from planner_engine import generate_itinerary, apply_intent
from ml_model import recommend_destination, analyze_sentiment, ensure_models_exist
from chatbot import extract_intent
from weather import get_weather
from maps import get_map_data
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Smart AI Trip Planner API", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ensure_models_exist()
    print("DB tables created. ML models ready.")

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.0/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdnjs.cloudflare.com/ajax/libs/Redoc/2.1.2/redoc.standalone.js",
    )

@app.get("/")
def root():
    return {"status": "ok", "message": "Smart AI Trip Planner API Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/register", response_model=schemas.TokenResponse)
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
    return {"access_token": token, "token_type": "bearer", "user_name": user.name, "user_id": user.id}


@app.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
    return {"access_token": token, "token_type": "bearer", "user_name": user.name, "user_id": user.id}

# ── Trip Generation ───────────────────────────────────────────────────────────
@app.post("/generate-trip")
def generate_trip(data: schemas.TripCreate):
    try:
        # ML: get recommended destination
        destination = recommend_destination(
            budget=data.budget,
            days=data.days,
            interest=data.interests[0] if data.interests else "Beach",
            month=data.month,
            travel_style=data.style,
            travelers=data.travelers,
        )
        # Generate full itinerary
        trip = generate_itinerary(
            destination=destination,
            budget=data.budget,
            days=data.days,
            interests=data.interests,
            travelers=data.travelers,
            month=data.month,
            style=data.style,
        )
        return {"success": True, "data": trip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Chatbot Intent ────────────────────────────────────────────────────────────
@app.post("/chat-intent")
def chat_intent(data: schemas.ChatInput, db: Session = Depends(get_db),
                user=Depends(get_optional_user)):
    intent = extract_intent(data.user_message, data.current_trip_data)
    # Log to DB
    log = models.ChatLog(
        user_id=user["sub"] if user else None,
        message=data.user_message,
        intent_json=intent,
    )
    db.add(log)
    db.commit()
    return {"success": True, "intent": intent}

# ── Update Itinerary ──────────────────────────────────────────────────────────
@app.post("/update-itinerary")
def update_itinerary(data: schemas.UpdateItineraryInput):
    try:
        updated = apply_intent(data.current_trip_data, data.intent_json)
        return {"success": True, "data": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Weather ───────────────────────────────────────────────────────────────────
@app.get("/weather/{city}")
def weather(city: str):
    return get_weather(city)

# ── Map Data ──────────────────────────────────────────────────────────────────
@app.get("/map-data/{city}")
def map_data(city: str):
    return get_map_data(city)

# ── Save Trip ─────────────────────────────────────────────────────────────────
@app.post("/save-trip")
def save_trip(data: schemas.SaveTripInput, db: Session = Depends(get_db),
              user=Depends(get_current_user)):
    trip_data = data.trip_data
    trip = models.Trip(
        user_id=user["sub"],
        destination=trip_data.get("destination", "Unknown"),
        budget=trip_data.get("total_cost", 0),
        days=len(trip_data.get("itinerary", [])),
        trip_json=trip_data,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return {"success": True, "trip_id": trip.id, "message": "Trip saved!"}

# ── Trip History ──────────────────────────────────────────────────────────────
@app.get("/trip-history")
def trip_history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    trips = (db.query(models.Trip)
               .filter(models.Trip.user_id == user["sub"])
               .order_by(models.Trip.created_at.desc())
               .all())
    return {
        "success": True,
        "trips": [
            {"id": t.id, "destination": t.destination, "budget": t.budget,
             "days": t.days, "created_at": str(t.created_at), "trip_json": t.trip_json}
            for t in trips
        ],
    }

# ── Delete Trip ───────────────────────────────────────────────────────────────
@app.delete("/trip/{trip_id}")
def delete_trip(trip_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id, models.Trip.user_id == user["sub"]
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    db.delete(trip)
    db.commit()
    return {"success": True, "message": "Trip deleted"}

# ── Favorites ─────────────────────────────────────────────────────────────────
@app.post("/favorites")
def add_favorite(place_name: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    fav = models.Favorite(user_id=user["sub"], place_name=place_name)
    db.add(fav)
    db.commit()
    return {"success": True}

@app.get("/favorites")
def get_favorites(db: Session = Depends(get_db), user=Depends(get_current_user)):
    favs = db.query(models.Favorite).filter(models.Favorite.user_id == user["sub"]).all()
    return {"success": True, "favorites": [f.place_name for f in favs]}

# ── Sentiment ─────────────────────────────────────────────────────────────────
@app.post("/analyze-review")
def analyze_review(review: str):
    return analyze_sentiment(review)
