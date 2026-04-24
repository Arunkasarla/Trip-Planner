"""
planner_engine.py — Core itinerary generator and updater
"""
import copy, random
from typing import Any

# ── Destination database ─────────────────────────────────────────────────────
DESTINATIONS = {
    "Goa": {
        "tags": ["beach","nightlife","shopping","water sports"],
        "best_months": ["Nov","Dec","Jan","Feb","Mar"],
        "tips": ["Carry sunscreen","Rent a scooter","Try Goan fish curry"],
        "activities": {
            "beach":     [{"name":"Water Sports at Baga Beach","cost_b":800,"cost_l":2000,"duration":"3 hrs"},
                          {"name":"Sunset at Calangute Beach","cost_b":0,"cost_l":0,"duration":"2 hrs"},
                          {"name":"Dolphin Spotting Cruise","cost_b":500,"cost_l":1500,"duration":"3 hrs"}],
            "nightlife": [{"name":"Club Tito's Night Out","cost_b":800,"cost_l":3000,"duration":"4 hrs"},
                          {"name":"Beach Bonfire Party","cost_b":400,"cost_l":1200,"duration":"3 hrs"}],
            "shopping":  [{"name":"Anjuna Flea Market","cost_b":500,"cost_l":2500,"duration":"2.5 hrs"},
                          {"name":"Mapusa Local Market","cost_b":300,"cost_l":800,"duration":"2 hrs"}],
            "adventure": [{"name":"Scuba Diving at Grande Island","cost_b":2000,"cost_l":4000,"duration":"4 hrs"},
                          {"name":"Paragliding at Arambol","cost_b":1500,"cost_l":3000,"duration":"2 hrs"}],
            "nature":    [{"name":"Dudhsagar Falls Trek","cost_b":1000,"cost_l":2500,"duration":"5 hrs"},
                          {"name":"Spice Plantation Tour","cost_b":600,"cost_l":1500,"duration":"3 hrs"}],
        },
        "hotels": {
            "luxury": [{"name":"Taj Exotica Goa","cost_per_night":8000,"rating":4.8}],
            "budget": [{"name":"OYO Beach Retreat","cost_per_night":1200,"rating":3.9}],
            "family": [{"name":"Cidade de Goa Resort","cost_per_night":5000,"rating":4.5}],
            "solo":   [{"name":"The Hostel Crowd Goa","cost_per_night":700,"rating":4.2}],
        },
        "attractions": ["Baga Beach","Fort Aguada","Basilica of Bom Jesus","Dudhsagar Falls","Anjuna Market"],
        "meal_cost": {"budget":300,"luxury":1200,"family":600,"solo":300},
    },
    "Manali": {
        "tags": ["nature","adventure","snow","trekking"],
        "best_months": ["May","Jun","Sep","Oct"],
        "tips": ["Carry warm clothes","Book permits in advance","Try Himachali Dham"],
        "activities": {
            "adventure": [{"name":"Rohtang Pass Snow Drive","cost_b":1500,"cost_l":3500,"duration":"6 hrs"},
                          {"name":"River Rafting on Beas","cost_b":800,"cost_l":2000,"duration":"3 hrs"}],
            "nature":    [{"name":"Solang Valley Cable Car","cost_b":600,"cost_l":1200,"duration":"3 hrs"},
                          {"name":"Jogini Waterfall Trek","cost_b":400,"cost_l":1000,"duration":"4 hrs"}],
            "trekking":  [{"name":"Hampta Pass Trek","cost_b":2500,"cost_l":5000,"duration":"8 hrs"},
                          {"name":"Bhrigu Lake Trek","cost_b":2000,"cost_l":4000,"duration":"7 hrs"}],
            "temple":    [{"name":"Hadimba Devi Temple","cost_b":0,"cost_l":0,"duration":"1.5 hrs"},
                          {"name":"Manu Temple Visit","cost_b":0,"cost_l":0,"duration":"1 hr"}],
            "shopping":  [{"name":"Mall Road Shopping","cost_b":500,"cost_l":3000,"duration":"2 hrs"}],
        },
        "hotels": {
            "luxury": [{"name":"Span Resort & Spa","cost_per_night":7000,"rating":4.7}],
            "budget": [{"name":"Snow Valley Hostel","cost_per_night":800,"rating":4.0}],
            "family": [{"name":"Manali Inn","cost_per_night":3500,"rating":4.3}],
            "solo":   [{"name":"Backpacker Panda","cost_per_night":600,"rating":4.1}],
        },
        "attractions": ["Rohtang Pass","Solang Valley","Hadimba Temple","Old Manali","Beas Kund"],
        "meal_cost": {"budget":200,"luxury":1000,"family":500,"solo":250},
    },
    "Varanasi": {
        "tags": ["temple","spiritual","cultural","heritage"],
        "best_months": ["Oct","Nov","Dec","Jan","Feb"],
        "tips": ["Wake up early for Ganga Aarti","Hire a local guide","Try Banarasi Paan"],
        "activities": {
            "temple":    [{"name":"Kashi Vishwanath Temple","cost_b":0,"cost_l":0,"duration":"2 hrs"},
                          {"name":"Sankat Mochan Hanuman Temple","cost_b":0,"cost_l":0,"duration":"1 hr"}],
            "nature":    [{"name":"Sunrise Boat Ride on Ganges","cost_b":300,"cost_l":800,"duration":"2 hrs"},
                          {"name":"Evening Ganga Aarti at Dashashwamedh Ghat","cost_b":0,"cost_l":0,"duration":"2 hrs"}],
            "cultural":  [{"name":"Sarnath Buddhist Site Tour","cost_b":200,"cost_l":600,"duration":"3 hrs"},
                          {"name":"Varanasi Silk Weaving Workshop","cost_b":300,"cost_l":1000,"duration":"2 hrs"}],
            "shopping":  [{"name":"Vishwanath Gali Shopping","cost_b":500,"cost_l":2000,"duration":"2 hrs"}],
        },
        "hotels": {
            "luxury": [{"name":"BrijRama Palace","cost_per_night":9000,"rating":4.9}],
            "budget": [{"name":"Hotel Alka Varanasi","cost_per_night":1000,"rating":3.8}],
            "family": [{"name":"Radisson Hotel Varanasi","cost_per_night":4500,"rating":4.4}],
            "solo":   [{"name":"Stops Hostel Varanasi","cost_per_night":500,"rating":4.2}],
        },
        "attractions": ["Dashashwamedh Ghat","Kashi Vishwanath","Sarnath","Assi Ghat","Ramnagar Fort"],
        "meal_cost": {"budget":200,"luxury":800,"family":400,"solo":200},
    },
    "Andaman": {
        "tags": ["beach","snorkeling","island","water sports"],
        "best_months": ["Nov","Dec","Jan","Feb","Mar"],
        "tips": ["Book permits early","Carry reef-safe sunscreen","Try fresh seafood"],
        "activities": {
            "beach":     [{"name":"Radhanagar Beach Sunset","cost_b":0,"cost_l":0,"duration":"3 hrs"},
                          {"name":"Elephant Beach Snorkeling","cost_b":800,"cost_l":2000,"duration":"4 hrs"}],
            "adventure": [{"name":"Scuba Diving at Neil Island","cost_b":3000,"cost_l":6000,"duration":"5 hrs"},
                          {"name":"Sea Walking at Corbyn Cove","cost_b":2500,"cost_l":4000,"duration":"3 hrs"}],
            "nature":    [{"name":"Cellular Jail Night Show","cost_b":150,"cost_l":500,"duration":"2 hrs"},
                          {"name":"Mangrove Creek Kayaking","cost_b":1000,"cost_l":2500,"duration":"3 hrs"}],
        },
        "hotels": {
            "luxury": [{"name":"Taj Exotica Andaman","cost_per_night":12000,"rating":4.8}],
            "budget": [{"name":"Symphony Palms Beach Resort","cost_per_night":2500,"rating":4.0}],
            "family": [{"name":"SeaShell Port Blair","cost_per_night":5000,"rating":4.4}],
            "solo":   [{"name":"Driftwood Hostel","cost_per_night":800,"rating":4.3}],
        },
        "attractions": ["Radhanagar Beach","Cellular Jail","Havelock Island","Neil Island","Baratang"],
        "meal_cost": {"budget":400,"luxury":1500,"family":700,"solo":400},
    },
    "Rishikesh": {
        "tags": ["adventure","yoga","rafting","spiritual"],
        "best_months": ["Mar","Apr","Sep","Oct","Nov"],
        "tips": ["Best rafting Mar-May","No meat near ghats","Try Ayurvedic massage"],
        "activities": {
            "adventure": [{"name":"White Water River Rafting","cost_b":600,"cost_l":2000,"duration":"4 hrs"},
                          {"name":"Bungee Jumping at Mohan Chatti","cost_b":3000,"cost_l":3500,"duration":"2 hrs"}],
            "nature":    [{"name":"Neer Garh Waterfall Trek","cost_b":200,"cost_l":600,"duration":"3 hrs"},
                          {"name":"Rajaji National Park Safari","cost_b":800,"cost_l":2000,"duration":"4 hrs"}],
            "temple":    [{"name":"Triveni Ghat Aarti","cost_b":0,"cost_l":0,"duration":"2 hrs"},
                          {"name":"Neelkanth Mahadev Temple","cost_b":0,"cost_l":0,"duration":"2 hrs"}],
            "yoga":      [{"name":"Sunrise Yoga at Parmarth Niketan","cost_b":200,"cost_l":500,"duration":"2 hrs"}],
        },
        "hotels": {
            "luxury": [{"name":"Aloha on the Ganges","cost_per_night":6000,"rating":4.7}],
            "budget": [{"name":"Zostel Rishikesh","cost_per_night":600,"rating":4.3}],
            "family": [{"name":"Ganga Kinare","cost_per_night":4000,"rating":4.5}],
            "solo":   [{"name":"Bunk Rishikesh","cost_per_night":500,"rating":4.2}],
        },
        "attractions": ["Laxman Jhula","Triveni Ghat","Beatles Ashram","Neelkanth Temple","Neer Garh Waterfall"],
        "meal_cost": {"budget":200,"luxury":800,"family":400,"solo":200},
    },
    "Jaipur": {
        "tags": ["heritage","shopping","culture","royal"],
        "best_months": ["Oct","Nov","Dec","Jan","Feb"],
        "tips": ["Hire auto-rickshaw for local trips","Bargain at markets","Try Dal Baati Churma"],
        "activities": {
            "shopping":  [{"name":"Johari Bazaar Gem Shopping","cost_b":1000,"cost_l":10000,"duration":"3 hrs"},
                          {"name":"Bapu Bazaar Handicrafts","cost_b":500,"cost_l":3000,"duration":"2 hrs"}],
            "adventure": [{"name":"Hot Air Balloon Ride","cost_b":8000,"cost_l":15000,"duration":"2 hrs"},
                          {"name":"Camel Safari at Sambhar","cost_b":600,"cost_l":2000,"duration":"3 hrs"}],
            "temple":    [{"name":"Birla Mandir Temple","cost_b":0,"cost_l":0,"duration":"1 hr"},
                          {"name":"Govind Dev Ji Temple","cost_b":0,"cost_l":0,"duration":"1 hr"}],
            "nature":    [{"name":"Amber Fort & Light Show","cost_b":300,"cost_l":800,"duration":"3 hrs"},
                          {"name":"Jal Mahal Sunset View","cost_b":100,"cost_l":300,"duration":"1.5 hrs"}],
        },
        "hotels": {
            "luxury": [{"name":"Rambagh Palace","cost_per_night":15000,"rating":4.9}],
            "budget": [{"name":"Hotel Pearl Palace","cost_per_night":1200,"rating":4.4}],
            "family": [{"name":"ITC Rajputana","cost_per_night":7000,"rating":4.6}],
            "solo":   [{"name":"Moustache Hostel Jaipur","cost_per_night":700,"rating":4.4}],
        },
        "attractions": ["Amber Fort","Hawa Mahal","City Palace","Jantar Mantar","Nahargarh Fort"],
        "meal_cost": {"budget":250,"luxury":1200,"family":600,"solo":250},
    },
    "Munnar": {
        "tags": ["nature","tea gardens","trekking","wildlife"],
        "best_months": ["Sep","Oct","Nov","Dec","Jan","Feb"],
        "tips": ["Carry light woolens","Best at sunrise","Try Kerala Sadya"],
        "activities": {
            "nature":    [{"name":"Eravikulam National Park","cost_b":100,"cost_l":300,"duration":"3 hrs"},
                          {"name":"Tea Museum Munnar","cost_b":100,"cost_l":200,"duration":"2 hrs"}],
            "adventure": [{"name":"Anamudi Peak Trek","cost_b":500,"cost_l":1500,"duration":"6 hrs"},
                          {"name":"Attukal Waterfalls Visit","cost_b":200,"cost_l":500,"duration":"2 hrs"}],
            "trekking":  [{"name":"Chokramudi Peak Sunrise Trek","cost_b":600,"cost_l":1500,"duration":"5 hrs"}],
            "wildlife":  [{"name":"Chinnar Wildlife Sanctuary","cost_b":300,"cost_l":800,"duration":"4 hrs"}],
        },
        "hotels": {
            "luxury": [{"name":"Windermere Estate","cost_per_night":6000,"rating":4.7}],
            "budget": [{"name":"Green View Munnar","cost_per_night":1000,"rating":4.0}],
            "family": [{"name":"Tea County Resort","cost_per_night":4000,"rating":4.5}],
            "solo":   [{"name":"Jungle Hut","cost_per_night":700,"rating":4.1}],
        },
        "attractions": ["Eravikulam National Park","Mattupetty Dam","Echo Point","Tea Gardens","Attukal Waterfall"],
        "meal_cost": {"budget":200,"luxury":800,"family":450,"solo":200},
    },
    "Delhi": {
        "tags": ["heritage","shopping","food","culture"],
        "best_months": ["Oct","Nov","Dec","Jan","Feb","Mar"],
        "tips": ["Use Delhi Metro","Book monuments online","Try street food in Chandni Chowk"],
        "activities": {
            "shopping":  [{"name":"Chandni Chowk Street Market","cost_b":500,"cost_l":3000,"duration":"3 hrs"},
                          {"name":"Sarojini Nagar Market","cost_b":500,"cost_l":1000,"duration":"2 hrs"}],
            "temple":    [{"name":"Akshardham Temple","cost_b":170,"cost_l":500,"duration":"4 hrs"},
                          {"name":"Lotus Temple","cost_b":0,"cost_l":0,"duration":"1.5 hrs"}],
            "nature":    [{"name":"Qutub Minar & Gardens","cost_b":30,"cost_l":100,"duration":"2 hrs"},
                          {"name":"India Gate Evening Walk","cost_b":0,"cost_l":0,"duration":"2 hrs"}],
            "cultural":  [{"name":"Red Fort Tour","cost_b":35,"cost_l":100,"duration":"2.5 hrs"},
                          {"name":"Humayun's Tomb","cost_b":35,"cost_l":100,"duration":"2 hrs"}],
        },
        "hotels": {
            "luxury": [{"name":"The Imperial New Delhi","cost_per_night":12000,"rating":4.8}],
            "budget": [{"name":"Zostel Delhi","cost_per_night":700,"rating":4.2}],
            "family": [{"name":"Radisson Blu New Delhi","cost_per_night":5500,"rating":4.5}],
            "solo":   [{"name":"Moustache Delhi","cost_per_night":600,"rating":4.3}],
        },
        "attractions": ["Red Fort","Qutub Minar","India Gate","Akshardham","Humayun's Tomb"],
        "meal_cost": {"budget":250,"luxury":1200,"family":600,"solo":300},
    },
}

