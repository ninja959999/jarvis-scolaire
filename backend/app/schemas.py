from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class HomeworkCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    due_date: datetime


class HomeworkOut(HomeworkCreate):
    id: int
    priority_score: float
    is_completed: bool
    model_config = ConfigDict(from_attributes=True)


class TimetableCreate(BaseModel):
    subject: str
    room: str = ""
    start_time: datetime
    end_time: datetime
    is_cancelled: bool = False


class TimetableOut(TimetableCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    trigger_time: datetime
    category: str = "PERSO"
    recurrence_rule: str | None = None


class ReminderOut(ReminderCreate):
    id: int
    is_completed: bool
    model_config = ConfigDict(from_attributes=True)


class DailyLogUpdate(BaseModel):
    bag_prepared: bool | None = None
    clothes_prepared: bool | None = None
    sport_done: bool | None = None


class DailyLogOut(DailyLogUpdate):
    date: date
    homeworks_completed_ratio: float
    model_config = ConfigDict(from_attributes=True)
