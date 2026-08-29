from datetime import date, datetime, time, timedelta
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
import httpx
import os
import hashlib
import hmac
import time as unix_time
from urllib.parse import urlencode
from .database import Base, engine, get_db
from .models import DailyLog, Homework, IntegrationCredential, Reminder, TimetableEntry, User
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


@app.get("/api/preferences")
def preferences():
    return {"weather_city": settings.weather_city, "train": {"departure": settings.train_departure_station, "arrival": settings.train_arrival_station, "usual_time": settings.train_usual_time}, "gmail_ready": bool(settings.google_client_id and settings.google_client_secret)}


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


@app.get("/api/weather")
async def weather():
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            geo = await client.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": settings.weather_city, "count": 1, "language": "fr", "format": "json"})
            geo.raise_for_status()
            location = geo.json()["results"][0]
            forecast = await client.get("https://api.open-meteo.com/v1/forecast", params={"latitude": location["latitude"], "longitude": location["longitude"], "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m", "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code", "forecast_days": 1, "timezone": "Europe/Paris"})
            forecast.raise_for_status()
            result = forecast.json()
            current = result["current"]
            daily = result["daily"]
            return {"city": settings.weather_city, "temperature": current["temperature_2m"], "feels_like": current["apparent_temperature"], "weather_code": current["weather_code"], "wind": current["wind_speed_10m"], "max": daily["temperature_2m_max"][0], "min": daily["temperature_2m_min"][0], "rain_probability": daily["precipitation_probability_max"][0]}
    except (httpx.HTTPError, KeyError, IndexError):
        raise HTTPException(502, "Météo indisponible pour le moment")




def gmail_session_cookie(user_id: int):
    issued = str(int(unix_time.time()))
    raw = f"{user_id}.{issued}"
    signature = hmac.new(settings.google_client_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{signature}"


def verify_gmail_session(value: str):
    try:
        user_id, issued, signature = value.split(".", 2)
        raw = f"{user_id}.{issued}"
        expected = hmac.new(settings.google_client_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if unix_time.time() - int(issued) > 86400 or not hmac.compare_digest(signature, expected):
            return None
        return int(user_id)
    except (ValueError, TypeError):
        return None


@app.get("/api/integrations/gmail/status")
def gmail_status(db: Session = Depends(get_db)):
    user = current_user(db)
    credential = db.scalar(select(IntegrationCredential).where(IntegrationCredential.user_id == user.id, IntegrationCredential.provider == "gmail"))
    return {"configured": bool(settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri), "connected": credential is not None}


def gmail_state():
    issued = str(int(unix_time.time()))
    signature = hmac.new(settings.google_client_secret.encode(), issued.encode(), hashlib.sha256).hexdigest()
    return f"{issued}.{signature}"


@app.get("/api/integrations/gmail/start")
def gmail_start():
    if not settings.google_client_id or not settings.google_client_secret or not settings.google_redirect_uri:
        raise HTTPException(503, "Identifiants Google OAuth non configurés")
    state = gmail_state()
    params = {"client_id": settings.google_client_id, "redirect_uri": settings.google_redirect_uri, "response_type": "code", "access_type": "offline", "prompt": "consent", "scope": "https://www.googleapis.com/auth/gmail.readonly", "state": state}
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))


@app.get("/api/integrations/gmail/callback", response_class=HTMLResponse)
async def gmail_callback(code: str = "", state: str = "", error: str = "", db: Session = Depends(get_db)):
    if error:
        return HTMLResponse("<h2>Connexion Gmail annulée</h2><p>Tu peux fermer cette fenêtre et revenir dans JARVIS.</p>", status_code=400)
    if not code or "." not in state:
        raise HTTPException(400, "Retour OAuth invalide")
    issued, signature = state.split(".", 1)
    expected = hmac.new(settings.google_client_secret.encode(), issued.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected) or unix_time.time() - int(issued) > 600:
        raise HTTPException(400, "Session OAuth expirée")
    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post("https://oauth2.googleapis.com/token", data={"code": code, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret, "redirect_uri": settings.google_redirect_uri, "grant_type": "authorization_code"})
    if token_response.status_code >= 400:
        raise HTTPException(502, "Google n’a pas accepté la connexion")
    token = token_response.json()
    user = current_user(db)
    credential = db.scalar(select(IntegrationCredential).where(IntegrationCredential.user_id == user.id, IntegrationCredential.provider == "gmail"))
    if credential:
        credential.access_token = token.get("access_token", credential.access_token)
        credential.refresh_token = token.get("refresh_token", credential.refresh_token)
        credential.expires_at = datetime.utcnow() + timedelta(seconds=int(token.get("expires_in", 3600)))
    else:
        credential = IntegrationCredential(provider="gmail", access_token=token["access_token"], refresh_token=token.get("refresh_token", ""), expires_at=datetime.utcnow() + timedelta(seconds=int(token.get("expires_in", 3600))), user_id=user.id)
        db.add(credential)
    db.commit()
    response = HTMLResponse("<h2>Gmail est connecté à JARVIS ✅</h2><p>Tu peux fermer cette fenêtre et retourner dans ton espace.</p>"); response.set_cookie("jarvis_gmail_session", gmail_session_cookie(user.id), httponly=True, secure=True, samesite="lax", max_age=86400); return response


@app.get("/api/integrations/gmail/messages")
async def gmail_messages(request: Request, db: Session = Depends(get_db)):
    session_user_id = verify_gmail_session(request.cookies.get("jarvis_gmail_session", ""))
    if not session_user_id:
        raise HTTPException(401, "Session Gmail absente ou expirée")
    user = db.get(User, session_user_id)
    if not user:
        raise HTTPException(401, "Utilisateur inconnu")
    credential = db.scalar(select(IntegrationCredential).where(IntegrationCredential.user_id == user.id, IntegrationCredential.provider == "gmail"))
    if not credential:
        raise HTTPException(401, "Gmail n’est pas connecté")
    access_token = credential.access_token
    if not credential.expires_at or credential.expires_at <= datetime.utcnow() + timedelta(seconds=60):
        async with httpx.AsyncClient(timeout=20) as client:
            refreshed = await client.post("https://oauth2.googleapis.com/token", data={"client_id": settings.google_client_id, "client_secret": settings.google_client_secret, "refresh_token": credential.refresh_token, "grant_type": "refresh_token"})
        if refreshed.status_code >= 400:
            raise HTTPException(401, "Autorisation Gmail expirée")
        refreshed_data = refreshed.json()
        access_token = refreshed_data["access_token"]
        credential.access_token = access_token
        credential.expires_at = datetime.utcnow() + timedelta(seconds=int(refreshed_data.get("expires_in", 3600)))
        db.commit()
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=20) as client:
        listed = await client.get("https://gmail.googleapis.com/gmail/v1/users/me/messages", headers=headers, params={"q": "is:unread newer_than:30d", "maxResults": 10})
        if listed.status_code >= 400:
            raise HTTPException(502, "Impossible de lire Gmail")
        items = []
        for item in listed.json().get("messages", []):
            detail = await client.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}", headers=headers, params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]})
            if detail.status_code < 400:
                headers_map = {h["name"].lower(): h["value"] for h in detail.json().get("payload", {}).get("headers", [])}
                items.append({"id": item["id"], "subject": headers_map.get("subject", "(sans objet)"), "from": headers_map.get("from", ""), "date": headers_map.get("date", "")})
    return {"messages": items}


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