FALLBACK_DESTINATION = "Goa"

TIME_SLOTS = ["Morning", "Afternoon", "Evening", "Night"]
MEALS = {
    "Morning":   {"activity": "Breakfast", "place": "Hotel Restaurant"},
    "Afternoon": {"activity": "Lunch",     "place": "Local Restaurant"},
    "Night":     {"activity": "Dinner",    "place": "Local Cuisine Spot"},
}


def _style_key(style: str) -> str:
    s = style.lower()
    if "luxury" in s: return "luxury"
    if "family" in s: return "family"
    if "solo"   in s: return "solo"
    return "budget"


def _cost_key(style: str) -> str:
    return "cost_l" if _style_key(style) == "luxury" else "cost_b"


def generate_itinerary(destination: str, budget: float, days: int,
                        interests: list, travelers: int, month: str,
                        style: str = "budget") -> dict:
    """Generate a complete day-wise trip itinerary."""
    dest = DESTINATIONS.get(destination, DESTINATIONS[FALLBACK_DESTINATION])
    sk   = _style_key(style)
    ck   = _cost_key(style)

    hotel = dest["hotels"].get(sk, dest["hotels"]["budget"])[0]
    per_night = hotel["cost_per_night"]
    meal_cost = dest["meal_cost"].get(sk, 300)

    # Build activity pool from interests
    activity_pool: list = []
    for interest in interests:
        key = interest.lower()
        acts = dest["activities"].get(key, [])
        activity_pool.extend(acts)

    # Fallback: use all activities
    if not activity_pool:
        for acts in dest["activities"].values():
            activity_pool.extend(acts)

    used = set()
    itinerary = []
    total_cost = per_night * days

    for day_num in range(1, days + 1):
        slots = []
        day_cost = per_night + meal_cost * 3

        # Pick 2 unique activities per day
        day_acts = []
        for act in activity_pool:
            if act["name"] not in used and len(day_acts) < 2:
                day_acts.append(act)
                used.add(act["name"])

        # If we ran out, reshuffle
        if len(day_acts) < 2:
            used.clear()
            random.shuffle(activity_pool)
            for act in activity_pool:
                if act["name"] not in used and len(day_acts) < 2:
                    day_acts.append(act)
                    used.add(act["name"])

        slot_times = ["Morning", "Afternoon", "Evening"]
        if day_num == 1:
            slots.append({"time": "Morning", "activity": "Check-in & Rest",
                          "place": hotel["name"], "cost": 0, "duration": "1 hr",
                          "notes": "Settle in and freshen up"})
            slot_times = ["Afternoon", "Evening"]

        for i, act in enumerate(day_acts[:len(slot_times)]):
            cost = act[ck] * travelers
            slots.append({
                "time": slot_times[i],
                "activity": act["name"],
                "place": destination,
                "cost": cost,
                "duration": act["duration"],
                "notes": f"Recommended for {style} travelers",
            })
            day_cost += cost

        # Meals
        slots.append({"time": "Night", "activity": "Dinner",
                       "place": f"Local {destination} Restaurant",
                       "cost": meal_cost * travelers, "duration": "1.5 hrs",
                       "notes": "Try local cuisine"})

        theme = interests[0].title() if interests else "Sightseeing"
        itinerary.append({
            "day": day_num,
            "theme": f"Day {day_num} – {theme} & Exploration",
            "slots": slots,
            "day_cost": round(day_cost),
            "notes": f"Enjoy {destination}!",
        })
        total_cost += day_cost

    return {
        "destination": destination,
        "total_cost": round(total_cost),
        "daily_budget": round(total_cost / days),
        "hotels": [hotel],
        "attractions": dest["attractions"],
        "itinerary": itinerary,
        "weather_summary": f"Best visited in {', '.join(dest['best_months'][:3])}",
        "tips": dest["tips"],
    }


