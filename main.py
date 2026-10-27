from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx

from .config import settings
from .database import Base, engine, get_db
from .models import User, Chat, Message
from .schemas import RegisterIn, LoginIn, ChatCreateIn, ChatIn
from .security import hash_password, verify_password, create_token, get_current_user, require_admin
from .ai_engine import generate_reply

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0", description="JVM Technologies AI Platform API")
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def home():
    return FileResponse(static_dir / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name, "ai_provider": settings.ai_provider, "model": settings.ai_model}

@app.post("/api/auth/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    is_first = db.query(User).count() == 0
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password), is_admin=is_first)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user), "token_type": "bearer", "user": user_payload(user)}

@app.post("/api/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == payload.email.strip().lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"access_token": create_token(user), "token_type": "bearer", "user": user_payload(user)}

def user_payload(user: User):
    return {"id": user.id, "name": user.name, "email": user.email, "is_admin": user.is_admin}

@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return user_payload(user)

@app.get("/api/admin/summary")
def admin_summary(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return {
        "users": db.query(User).count(),
        "chats": db.query(Chat).count(),
        "messages": db.query(Message).count(),
        "admin": user_payload(admin)
    }

@app.get("/api/chats")
def list_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chats = db.query(Chat).filter(Chat.user_id == user.id).order_by(Chat.id.desc()).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in chats]

@app.post("/api/chats")
def create_chat(payload: ChatCreateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = Chat(user_id=user.id, title=payload.title.strip() or "New conversation")
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {"id": chat.id, "title": chat.title}

@app.get("/api/chats/{chat_id}")
def get_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"id": chat.id, "title": chat.title, "messages": [{"role": m.role, "content": m.content} for m in chat.messages]}

@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(chat)
    db.commit()
    return {"ok": True}

@app.post("/api/chat")
async def chat(payload: ChatIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat_obj = None
    if payload.chat_id is not None:
        chat_obj = db.query(Chat).filter(Chat.id == payload.chat_id, Chat.user_id == user.id).first()
        if not chat_obj:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        title = " ".join(payload.message.strip().split())[:55] or "New conversation"
        chat_obj = Chat(user_id=user.id, title=title)
        db.add(chat_obj)
        db.commit()
        db.refresh(chat_obj)

    db.add(Message(chat_id=chat_obj.id, role="user", content=payload.message.strip()))
    db.commit()
    recent = db.query(Message).filter(Message.chat_id == chat_obj.id).order_by(Message.id.asc()).all()
    history = [{"role": m.role, "content": m.content} for m in recent]
    try:
        answer = await generate_reply(history, payload.mode)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="The AI service timed out. Try again or increase AI_TIMEOUT_SECONDS.")
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        detail = "AI provider returned an error. Check provider URL, model name, and API key."
        if status_code == 401:
            detail = "AI provider rejected the API key. Check AI_API_KEY."
        elif status_code == 404:
            detail = "AI model or endpoint was not found. Check AI_BASE_URL and AI_MODEL."
        raise HTTPException(status_code=502, detail=detail)
    except (httpx.ConnectError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(exc)}")
    except (KeyError, IndexError, ValueError):
        raise HTTPException(status_code=502, detail="AI provider returned an unexpected response.")
    db.add(Message(chat_id=chat_obj.id, role="assistant", content=answer))
    db.commit()
    return {"chat_id": chat_obj.id, "title": chat_obj.title, "reply": answer}
