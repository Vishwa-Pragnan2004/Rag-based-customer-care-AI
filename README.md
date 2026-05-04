# 🧊 FrostGuard AC Services — RAG-Based Customer Care AI

An intelligent customer care system for AC services, powered by **RAG (Retrieval-Augmented Generation)** and a local LLM. Features a user-facing AI chatbot and a full admin dashboard for managing appointments, customers, and service tickets.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)

---

## ✨ Features

### 🤖 AI Chatbot (User-Facing)
- Natural language appointment booking (installation, repair, AMC, gas refill)
- Ticket status tracking with ticket IDs
- FAQ answering via RAG (Retrieval-Augmented Generation)
- Escalation to human agents
- Powered by **Qwen 2.5 (0.5B)** running locally — no API keys needed

### 🔐 Admin Dashboard
- **JWT-authenticated** admin login
- **Dashboard** — real-time stats (customers, tickets, escalations)
- **Customer Management** — searchable user registry
- **Appointment Tracking** — 5-step status pipeline:
  ```
  Requested → Booked → Technician Assigned → In Progress → Completed
  ```
- **Escalations Viewer** — monitor escalated tickets
- **DB Viewer** — raw database table browser
- **Status Updates** — assign technicians, set arrival dates, add notes

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 + Vite |
| **Backend** | FastAPI + Uvicorn |
| **AI/LLM** | HuggingFace Transformers (Qwen 2.5-0.5B-Instruct) |
| **RAG** | Sentence-Transformers + FAISS |
| **Database** | SQLite |
| **Auth** | JWT (PyJWT) + bcrypt |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip

### 1. Clone the repo
```bash
git clone https://github.com/Vishwa-Pragnan2004/Rag-based-customer-care-AI.git
cd Rag-based-customer-care-AI
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Start the backend (from project root)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

> The first run will download the Qwen 2.5 model (~500MB). Subsequent runs use the cached model.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Open in Browser
| Page | URL |
|------|-----|
| **Chatbot** | http://localhost:5173/ |
| **Admin Panel** | http://localhost:5173/admin |

**Admin Credentials:** `admin` / `frostguard2024`

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment config
│   ├── data/                   # FAQ knowledge base (.txt files)
│   ├── db/                     # SQLite database (auto-created)
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── routes/
│   │   ├── chat.py             # Chatbot API endpoint
│   │   └── admin.py            # Admin API endpoints (JWT-protected)
│   └── services/
│       ├── agent.py            # AI agent pipeline (intent → tool → response)
│       ├── auth.py             # JWT authentication
│       ├── database.py         # SQLite operations + migrations
│       ├── llm.py              # Local LLM service (Qwen 2.5)
│       ├── logger.py           # Conversation logging
│       ├── rag.py              # RAG: FAISS vector search
│       └── tools.py            # Tool registry (booking, status, etc.)
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main chatbot UI
│   │   ├── components/         # Chat UI components
│   │   ├── pages/admin/        # Admin dashboard pages
│   │   └── styles/admin.css    # Admin panel dark theme
│   └── package.json
└── README.md
```

---

## 🔧 Services & Pricing

| Service | Price |
|---------|-------|
| AC Installation | ₹1,500 |
| AC Repair | ₹500 (visit) + parts |
| Annual Maintenance (AMC) | ₹2,500/year |
| Gas Refill | ₹2,000 |

---

## 📄 License

This project is for educational/demo purposes.