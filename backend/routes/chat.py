from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from services.agent import AgentPipeline
router = APIRouter()
agent = AgentPipeline()
@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest):
    res = agent.run(req.query, req.history)
    return ChatResponse(**res)