# ── Intent Handlers ──────────────────────────────────────────────────────────

def apply_intent(current_trip: dict, intent: dict) -> dict:
    """Route intent to the correct handler and return updated trip."""
    trip = copy.deepcopy(current_trip)
    action = intent.get("action", "unknown")

    handlers = {
        "remove_activity":  _handle_remove,
        "add_activity":     _handle_add,
        "optimize_budget":  _handle_budget,
        "extend_trip":      _handle_extend,
        "shorten_trip":     _handle_shorten,
        "change_activity":  _handle_change,
        "change_hotel":     _handle_hotel,
        "add_day":          _handle_extend,
    }

    handler = handlers.get(action)
    if handler:
        trip = handler(trip, intent)
    return trip


def _resolve_day(trip: dict, day_val) -> int | None:
    days = trip.get("itinerary", [])
    if day_val == "last": return days[-1]["day"] if days else None
    try: return int(day_val)
    except: return None


def _handle_remove(trip: dict, intent: dict) -> dict:
    day_num = _resolve_day(trip, intent.get("day", 1))
    activity = (intent.get("activity") or "").lower()
    for day in trip["itinerary"]:
        if day["day"] == day_num:
            day["slots"] = [s for s in day["slots"]
                            if activity not in s["activity"].lower()]
            day["day_cost"] = sum(s["cost"] for s in day["slots"])
    trip["total_cost"] = sum(d["day_cost"] for d in trip["itinerary"])
    return trip


