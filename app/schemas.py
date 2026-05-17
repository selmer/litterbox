from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_CAT_WEIGHT_KG = 20.0
MAX_VISIT_DURATION_SECONDS = 60 * 60
DurationSource = Literal["status_dp", "report_log_counter", "report_log_duration", "manual", "hard_timeout", "unknown"]


# --- Cat schemas ---

class CatCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    reference_weight_kg: Optional[float] = Field(default=None, gt=0, le=MAX_CAT_WEIGHT_KG)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value


class CatUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    active: Optional[bool] = None
    reference_weight_kg: Optional[float] = Field(default=None, gt=0, le=MAX_CAT_WEIGHT_KG)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value


class CatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    active: bool
    reference_weight_kg: Optional[float]
    photo_url: Optional[str] = None
    created_at: datetime


# --- Visit schemas ---

class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cat_id: Optional[int]
    identified_by: Optional[Literal["auto", "manual"]]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    duration_source: DurationSource = "unknown"
    duration_is_estimated: bool = False
    weight_kg: Optional[float]
    created_at: datetime


class VisitDiagnosticOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visit_id: int
    event_type: str
    payload: dict[str, Any]
    recorded_at: datetime


class VisitCreate(BaseModel):
    cat_id: int = Field(gt=0)
    started_at: datetime
    duration_seconds: int = Field(gt=0, le=MAX_VISIT_DURATION_SECONDS)
    weight_kg: float = Field(gt=0, le=MAX_CAT_WEIGHT_KG)


class VisitUpdate(BaseModel):
    cat_id: Optional[int] = Field(default=None, gt=0)


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    ended_at: Optional[datetime]


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
    poller_last_successful_at: Optional[datetime] = None
    poller_last_attempted_at: Optional[datetime] = None
    poller_last_error: Optional[str] = None
    generated_at: datetime


# --- ESP32 e-paper display schemas ---

class DisplayStatus(BaseModel):
    label: str
    healthy: bool
    last_successful_at: Optional[datetime] = None
    message: Optional[str] = None


class DisplayLatestVisit(BaseModel):
    cat_name: str
    identified: bool
    started_at: datetime
    time_ago_label: str
    duration_seconds: Optional[int]
    weight_kg: Optional[float]
    identified_by: Optional[Literal["auto", "manual"]] = None


class DisplayToday(BaseModel):
    visits: int
    time_in_box_seconds: int
    cleaning_cycles: int
    unidentified_visits: int


class DisplayChartPoint(BaseModel):
    date: str
    weight_kg: float


class DisplayChart(BaseModel):
    label: str
    unit: str
    min_kg: float
    max_kg: float
    points: list[DisplayChartPoint]


class DisplayWeightComparison(BaseModel):
    weight_kg: float
    measured_at: datetime
    delta_kg: float


class DisplayCatSummary(BaseModel):
    name: str
    visits_today: int
    last_weight_kg: Optional[float]
    latest_weight_kg: Optional[float] = None
    latest_weight_at: Optional[datetime] = None
    one_month_ago: Optional[DisplayWeightComparison] = None
    three_months_ago: Optional[DisplayWeightComparison] = None
    sparkline: list[float] = Field(default_factory=list)


class DisplaySummaryOut(BaseModel):
    generated_at: datetime
    refresh_after_seconds: int
    status: DisplayStatus
    latest_visit: Optional[DisplayLatestVisit]
    today: DisplayToday
    chart: Optional[DisplayChart]
    cats: list[DisplayCatSummary]
    alert: Optional[str] = None


# --- Tuya webhook payload schemas ---

class TuyaDPStatus(BaseModel):
    code: str
    value: Any          # int, bool, or str depending on DP


class TuyaWebhookPayload(BaseModel):
    dataId: str
    devId: str
    productKey: Optional[str] = None
    status: list[TuyaDPStatus]
