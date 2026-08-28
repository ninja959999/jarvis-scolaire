from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Homework, TimetableEntry, User
from .settings import settings


def ensure_demo_data(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == settings.dev_user_email))
    if not user:
        user = User(email=settings.dev_user_email, name=settings.dev_user_name)
        db.add(user)
        db.flush()
    if not db.scalar(select(Homework).where(Homework.user_id == user.id)):
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        db.add_all([
            Homework(subject="Maths", description="Exercices 12 à 18", due_date=now + timedelta(days=1), priority_score=8.2, user_id=user.id),
            Homework(subject="Histoire", description="Lire le chapitre 4", due_date=now + timedelta(days=3), priority_score=5.4, user_id=user.id),
        ])
        db.add(TimetableEntry(subject="Maths", room="B204", start_time=now.replace(hour=8), end_time=now.replace(hour=9), user_id=user.id))
        db.add(TimetableEntry(subject="Français", room="A103", start_time=now.replace(hour=10), end_time=now.replace(hour=11), user_id=user.id))
    db.commit()
    return user