def _handle_add(trip: dict, intent: dict) -> dict:
    day_num  = _resolve_day(trip, intent.get("day", "last"))
    activity = intent.get("activity", "sightseeing")
    dest     = trip.get("destination", FALLBACK_DESTINATION)
    dest_data = DESTINATIONS.get(dest, DESTINATIONS[FALLBACK_DESTINATION])

    new_slot = {"time": "Evening", "activity": f"{activity.title()} Experience",
                "place": dest, "cost": 500, "duration": "2 hrs",
                "notes": f"Added {activity} activity"}

    # Try to find a matching activity in DB
    for key, acts in dest_data["activities"].items():
        if activity.lower() in key or any(activity.lower() in a["name"].lower() for a in acts):
            a = acts[0]
            new_slot.update({"activity": a["name"], "cost": a["cost_b"], "duration": a["duration"]})
            break

    for day in trip["itinerary"]:
        if day["day"] == day_num:
            day["slots"].append(new_slot)
            day["day_cost"] += new_slot["cost"]
    trip["total_cost"] = sum(d["day_cost"] for d in trip["itinerary"])
    return trip


def _handle_budget(trip: dict, intent: dict) -> dict:
    """Reduce costs by 30% across all slots."""
    for day in trip["itinerary"]:
        for slot in day["slots"]:
            slot["cost"] = round(slot["cost"] * 0.7)
        day["day_cost"] = sum(s["cost"] for s in day["slots"])
    trip["total_cost"] = sum(d["day_cost"] for d in trip["itinerary"])
    if trip.get("hotels"):
        trip["hotels"][0]["cost_per_night"] = round(trip["hotels"][0]["cost_per_night"] * 0.6)
    return trip


