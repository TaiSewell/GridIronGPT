# GridironGPT — AI Fantasy Football Assistant

**GridironGPT** is an AI-powered fantasy football assistant that combines real **statistical data**, **Sleeper API league syncing**, and **OpenAI** formatting to generate clear, conversational fantasy insights.

The backend fetches league, roster, player, and matchup data from the Sleeper API & SportsDataIO API, caches it locally in **SQLite**, and exposes it through a lightweight **FastAPI** service.
The frontend (React + Tailwind) will provide an interactive chat interface powered by the OpenAI Mini Model for natural, easy-to-read analysis.

---

## 🧠 Tech Stack
| **Layer**      | **Technology**                | **Purpose**                                      |
|----------------|-------------------------------|--------------------------------------------------|
| Frontend       | React + Vite + Tailwind       | Chat interface + user input                      |
| Backend        | FastAPI (Python)              | Syncs data, exposes endpoints, AI formatting     |
| Database       | SQLite                        | Local cache of Sleeper API data                  |
| External API   | Sleeper API, SportsDataIO API | Provides league, roster, matchup & player info   |
| AI             | OpenAI Mini Model             | Conversational formatting of backend output      |

---

## 🗂️ Project Structure
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

### 🔑 Environment Variables
Create a .env file inside backend/:
```bash
OPENAI_API_KEY=your_api_key_here
DB_PATH=./data/gridiron.db
SLEEPER_LEAGUE_ID=your_default_league_id   # optional
```