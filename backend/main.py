from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat, admin
app = FastAPI(title="FrostGuard AC Services API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(admin.router, prefix="/api/v1/admin")