def _handle_extend(trip: dict, intent: dict) -> dict:
    days_added = int(intent.get("days_added", 1))
    dest = trip.get("destination", FALLBACK_DESTINATION)
    dest_data = DESTINATIONS.get(dest, DESTINATIONS[FALLBACK_DESTINATION])
    existing_days = len(trip.get("itinerary", []))
    acts = list(dest_data["activities"].values())
    all_acts = [a for sublist in acts for a in sublist]
    random.shuffle(all_acts)

    for i in range(days_added):
        day_num = existing_days + i + 1
        act = all_acts[i % len(all_acts)]
        new_day = {
            "day": day_num,
            "theme": f"Day {day_num} – Extended Exploration",
            "slots": [
                {"time": "Morning", "activity": act["name"], "place": dest,
                 "cost": act["cost_b"], "duration": act["duration"], "notes": "Extra day activity"},
                {"time": "Evening", "activity": "Leisure & Shopping", "place": dest,
                 "cost": 500, "duration": "2 hrs", "notes": "Relax and explore"},
                {"time": "Night", "activity": "Dinner", "place": "Local Restaurant",
                 "cost": 400, "duration": "1.5 hrs", "notes": "Local cuisine"},
            ],
            "day_cost": act["cost_b"] + 900,
            "notes": "Newly added day",
        }
        trip["itinerary"].append(new_day)
        trip["total_cost"] += new_day["day_cost"]
    return trip


