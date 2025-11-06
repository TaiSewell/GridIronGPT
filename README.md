# 🏈 GridironGPT — AI Fantasy Football Assistant
<h2>Status: In Development</h2>

**GridironGPT** is a conversational fantasy football assistant that blends real statistical analysis with AI-powered formatting.  
Built with **React**, **FastAPI**, **Python**, and **SQLite**, the app processes and analyzes player data on the backend while the **OpenAI Mini model** delivers responses that are easy to read, insightful, and conversational.

---

## 🚀 Features

- 🧮 **Backend-Driven Logic** – All projections, matchup evaluations, and player rankings are handled by the FastAPI backend.  
- 🤖 **AI-Powered Formatting** – The OpenAI Mini model reformats backend output into clear, chat-style advice.  
- 💬 **Smart Chat Interface** – Users can ask questions like “Who are the best RB matchups this week?” or “Should I start this QB?”  
- 🗂️ **SQLite Data Layer** – Stores and indexes player stats, projections, and roster information.  
- ⚡ **Modern Frontend** – Built with React, Vite, and Tailwind CSS for fast, responsive performance.

---

## 🧠 Tech Stack

| Layer | Technology | Description |
|-------|-------------|-------------|
| **Frontend** | React + Vite + Tailwind CSS | Interactive chat UI |
| **Backend** | FastAPI (Python) | Handles all logic, routes, and AI requests |
| **Database** | SQLite | Stores fantasy player data |
| **AI Integration** | OpenAI Mini Model | Formats backend results conversationally |

---

## 🗂️ Project Structure

![Project Structure](/assets/File%20Structure%20GridIronGPT.png)

---

## ⚙️ Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/taisewell/GridironGPT.git
cd GridironGPT
```
```bash
2️⃣ Backend Setup
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```
```bash
3️⃣ Frontend Setup
cd frontend
npm install
npm run dev
```

### 🔑 Environment Variables
Create a .env file in your backend directory with:
OPENAI_API_KEY=your_api_key_here
This key connects to the OpenAI Mini model, which formats backend data into conversational responses.

💡 Roadmap
 Phase 0 – Setup

 Phase 1 – Data Layer (schema, load_csv, db.py)

 Phase 2 – Backend Logic & Projections

 Phase 3 – OpenAI Mini Model Integration (formatting layer)

 Phase 4 – React Chat Interface

 Phase 5 – Deployment

 Phase 6 – UI Polish & Documentation

🧩 Future Enhancements
Add user authentication and saved team data

Integrate live API data (injuries, projections, weather)

Deploy to Vercel (frontend) + Render/AWS (backend)

Expand AI model context for deeper analysis

📜 License
This project is licensed under the MIT License.

Developed by Tai Sewell

“Where stats meet strategy.”

