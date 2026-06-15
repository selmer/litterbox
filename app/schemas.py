from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.durations import TRUSTED_DURATION_SOURCES


MAX_CAT_WEIGHT_KG = 20.0
MAX_VISIT_DURATION_SECONDS = 60 * 60
DurationSource = Literal["status_dp", "report_log_counter", "report_log_duration", "manual", "hard_timeout", "unknown"]
WeightConfidence = Literal["normal", "suspect", "ignored"]
WeightConfidenceReason = Literal["manual", "outlier_delta", "operator_ignored", "operator_restored"]
CatEventType = Literal["vet_visit", "medication", "diet_change", "grooming", "health_note", "milestone", "other"]
HealthSignalSeverity = Literal["info", "watch", "attention"]
VisitSummaryBucket = Literal["day", "week", "month"]


# --- Cat schemas ---

class CatCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    reference_weight_kg: Optional[float] = Field(default=None, gt=0, le=MAX_CAT_WEIGHT_KG)
    birth_date: Optional[date] = None

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
    birth_date: Optional[date] = None

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
    birth_date: Optional[date] = None
    photo_url: Optional[str] = None
    created_at: datetime


# --- Cat event schemas ---

class CatEventCreate(BaseModel):
    event_type: CatEventType
    cat_ids: Optional[list[int]] = None
    occurred_at: date
    title: str = Field(min_length=1, max_length=120)
    notes: Optional[str] = Field(default=None, max_length=2000)
    cost_amount: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    cost_currency: str = Field(default="EUR", min_length=3, max_length=3)

    @field_validator("cat_ids")
    @classmethod
    def cat_ids_must_not_be_empty(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        if value is not None and len(value) == 0:
            raise ValueError("At least one cat must be selected")
        return value

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value

    @field_validator("notes")
    @classmethod
    def notes_blank_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        return value or None

    @field_validator("cost_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class CatEventUpdate(BaseModel):
    event_type: Optional[CatEventType] = None
    cat_ids: Optional[list[int]] = None
    occurred_at: Optional[date] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    notes: Optional[str] = Field(default=None, max_length=2000)
    cost_amount: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    cost_currency: Optional[str] = Field(default=None, min_length=3, max_length=3)

    @field_validator("cat_ids")
    @classmethod
    def cat_ids_must_not_be_empty(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        if value is not None and len(value) == 0:
            raise ValueError("At least one cat must be selected")
        return value

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value

    @field_validator("notes")
    @classmethod
    def notes_blank_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        return value or None

    @field_validator("cost_currency")
    @classmethod
    def normalize_currency(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return value.strip().upper()


class CatEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cat_id: int
    cat_ids: list[int] = Field(default_factory=list)
    cat_names: list[str] = Field(default_factory=list)
    event_type: CatEventType
    occurred_at: date
    title: str
    notes: Optional[str]
    cost_amount: Optional[Decimal]
    cost_currency: str
    created_at: datetime
    updated_at: datetime


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
    weight_confidence: WeightConfidence = "normal"
    weight_confidence_reason: Optional[str] = None
    created_at: datetime

    @model_validator(mode="after")
    def hide_untrusted_duration(self):
        if (
            self.duration_seconds is None
            or self.duration_is_estimated
            or self.duration_source not in TRUSTED_DURATION_SOURCES
        ):
            self.duration_seconds = None
        return self


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
    weight_confidence: WeightConfidence = "normal"


class VisitUpdate(BaseModel):
    cat_id: Optional[int] = Field(default=None, gt=0)
    started_at: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(default=None, gt=0, le=MAX_VISIT_DURATION_SECONDS)
    weight_kg: Optional[float] = Field(default=None, gt=0, le=MAX_CAT_WEIGHT_KG)
    weight_confidence: Optional[WeightConfidence] = None


class VisitSummaryCatOut(BaseModel):
    cat_id: Optional[int]
    cat_name: Optional[str]
    visit_count: int
    average_duration_seconds: Optional[int] = None
    average_weight_kg: Optional[float] = None
    latest_visit_at: Optional[datetime] = None


class VisitSummaryBucketOut(BaseModel):
    bucket: VisitSummaryBucket
    bucket_start: datetime
    bucket_end: datetime
    visit_count: int
    identified_visit_count: int
    unidentified_visit_count: int
    average_visits_per_day: float
    average_duration_seconds: Optional[int] = None
    latest_visit_at: Optional[datetime] = None
    cats: list[VisitSummaryCatOut] = Field(default_factory=list)


class WeightDataPoint(BaseModel):
    timestamp: datetime
    weight_kg: float
    visit_id: int
    weight_confidence: WeightConfidence = "normal"


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

class HealthSignal(BaseModel):
    id: str
    type: str
    severity: HealthSignalSeverity
    message: str
    detail: Optional[str] = None
    cat_id: Optional[int] = None
    cat_name: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


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
    health_signal: Optional[HealthSignal] = None


class DashboardOut(BaseModel):
    cats: list[CatDashboard]
    unidentified_visits_today: int
    cleaning_cycles_today: int
    health_signals: list[HealthSignal] = Field(default_factory=list)
    device_faults: list[str] = Field(default_factory=list)
    device_fault_code: Optional[int] = None
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


# --- Diagnostics schemas ---

class DiagnosticsPollerOut(BaseModel):
    mode: str
    healthy: bool
    last_successful_at: Optional[datetime] = None
    last_attempted_at: Optional[datetime] = None
    last_error: Optional[str] = None
    interval_seconds: int
    healthy_threshold_seconds: int


class DiagnosticsOpenVisitOut(BaseModel):
    id: int
    cat_id: Optional[int]
    identified_by: Optional[Literal["auto", "manual"]]
    started_at: datetime
    age_seconds: int
    weight_kg: Optional[float]
    last_weight_at: Optional[datetime]
    duration_source: DurationSource = "unknown"


class DiagnosticsOpenVisitsOut(BaseModel):
    count: int
    oldest_started_at: Optional[datetime] = None
    oldest_age_seconds: Optional[int] = None
    visits: list[DiagnosticsOpenVisitOut]


class DiagnosticsReconciliationOut(BaseModel):
    reconciliation_attempts: int
    report_logs_fetched: int
    pending_retries: int
    completion_matches: int
    hard_timeouts: int
    latest_event_at: Optional[datetime] = None


class DiagnosticsEndpointOut(BaseModel):
    label: str
    method: str
    path: str


class DiagnosticsSummaryOut(BaseModel):
    generated_at: datetime
    poller: DiagnosticsPollerOut
    open_visits: DiagnosticsOpenVisitsOut
    recent_diagnostics: list[VisitDiagnosticOut]
    reconciliation: DiagnosticsReconciliationOut
    display: DisplaySummaryOut
    endpoints: list[DiagnosticsEndpointOut]


# --- Tuya webhook payload schemas ---

class TuyaDPStatus(BaseModel):
    code: str
    value: Any          # int, bool, or str depending on DP


class TuyaWebhookPayload(BaseModel):
    dataId: str
    devId: str
    productKey: Optional[str] = None
    status: list[TuyaDPStatus]
