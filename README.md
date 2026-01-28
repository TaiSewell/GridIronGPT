# GridironGPT - AI Fantasy Football Assistant

GridironGPT is an AI-powered fantasy football assistant that combines statistical data, Sleeper league syncing, and OpenAI formatting to generate clear, conversational fantasy insights.

The backend syncs league, roster, player, and matchup data from Sleeper and SportsDataIO, caches it in SQLite, and exposes it through a FastAPI service. The React frontend provides an interactive chat interface for natural, easy-to-read analysis.

## Tech stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | React + Vite + Tailwind | Chat interface and user input |
| Backend | FastAPI (Python) | Data sync, API endpoints, AI formatting |
| Database | SQLite | Local cache of Sleeper data |
| External APIs | Sleeper API, SportsDataIO API | League, roster, matchup, player data |
| AI | OpenAI Mini Model | Conversational formatting |

## Project structure

```
GridironGPT/
|-- assets/
|-- backend/
|   |-- app/
|   |   |-- ai/
|   |   |-- routers/
|   |   |-- services/
|   |   |-- utils/
|   |   |-- config.py
|   |   |-- main.py
|   |-- queries/
|   |-- tests/
|   |-- cache_manager.py
|   |-- data_client.py
|   |-- db.py
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- schema.sql
|   `-- sync.py
|-- data/
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- assets/
|   |   |-- images/
|   |   |-- App.css
|   |   |-- App.jsx
|   |   |-- HomePage.jsx
|   |   |-- index.css
|   |   `-- main.jsx
|   |-- Dockerfile
|   |-- package.json
|   `-- vite.config.js
|-- nginx/
|-- scripts/
|-- .env
|-- .env.example
|-- .gitignore
|-- AGENTS.md
|-- docker-compose.yml
`-- README.md
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

If you want backend-specific overrides, you can also create `backend/.env`:

```bash
OPENAI_API_KEY=your_api_key_here
DB_PATH=./data/gridiron.db
SLEEPER_LEAGUE_ID=your_default_league_id
```

### Docker (Compose)

Build and run the full stack (backend, frontend, nginx proxy):

```
docker compose up --build
```

Then open:

- http://localhost

To stop:

```
docker compose down
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

## Notes

- Database file lives under `data/` by default.
- The API expects valid Sleeper league IDs and a SportsDataIO key.
