# 🌍 Smart AI Trip Planner

A production-ready, full-stack web application that uses Machine Learning to recommend personalized travel destinations and Generative AI to allow users to interactively edit and customize their itineraries through a chat interface.

---

## 🚀 Features
- **AI Destination Recommender:** Suggests the best destination based on user budget, travel style, interests, and season.
- **Interactive AI Chatbot:** Uses Google Gemini to understand natural language requests (e.g., "Add an extra day", "Make it cheaper") and dynamically updates the itinerary without writing raw text.
- **Live Maps Integration:** Interactive destination maps using Leaflet.js with plotted hotels and attractions.
- **Live Weather Integration:** Real-time weather and 5-day forecasts via OpenWeatherMap.
- **Secure Authentication:** JWT-based user login, registration, and password hashing (bcrypt).
- **User Dashboard:** Save trips to a PostgreSQL database, view travel statistics, and export itineraries as beautifully formatted PDFs.
- **Premium UI:** Glassmorphism design, dark/light mode toggle, and fully responsive layouts.

---

## 🛠️ Technology Stack
### Frontend
* **HTML5 / CSS3 / Vanilla JavaScript**
* **Leaflet.js:** Interactive Maps
* **jsPDF:** Client-side PDF generation

### Backend
* **Python 3.11**
* **FastAPI:** High-performance API framework
* **PostgreSQL & SQLAlchemy:** Relational database and ORM
* **Uvicorn:** ASGI Web Server
* **PyJWT & Bcrypt:** Security and Authentication

### AI & Machine Learning
* **Scikit-Learn:** Core ML library
* **Google Gemini 1.5 Flash:** Generative AI for Intent Parsing
* **Pandas & NumPy:** Data processing

---

## 🧠 How the AI & ML Models Work

This project employs three distinct AI systems working in harmony:

### 1. Destination Recommendation (Random Forest)
* **Type:** Supervised Machine Learning (`sklearn.ensemble.RandomForestClassifier`)
* **How it works:** When a user submits their preferences (budget, days, interests, travel style), the model analyzes historical trip data (`data/trips.csv`) using multiple decision trees. It calculates the statistical probability of which destination historically matches those specific inputs best and outputs the ideal location.

### 2. Review Sentiment Analysis (Logistic Regression)
* **Type:** Natural Language Processing (`sklearn.linear_model.LogisticRegression` + `TfidfVectorizer`)
* **How it works:** It processes textual reviews (`data/reviews.csv`) by converting English words into numerical weights (TF-IDF). It then uses a mathematical boundary line to classify whether a review is Positive or Negative. This helps rank hotels and attractions.

### 3. AI Chatbot Intent Parser (Google Gemini)
* **Type:** Large Language Model (Generative AI)
* **How it works:** To ensure the AI doesn't "hallucinate" fake places or break the itinerary budget, Gemini is strictly instructed **not** to write the itinerary. Instead, it reads the user's chat message (e.g., "Remove the beach on day 2") and outputs a highly structured **JSON Intent** (e.g., `{"action": "remove_activity", "day": 2, "target": "beach"}`). 
* The Python backend receives this JSON and executes the logic safely, ensuring total control over the data.

---

## 🏗️ System Architecture Flow
1. **User Input:** User fills out the planning form on the Frontend.
2. **Prediction:** Backend passes data to the ML `RandomForest` model.
3. **Generation:** `planner_engine.py` constructs a structured JSON itinerary within the budget constraints.
4. **Data Fetching:** Backend calls external APIs (OpenWeatherMap & Nominatim Maps).
5. **Modification:** User chats with the floating bot ➔ Gemini parses Intent ➔ Backend re-calculates the trip ➔ Frontend updates live.
6. **Storage:** User clicks "Save Trip", storing the structured JSON into the PostgreSQL database.

---

## 💻 Local Setup & Installation

### Prerequisites
* Python 3.10+
* PostgreSQL Database (Local or Cloud like Neon/Render)
* Google Gemini API Key
* OpenWeatherMap API Key

### 1. Clone the repository
```bash
git clone https://github.com/Arunkasarla/Trip-Planner.git
cd Trip-Planner
```

### 2. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a `.env` file in the root directory and add your keys:
```env
DATABASE_URL=postgresql://user:password@localhost/trip_planner
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
SECRET_KEY=super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 🏃‍♂️ Run Commands

### Start the Backend (FastAPI)
Run this from the `backend/` directory:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
* Note: On the very first run, the backend will automatically train the ML models using the CSV files and create the `.pkl` files.
* API Documentation (Swagger) will be available at: `http://127.0.0.1:8000/docs`

### Start the Frontend (UI)
Open a new terminal window and run this from the `frontend/` directory:
```bash
cd frontend
python -m http.server 8080
```
* Open your browser and navigate to: `http://localhost:8080/index.html`

---

## 📝 Future Enhancements (Production Ready)
- **Vector Database (RAG):** Integrate `pgvector` to allow the AI to read thousands of live travel blogs before making recommendations.
- **Deep Learning (Two-Tower Model):** Upgrade the destination recommender to a personalized neural network similar to Airbnb's recommendation engine.
- **TSP Routing (Operations Research):** Integrate Google OR-Tools to mathematically optimize the daily route, minimizing travel time between attractions.
