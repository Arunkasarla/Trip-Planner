"""
ml_model.py — Two ML models:
  1. RandomForestClassifier  → destination recommendation
  2. LogisticRegression+TF-IDF → sentiment analysis of reviews
"""
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR   = os.path.join(BASE_DIR, "data")

TRIP_MODEL_PATH      = os.path.join(MODELS_DIR, "trip_model.pkl")
SENTIMENT_MODEL_PATH = os.path.join(MODELS_DIR, "sentiment_model.pkl")
VECTORIZER_PATH      = os.path.join(MODELS_DIR, "vectorizer.pkl")
ENCODERS_PATH        = os.path.join(MODELS_DIR, "encoders.pkl")

os.makedirs(MODELS_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Model 1 : Destination Recommendation
# ─────────────────────────────────────────────────────────────────────────────

CATEGORICAL_COLS = ["interest", "month", "travel_style"]
NUMERIC_COLS     = ["budget", "days", "travelers"]
TARGET_COL       = "recommended_place"


def train_recommendation_model():
    """Train RandomForest on trips.csv and persist to disk."""
    csv_path = os.path.join(DATA_DIR, "trips.csv")
    df = pd.read_csv(csv_path)

    encoders = {}
    for col in CATEGORICAL_COLS:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    le_target = LabelEncoder()
    df[TARGET_COL] = le_target.fit_transform(df[TARGET_COL].astype(str))
    encoders[TARGET_COL] = le_target

    X = df[NUMERIC_COLS + CATEGORICAL_COLS].values
    y = df[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"[ML] Recommendation model accuracy: {acc:.2%}")

    joblib.dump(model, TRIP_MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
    return model, encoders


def load_recommendation_model():
    if os.path.exists(TRIP_MODEL_PATH) and os.path.exists(ENCODERS_PATH):
        return joblib.load(TRIP_MODEL_PATH), joblib.load(ENCODERS_PATH)
    return train_recommendation_model()


def recommend_destination(budget: float, days: int, interest: str,
                           month: str, travel_style: str, travelers: int) -> str:
    """Return the top recommended destination for given trip parameters."""
    try:
        model, encoders = load_recommendation_model()

        interest_enc    = _safe_encode(encoders["interest"], interest, CATEGORICAL_COLS[0])
        month_enc       = _safe_encode(encoders["month"], month, CATEGORICAL_COLS[1])
        style_enc       = _safe_encode(encoders["travel_style"], travel_style, CATEGORICAL_COLS[2])

        X = np.array([[budget, days, travelers, interest_enc, month_enc, style_enc]])
        pred = model.predict(X)[0]
        return encoders[TARGET_COL].inverse_transform([pred])[0]
    except Exception as e:
        print(f"[ML] Recommendation error: {e}")
        # Fallback rule-based
        return _rule_based_recommendation(interest, budget, month)


def _safe_encode(le: LabelEncoder, value: str, col: str) -> int:
    """Encode a label; return 0 if unseen."""
    try:
        return int(le.transform([value])[0])
    except ValueError:
        return 0


def _rule_based_recommendation(interest: str, budget: float, month: str) -> str:
    rules = {
        "Beach":     ["Goa", "Andaman", "Goa"],
        "Temple":    ["Varanasi", "Tirupati", "Madurai"],
        "Nature":    ["Manali", "Coorg", "Munnar"],
        "Adventure": ["Rishikesh", "Leh", "Manali"],
        "Shopping":  ["Mumbai", "Delhi", "Jaipur"],
        "Nightlife": ["Goa", "Mumbai", "Bangalore"],
    }
    options = rules.get(interest, ["Goa", "Manali", "Jaipur"])
    idx = 0 if budget < 15000 else (1 if budget < 25000 else 2)
    return options[min(idx, len(options) - 1)]


# ─────────────────────────────────────────────────────────────────────────────
# Model 2 : Sentiment Analysis
# ─────────────────────────────────────────────────────────────────────────────

def train_sentiment_model():
    """Train TF-IDF + Logistic Regression on reviews.csv."""
    csv_path = os.path.join(DATA_DIR, "reviews.csv")
    df = pd.read_csv(csv_path)

    X = df["review_text"].astype(str)
    y = df["label"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_train_v  = vectorizer.fit_transform(X_train)
    X_test_v   = vectorizer.transform(X_test)

    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train_v, y_train)

    acc = accuracy_score(y_test, clf.predict(X_test_v))
    print(f"[ML] Sentiment model accuracy: {acc:.2%}")

    joblib.dump(clf, SENTIMENT_MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    return clf, vectorizer


def load_sentiment_model():
    if os.path.exists(SENTIMENT_MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        return joblib.load(SENTIMENT_MODEL_PATH), joblib.load(VECTORIZER_PATH)
    return train_sentiment_model()


def analyze_sentiment(text: str) -> dict:
    """Return {'label': 'positive'|'negative', 'confidence': float}."""
    try:
        clf, vectorizer = load_sentiment_model()
        X = vectorizer.transform([text])
        label      = clf.predict(X)[0]
        confidence = float(clf.predict_proba(X).max())
        return {"label": label, "confidence": round(confidence, 3)}
    except Exception as e:
        print(f"[ML] Sentiment error: {e}")
        return {"label": "positive", "confidence": 0.5}


# ─────────────────────────────────────────────────────────────────────────────
# Init — called on startup
# ─────────────────────────────────────────────────────────────────────────────

def ensure_models_exist():
    """Train both models if pkl files are missing."""
    if not os.path.exists(TRIP_MODEL_PATH):
        print("[ML] Training recommendation model...")
        train_recommendation_model()
    if not os.path.exists(SENTIMENT_MODEL_PATH):
        print("[ML] Training sentiment model...")
        train_sentiment_model()
    print("[ML] All models ready.")
