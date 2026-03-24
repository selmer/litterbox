from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel


# --- Cat schemas ---

class CatCreate(BaseModel):
    name: str
    reference_weight_kg: Optional[float] = None


class CatUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    reference_weight_kg: Optional[float] = None


class CatOut(BaseModel):
    id: int
    name: str
    active: bool
    reference_weight_kg: Optional[float]
    photo_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Visit schemas ---

class VisitOut(BaseModel):
    id: int
    cat_id: Optional[int]
    identified_by: Optional[Literal["auto", "manual"]]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    weight_kg: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class VisitCreate(BaseModel):
    cat_id: int
    started_at: datetime
    duration_seconds: int
    weight_kg: float


class VisitUpdate(BaseModel):
    cat_id: Optional[int] = None
    identified_by: Optional[Literal["auto", "manual"]] = None


class WeightDataPoint(BaseModel):
    timestamp: datetime
    weight_kg: float
    visit_id: int


class WeightHistory(BaseModel):
    cat_id: int
    cat_name: str
    data: list[WeightDataPoint]


# --- Cleaning cycle schemas ---

class CleaningCycleOut(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Dashboard schemas ---

class CatDashboard(BaseModel):
    cat_id: int
    cat_name: str
    reference_weight_kg: Optional[float]
    photo_url: Optional[str] = None
    visits_today: int
    time_in_box_today_seconds: int
    last_visit_at: Optional[datetime]
    last_visit_weight_kg: Optional[float]
    last_visit_duration_seconds: Optional[int]


class DashboardOut(BaseModel):
    cats: list[CatDashboard]
    unidentified_visits_today: int
    cleaning_cycles_today: int
    poller_healthy: bool
    generated_at: datetime


# --- Tuya webhook payload schemas ---

class TuyaDPStatus(BaseModel):
    code: str
    value: Any          # int, bool, or str depending on DP


class TuyaWebhookPayload(BaseModel):
    dataId: str
    devId: str
    productKey: Optional[str] = None
    status: list[TuyaDPStatus]