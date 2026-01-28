# GridironGPT

Status: In development

GridironGPT is an AI-powered fantasy football assistant. It syncs Sleeper league data and SportsDataIO projections into a local SQLite cache, exposes clean FastAPI endpoints, and formats insights through an AI layer. A React + Vite frontend provides the chat-style UI.

## Features
- Sleeper league sync (league, users, rosters, matchups, players)
- SportsDataIO projections and weekly actuals support
- SQLite cache with reusable query helpers and WAL mode
- FastAPI API with dedicated routers for players, rosters, users, DST, and AI insights
- CLI sync tools for players, leagues, matchups, projections, and actuals
- React + Vite frontend with Tailwind

## Tech stack
- Backend: Python, FastAPI, Uvicorn
- Frontend: React, Vite, Tailwind
- Storage: SQLite
- External APIs: Sleeper, SportsDataIO
- AI: OpenAI API (optional, configured via env)

## 🗂 Project Structure
```
GridironGPT/
├── assets/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── routers/
│   │   │   ├── admin.py
│   │   │   ├── advice.py
│   │   │   ├── deps.py
│   │   │   ├── dst.py
│   │   │   ├── health.py
│   │   │   ├── players.py
│   │   │   ├── rosters.py
│   │   │   └── users.py
│   │   ├── services/
│   │   ├── utils/
│   │   ├── config.py
│   │   └── main.py
│   ├── queries/
│   ├── tests/
│   ├── cache_manager.py
│   ├── data_client.py
│   ├── db.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── schema.sql
│   └── sync.py
├── data/
├── frontend/
│   ├── public/
│   └── src/
│       ├── assets/
│       ├── images/
│       ├── App.css
│       ├── App.jsx
│       ├── HomePage.jsx
│       ├── index.css
│       └── main.jsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── nginx/
├── scripts/
├── .env
├── .env.example
├── .gitignore
├── AGENTS.md
├── docker-compose.yml
└── README.md
```

## Getting started

### Prerequisites
- Python 3.x
- Node.js + npm

### Environment variables
Copy `.env.example` to `.env` at the repo root and fill in values.

Example:
```
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ALLOWED_ORIGINS=http://localhost:5173

# Data
DB_PATH=./data/gridiron.db
SLEEPER_BASE=https://api.sleeper.app/v1
SLEEPER_LEAGUE_ID=YOUR_LEAGUE_ID
SPORTS_DATA_KEY=YOUR_SPORTS_DATA_KEY
SPORTS_DATA_BASE=https://api.sportsdata.io/v3/nfl

# AI (optional)
OPENAI_API_KEY=sk-...
```

### Backend (FastAPI)
```
python -m venv .venv
. .venv/Scripts/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

### Frontend (React)
```
cd frontend
npm install
npm run dev
```

## Data sync CLI
The sync script lives at `backend/sync.py`.

Examples:
```
python backend/sync.py players
python backend/sync.py league YOUR_LEAGUE_ID
python backend/sync.py matchups YOUR_LEAGUE_ID 1
python backend/sync.py week-meta 2024 1
python backend/sync.py week-actuals 2024 1
python backend/sync.py inspect --league YOUR_LEAGUE_ID
```

## API quick reference
- `GET /` Welcome message
- `GET /health` Health check
- `GET /players` List players
- `GET /players/search` Search players
- `GET /players/{player_id}` Player detail
- `GET /players/{player_id}/projection` Player weekly projection
- `GET /players/search/projection` Search projections by name
- `GET /rosters/league` League rosters
- `GET /rosters/owner` Roster by owner name
- `GET /users` League users
- `GET /users/lookup` User lookup
- `GET /dst/weekly` Weekly DST projections/actuals
- `GET /dst/season-ranks` Season DST ranks
- `POST /ai/compare-rosters`
- `POST /ai/start-sit`
- `POST /ai/fantasy-leaders`
- `POST /ai/league-summary`
- `POST /ai/roster-insights`
- `POST /admin/league` Switch active league

## Docker
Build and run the full stack (backend, frontend, nginx):
```
docker compose up --build
```

## Tests
```
pytest
```

## Notes
- The backend reads env files from the repo root and `backend/.env`.
- SQLite data is stored under `data/` by default.
```
