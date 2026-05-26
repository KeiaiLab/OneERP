"""활동(Activity) 문서 모델 — CRM 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic model_json_schema 런타임 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ActivityCreate(BaseModel):
    """활동 생성 요청 스키마."""

    activity_type: str
    activity_date: date | None = None
    party_type: str = ""
    party: str = ""
    description: str = ""
    assigned_to: str = ""


class ActivityUpdate(BaseModel):
    """활동 수정 요청 스키마."""

    activity_type: str | None = None
    activity_date: date | None = None
    party_type: str | None = None
    party: str | None = None
    description: str | None = None
    assigned_to: str | None = None


class Activity(BaseDocument):
    """활동 문서 — CRM 활동 마스터.

    naming prefix: ACTV
    """

    activity_type: str = ""
    activity_date: date | None = None
    party_type: str = ""
    party: str = ""
    description: str = ""
    assigned_to: str = ""
