import os
import sys
# Add the current directory (backend/) to sys.path so absolute imports resolve under any working directory context
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
# Load environment variables from the .env file in the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, admin
app = FastAPI(title="FrostGuard AC Services API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(admin.router, prefix="/api/v1/admin")
