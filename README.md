# GridironGPT — AI Fantasy Football Assistant

**GridironGPT** is an AI-powered fantasy football assistant that combines real **statistical data**, **Sleeper API league syncing**, and **OpenAI** formatting to generate clear, conversational fantasy insights.

The backend fetches league, roster, player, and matchup data from the Sleeper API & SportsDataIO API, caches it locally in **SQLite**, and exposes it through a lightweight **FastAPI** service.
The frontend (React + Tailwind) will provide an interactive chat interface powered by the OpenAI Mini Model for natural, easy-to-read analysis.

## 🚀 Core Features (Current & In-Progress)
### ✔️ Local Sleeper Data Caching (Phase 1)

Pulls league, roster, matchup, and player data from the Sleeper API

Stores all data locally in SQLite using a clean schema

Uses a meta table for:

active league tracking

last sync timestamps (TTLs)

Supports fast reads and offline-friendly performance

### ✔️ Flexible DB Layer

Custom db.py built with:

WAL mode

foreign key enforcement

reusable query helpers (fetch_all, fetch_one, execute, executemany)

metadata persistence

Prepped for future projections + analytics

### 🔜 AI Layer (Phase 3)

Backend computes raw insights

OpenAI Mini model reformats results into:

start/sit advice

matchup breakdowns

weekly ranking explanations

### 🔜 Smart Chat UI (Phase 4)

React UI optimized for:

quick queries

matchup lookups

weekly roster decisions

---

## 🧠 Tech Stack
| **Layer**      | **Technology**            | **Purpose**                                      |
|----------------|---------------------------|--------------------------------------------------|
| Frontend       | React + Vite + Tailwind   | Chat interface + user input                      |
| Backend        | FastAPI (Python)          | Syncs data, exposes endpoints, AI formatting     |
| Database       | SQLite                    | Local cache of Sleeper API data                  |
| External API   | Sleeper API               | Provides league, roster, matchup & player info   |
| AI             | OpenAI Mini Model         | Conversational formatting of backend output      |

---

## 🗂️ Project Structure
```
GridironGPT/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   └── models/
│   ├── Dockerfile
│   └── requirements.txt
│
├── data/
│   ├── schema.py
│   ├── gridiron_db.py
│   ├── data_client.py
│   ├── db.py
│   ├── sync.py
│   └── cache_manager.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.jsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   └── db_tests/
│
├── assets/
├── .env
├── .env.example
├── docker-compose.yml
├── .gitignore
└── README.md
```
---

## ⚙️ Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/taisewell/GridironGPT.git
cd GridironGPT
```
### 2️⃣ Backend Setup (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
### 3️⃣ Frontend Setup (React)
```bash
cd frontend
npm install
npm run dev
```

### 🔑 Environment Variables
Create a .env file inside backend/:
```bash
OPENAI_API_KEY=your_api_key_here
DB_PATH=./data/gridiron.db
SLEEPER_LEAGUE_ID=your_default_league_id   # optional
```

## 🗺️ Roadmap
Phase 0 – Setup ✔️
Repo initialized

Project structure created

Requirements + environment configured

Phase 1 – Data Layer (Current)
✔️ SQLite schema

✔️ db.py data access layer

⏳ Sleeper client

⏳ Sync pipeline (players, rosters, matchups)

Phase 2 – Backend Logic
Compute matchup advantages

Weekly player ranking logic

Start/Sit comparison processing

Phase 3 – AI Integration
Format backend outputs using OpenAI Mini

Efficient prompt generation

Chat-style conversational formatting

Phase 4 – React Chat Interface
Chat panel

Query input

Response formatting

Display synced roster + matchups

Phase 5 – Deployment
Vercel for frontend

Render / AWS for backend

Phase 6 – Polish
UI design improvements

Animations

Documentation cleanup

🔮 Future Enhancements
User-selectable Sleeper league

Multi-league caching

Live injury & projection data

Player comparison charts

Weekly fantasy projections

Performance metrics by roster slot

Developed by Tai Sewell

“Where stats meet strategy.”

