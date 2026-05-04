from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    query: str
    conversation_id: str = "default"
    history: List[Dict[str, str]] = []

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]
    result: Any = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    tool_calls: List[ToolCall] = []
    intent: str = "general"
    confidence: float = 0.0

# ---------------------------------------------------------------------------
# Admin schemas
# ---------------------------------------------------------------------------
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    token: str
    username: str

class AppointmentUpdateRequest(BaseModel):
    status: str
    technician: Optional[str] = None
    arrival_date: Optional[str] = None
    notes: Optional[str] = None
