"""
chatbot.py — Gemini API intent extractor.
Converts free-text user messages into strict intent JSON.
The chatbot NEVER writes itinerary text — only structured intents.
"""
import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are a strict JSON intent extractor for a trip planning app.
Given a user message about modifying a travel itinerary, respond with ONLY a valid JSON object.
NO explanation, NO markdown fences, NO extra text — pure JSON only.

Supported actions:
1. {"action":"remove_activity","activity":"<name>","day":<int or "last">}
2. {"action":"add_activity","activity":"<name>","day":<int or "last">}
3. {"action":"optimize_budget","mode":"low_cost"}
4. {"action":"extend_trip","days_added":<int>}
5. {"action":"shorten_trip","days_removed":<int>}
6. {"action":"change_activity","from":"<old>","to":"<new>","day":<int or "all">}
7. {"action":"change_hotel","preference":"<budget|luxury|family>"}
8. {"action":"add_day","position":"last"}
9. {"action":"unknown","message":"<original message>"}

Rules:
- day can be a number (1,2,3) or the string "last"
- If the message says "last day" use "last"
- Pick the closest matching action
- Return ONLY the JSON object
""".strip()


def extract_intent(user_message: str, current_trip_data: dict) -> dict:
    """
    Primary: Use Gemini 1.5 Flash to parse user message into intent JSON.
    Fallback: Keyword-based rule extraction.
    """
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Current trip destination: {current_trip_data.get('destination', 'Unknown')}, "
                f"{current_trip_data.get('days', 3)} days\n\n"
                f"User message: {user_message}"
            )
            response = model.generate_content(prompt)
            text = response.text.strip()

            # Strip markdown code fences if present
            text = re.sub(r"```(?:json)?", "", text).strip("` \n")

            # Extract JSON object
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                return parsed
        except Exception as e:
            print(f"[Gemini] Error: {e} — falling back to keyword extractor")

    return _keyword_extract(user_message)


def _keyword_extract(message: str) -> dict:
    """Rule-based fallback intent extractor."""
    msg = message.lower()

    # Extract day number
    day: int | str | None = None
    dm = re.search(r"day\s*(\d+)", msg)
    if dm:
        day = int(dm.group(1))
    elif "last" in msg:
        day = "last"

    # Remove / delete
    if any(w in msg for w in ["remove", "delete", "cancel", "skip", "drop"]):
        return {"action": "remove_activity", "activity": _get_activity(msg), "day": day or 1}

    # Add / include
    if any(w in msg for w in ["add", "include", "insert", "put"]):
        if "day" in msg or "more" in msg:
            nums = re.findall(r"\d+", msg)
            n = int(nums[0]) if nums else 1
            return {"action": "extend_trip", "days_added": n}
        return {"action": "add_activity", "activity": _get_activity(msg), "day": day or "last"}

    # Budget / cheaper
    if any(w in msg for w in ["cheap", "cheaper", "budget", "affordable", "reduce cost", "save money", "less expensive"]):
        return {"action": "optimize_budget", "mode": "low_cost"}

    # Extend trip
    if any(w in msg for w in ["extend", "more day", "another day", "extra day", "add one more"]):
        nums = re.findall(r"\d+", msg)
        return {"action": "extend_trip", "days_added": int(nums[0]) if nums else 1}

    # Shorten trip
    if any(w in msg for w in ["shorten", "reduce days", "fewer days", "less days"]):
        nums = re.findall(r"\d+", msg)
        return {"action": "shorten_trip", "days_removed": int(nums[0]) if nums else 1}

    # Replace / change activity
    if any(w in msg for w in ["replace", "change", "swap", "switch", "instead of"]):
        if any(w in msg for w in ["hotel", "accommodation", "stay", "lodge"]):
            mode = "budget" if any(w in msg for w in ["cheap", "budget"]) else "luxury"
            return {"action": "change_hotel", "preference": mode}
        return {"action": "change_activity", "from": _get_activity(msg), "to": _get_activity(msg, second=True), "day": day or "all"}

    # Hotel
    if any(w in msg for w in ["hotel", "accommodation", "stay"]):
        mode = "budget" if any(w in msg for w in ["cheap", "budget"]) else "luxury"
        return {"action": "change_hotel", "preference": mode}

    return {"action": "unknown", "message": message}


_ACTIVITY_KEYWORDS = [
    "beach", "temple", "museum", "nightlife", "shopping", "adventure",
    "trekking", "hiking", "waterfall", "park", "fort", "palace", "restaurant",
    "nature", "wildlife", "safari", "cruise", "snorkeling", "diving",
    "sightseeing", "market", "spa", "yoga", "cooking", "cultural",
]


def _get_activity(msg: str, second: bool = False) -> str:
    found = [a for a in _ACTIVITY_KEYWORDS if a in msg]
    if second and len(found) >= 2:
        return found[1]
    return found[0] if found else "activity"