def _handle_shorten(trip: dict, intent: dict) -> dict:
    days_removed = int(intent.get("days_removed", 1))
    trip["itinerary"] = trip["itinerary"][:-days_removed]
    trip["total_cost"] = sum(d["day_cost"] for d in trip["itinerary"])
    return trip


def _handle_change(trip: dict, intent: dict) -> dict:
    day_num  = _resolve_day(trip, intent.get("day", "all"))
    from_act = (intent.get("from") or "").lower()
    to_act   = (intent.get("to")   or "activity").lower()
    for day in trip["itinerary"]:
        if day_num is None or day["day"] == day_num or day_num == "all":
            for slot in day["slots"]:
                if from_act in slot["activity"].lower():
                    slot["activity"] = f"{to_act.title()} Experience"
                    slot["notes"] = f"Changed from {from_act} to {to_act}"
    return trip


def _handle_hotel(trip: dict, intent: dict) -> dict:
    pref = intent.get("preference", "budget")
    dest = trip.get("destination", FALLBACK_DESTINATION)
    dest_data = DESTINATIONS.get(dest, DESTINATIONS[FALLBACK_DESTINATION])
    new_hotel = dest_data["hotels"].get(pref, dest_data["hotels"]["budget"])[0]
    trip["hotels"] = [new_hotel]
    # Recalculate: swap old hotel cost
    old_per_night = trip.get("hotels", [{}])[0].get("cost_per_night", 2000)
    diff = (new_hotel["cost_per_night"] - old_per_night) * len(trip["itinerary"])
    trip["total_cost"] = max(0, trip["total_cost"] + diff)
    return trip
