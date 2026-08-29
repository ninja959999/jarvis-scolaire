from datetime import date, datetime, time, timedelta
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
import httpx
import os
from .database import Base, engine, get_db
from .models import DailyLog, Homework, Reminder, TimetableEntry
from .schemas import *
from .seed import ensure_demo_data
from .settings import settings

Base.metadata.create_all(bind=engine)
app = FastAPI(title="JARVIS Scolaire API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def current_user(db: Session):
    return ensure_demo_data(db)


@app.get("/health")
def health():
    return {"status": "ok", "service": "jarvis-api", "database": settings.database_url.split(":", 1)[0]}


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    user = current_user(db)
    today = date.today()
    start = datetime.combine(today, time.min)
    end = start + timedelta(days=1)
    return {
        "user": {"name": user.name, "email": user.email},
        "homeworks": db.scalars(select(Homework).where(Homework.user_id == user.id, Homework.is_completed == False).order_by(Homework.priority_score.desc())).all(),
        "timetable": db.scalars(select(TimetableEntry).where(TimetableEntry.user_id == user.id, TimetableEntry.start_time >= start, TimetableEntry.start_time < end).order_by(TimetableEntry.start_time)).all(),
        "reminders": db.scalars(select(Reminder).where(Reminder.user_id == user.id, Reminder.is_completed == False).order_by(Reminder.trigger_time)).all(),
    }


@app.post("/api/homeworks", response_model=HomeworkOut)
def create_homework(payload: HomeworkCreate, db: Session = Depends(get_db)):
    user = current_user(db)
    days_left = max(0, (payload.due_date.date() - date.today()).days)
    score = round(10 / (days_left + 1), 2)
    item = Homework(**payload.model_dump(), priority_score=score, user_id=user.id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@app.patch("/api/homeworks/{item_id}/complete", response_model=HomeworkOut)
def complete_homework(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Homework, item_id)
    if not item: raise HTTPException(404, "Devoir introuvable")
    item.is_completed = True; db.commit(); db.refresh(item)
    return item


@app.post("/api/reminders", response_model=ReminderOut)
def create_reminder(payload: ReminderCreate, db: Session = Depends(get_db)):
    user = current_user(db)
    item = Reminder(**payload.model_dump(), user_id=user.id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@app.patch("/api/reminders/{item_id}/complete", response_model=ReminderOut)
def complete_reminder(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Reminder, item_id)
    if not item: raise HTTPException(404, "Rappel introuvable")
    item.is_completed = True; db.commit(); db.refresh(item)
    return item


@app.get("/api/logs/today", response_model=DailyLogOut)
def today_log(db: Session = Depends(get_db)):
    user = current_user(db)
    item = db.get(DailyLog, date.today())
    if not item:
        item = DailyLog(date=date.today(), user_id=user.id); db.add(item); db.commit(); db.refresh(item)
    return item


@app.patch("/api/logs/today", response_model=DailyLogOut)
def update_today_log(payload: DailyLogUpdate, db: Session = Depends(get_db)):
    item = today_log(db)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    db.commit(); db.refresh(item)
    return item


@app.post("/api/sync/demo")
def sync_demo(db: Session = Depends(get_db)):
    ensure_demo_data(db)
    return {"message": "Données de démonstration synchronisées", "pronote_connected": False}


@app.post("/api/ai/chat")
async def ai_chat(payload: dict):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(503, "OPENROUTER_API_KEY non configurée sur le serveur")
    incoming = payload.get("messages", [])[-12:]
    messages = [{"role": "system", "content": "Tu es JARVIS, un tuteur scolaire français, clair, encourageant et concis. Aide l’élève à comprendre, réviser et s’organiser. Ne prétends pas connaître une information absente du contexte."}]
    for item in incoming:
        role = "assistant" if item.get("role") == "assistant" else "user"
        content = str(item.get("content", "")).strip()[:4000]
        if content:
            messages.append({"role": role, "content": content})
    if len(messages) == 1:
        raise HTTPException(400, "Message vide")
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "HTTP-Referer": "https://jarvis-scolaire.vercel.app", "X-Title": "JARVIS Scolaire"},
                json={"model": "openrouter/free", "messages": messages, "stream": False},
            )
        if response.status_code >= 400:
            raise HTTPException(response.status_code, "Le service IA est momentanément indisponible")
        result = response.json()
        return {"message": result["choices"][0]["message"]["content"], "model": result.get("model", "openrouter/free")}
    except httpx.TimeoutException:
        raise HTTPException(504, "Le service IA met trop de temps à répondre")
