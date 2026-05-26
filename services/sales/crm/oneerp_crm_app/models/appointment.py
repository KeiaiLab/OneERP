"""약속/미팅(Appointment) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AppointmentCreate(BaseModel):
    """약속/미팅 생성 요청 스키마."""

    title: str
    customer_id: str = ""
    scheduled_date: date | None = None
    location: str = ""
    agenda: str = ""
    assigned_to: str = ""


class AppointmentUpdate(BaseModel):
    """약속/미팅 수정 요청 스키마."""

    title: str | None = None
    customer_id: str | None = None
    scheduled_date: date | None = None
    location: str | None = None
    agenda: str | None = None
    assigned_to: str | None = None


class Appointment(BaseDocument):
    """약속/미팅 문서."""

    title: str = ""
    customer_id: str = ""
    scheduled_date: date | None = None
    location: str = ""
    agenda: str = ""
    assigned_to: str = ""
