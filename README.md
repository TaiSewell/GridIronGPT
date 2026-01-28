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
```

Developed by Tai Sewell

“Where stats meet strategy.”




