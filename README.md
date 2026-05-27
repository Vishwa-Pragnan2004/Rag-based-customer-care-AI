# 🧊 FrostGuard AC Services — Cloud-Native Customer Care AI

An intelligent, cloud-native customer care system for AC services, powered by **RAG (Retrieval-Augmented Generation)**, the **Google Gemini API**, and **Supabase**. It features a user-facing AI chatbot and a full admin dashboard for managing appointments, customers, and service tickets.

This project is fully optimized for **Vercel Serverless** deployment and can be hosted **100% free of cost**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase)
![Vercel](https://img.shields.io/badge/Vercel-Deployment-000000?logo=vercel)

---

## ✨ Features

### 🤖 AI Chatbot (User-Facing)
- **Natural language appointment booking** (installation, repair, AMC, gas refill).
- **Ticket status tracking** using ticket IDs.
- **FAQ answering** via dynamic RAG (Retrieval-Augmented Generation).
- **Escalation to human agents** when requested.
- **Powered by Google Gemini 1.5 Flash** (Free Tier) — fast response times, zero server overhead.

### 🔐 Admin Dashboard
- **JWT-authenticated** admin login.
- **Dashboard Overview** — real-time stats (customers, appointments, escalations).
- **Customer Management** — registry of customers and their history.
- **Appointment Tracking** — status pipelines: *Requested → Booked → In Progress → Completed*.
- **DB Viewer** — raw database table browser for admins.
- **Status Updates** — assign technicians, set arrival dates, add notes.

---

## 🏗️ Cloud-Optimized Tech Stack

| Layer | local offline (Original) | cloud-ready (Current) |
| :--- | :--- | :--- |
| **Frontend** | React 19 + Vite | React 19 + Vite (Vercel) |
| **Backend** | FastAPI + Uvicorn | FastAPI (Vercel Serverless) |
| **AI/LLM** | Qwen 2.5-0.5B (Local CPU) | **Google Gemini 1.5 Flash** (API) |
| **RAG Store** | FAISS + Sentence-Transformers | **Gemini text-embedding-004** + Pure Python Cosine Similarity |
| **Database** | SQLite (Local file) | **Supabase PostgreSQL** (or SQLite fallback) |
| **Auth** | JWT + bcrypt | JWT + bcrypt |

---

## 🚀 Getting Started (Local Development)

The application operates in **dual-database mode**: if `DATABASE_URL` is omitted, it automatically falls back to a local SQLite database for instant offline testing.

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Clone the Repository
```bash
git clone https://github.com/Vishwa-Pragnan2004/Rag-based-customer-care-AI.git
cd Rag-based-customer-care-AI
```

### 3. Backend Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   
   pip install -r backend/requirements.txt
   ```
2. Copy `backend/.env.example` to `backend/.env` and add your **Gemini API Key** (obtainable for free from [Google AI Studio](https://aistudio.google.com/)):
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   # Optional: Add your Supabase PostgreSQL connection URI if testing cloud DB locally
   DATABASE_URL=
   ```
3. Start the FastAPI backend:
   ```bash
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 4. Frontend Setup
1. Navigate to the frontend directory and install npm packages:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173/` in your browser. (The Admin Panel is located at `http://localhost:5173/admin` — Default Credentials: `admin` / `frostguard2024`).

---

## ☁️ Production Deployment on Vercel (100% Free)

You can deploy the entire stack on Vercel for free under a single domain.

1. **Host a Supabase Database**:
   * Create a free project on [Supabase](https://supabase.com/).
   * Copy the transaction PostgreSQL URI from **Settings -> Database** (ensure it ends with `?sslmode=require`).
2. **Push to GitHub**:
   * Commit all your local changes and push them to your GitHub repository.
3. **Import to Vercel**:
   * Log into [Vercel](https://vercel.com) and click **Add New -> Project**.
   * Import your GitHub repository.
   * Under **Environment Variables**, add the following keys:
     - `GEMINI_API_KEY` = `your-gemini-api-key`
     - `DATABASE_URL` = `your-supabase-postgresql-connection-string`
   * Click **Deploy**. Vercel will automatically build the React frontend and deploy the FastAPI backend as a serverless function using the root `vercel.json` configurations.