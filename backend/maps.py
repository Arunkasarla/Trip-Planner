"""
maps.py — OpenStreetMap / Nominatim geocoding and attraction lookup
"""
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL  = "https://overpass-api.de/api/interpreter"
HEADERS       = {"User-Agent": "SmartTripPlanner/1.0 (contact@tripplanner.app)"}


def get_map_data(city: str) -> dict:
    """
    Returns geocoordinates, nearby tourist attractions, and hotels
    for a given city using OpenStreetMap data (no API key required).
    """
    try:
        # 1. Geocode the city
        geo = requests.get(
            NOMINATIM_URL,
            params={"q": city, "format": "json", "limit": 1},
            headers=HEADERS,
            timeout=10,
        ).json()

        if not geo:
            return _mock_map(city)

        lat = float(geo[0]["lat"])
        lon = float(geo[0]["lon"])

        # 2. Overpass — tourist attractions + hotels within 15 km
        query = f"""
        [out:json][timeout:15];
        (
          node["tourism"="attraction"](around:15000,{lat},{lon});
          node["tourism"="museum"](around:15000,{lat},{lon});
          node["tourism"="hotel"](around:8000,{lat},{lon});
          node["amenity"="restaurant"](around:5000,{lat},{lon});
        );
        out body 30;
        """
        overpass_res = requests.post(OVERPASS_URL, data=query, headers=HEADERS, timeout=20)
        elements = overpass_res.json().get("elements", []) if overpass_res.status_code == 200 else []

        attractions, hotels = [], []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "").strip()
            if not name:
                continue
            el_lat = el.get("lat", lat)
            el_lon = el.get("lon", lon)
            tourism = tags.get("tourism", "")
            amenity = tags.get("amenity", "")

            if tourism == "hotel":
                hotels.append({"name": name, "lat": el_lat, "lon": el_lon, "type": "hotel"})
            elif amenity == "restaurant":
                attractions.append({"name": name, "lat": el_lat, "lon": el_lon, "type": "restaurant"})
            else:
                attractions.append({"name": name, "lat": el_lat, "lon": el_lon, "type": "attraction"})

        # Ensure we always have some markers
        if not attractions:
            attractions = [
                {"name": f"{city} Heritage Site", "lat": lat + 0.01, "lon": lon + 0.01, "type": "attraction"},
                {"name": f"{city} Scenic Viewpoint", "lat": lat - 0.01, "lon": lon - 0.01, "type": "attraction"},
                {"name": f"{city} Local Market", "lat": lat + 0.02, "lon": lon - 0.02, "type": "attraction"},
            ]
        if not hotels:
            hotels = [
                {"name": f"{city} Grand Hotel", "lat": lat + 0.005, "lon": lon + 0.005, "type": "hotel"},
            ]

        return {
            "city": city,
            "lat": lat,
            "lon": lon,
            "attractions": attractions[:12],
            "hotels": hotels[:6],
        }
    except Exception:
        return _mock_map(city)


def _mock_map(city: str) -> dict:
    return {
        "city": city,
        "lat": 20.5937,
        "lon": 78.9629,
        "attractions": [
            {"name": "Main Attraction", "lat": 20.60, "lon": 78.97, "type": "attraction"},
            {"name": "Heritage Site",   "lat": 20.58, "lon": 78.96, "type": "attraction"},
            {"name": "Local Market",    "lat": 20.59, "lon": 78.98, "type": "attraction"},
        ],
        "hotels": [
            {"name": "Grand Hotel", "lat": 20.595, "lon": 78.965, "type": "hotel"},
        ],
    }
