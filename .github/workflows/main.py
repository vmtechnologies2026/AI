from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.config import settings
from app.ai_engine import generate_reply

app = FastAPI(title=settings.app_name)

class ChatRequest(BaseModel):
    messages: list[dict] = Field(min_length=1)
    mode: str = "chat"

@app.get("/")
async def root():
    return {"name": settings.app_name, "status": "running", "docs": "/docs"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "provider": settings.ai_provider}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not settings.ai_model:
        raise HTTPException(status_code=503, detail="AI_MODEL is not configured.")
    try:
        reply = await generate_reply(request.messages, request.mode)
        return {"reply": reply}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {exc}") from exc
