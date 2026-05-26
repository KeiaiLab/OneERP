"""퇴사절차(EmployeeOffboarding) 문서 모델 — HR 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class OffboardingActivity(BaseModel):
    """퇴사절차 활동 항목."""

    task: str
    status: str = "pending"
    responsible: str = ""


class EmployeeOffboardingCreate(BaseModel):
    """퇴사절차 생성 요청 스키마."""

    employee: str
    offboarding_date: date | None = None
    activities: list[OffboardingActivity] = []


class EmployeeOffboardingUpdate(BaseModel):
    """퇴사절차 수정 요청 스키마."""

    employee: str | None = None
    offboarding_date: date | None = None
    activities: list[OffboardingActivity] | None = None


class EmployeeOffboarding(BaseDocument):
    """퇴사절차 문서 — HR 퇴사 오프보딩 트랜잭션.

    naming prefix: EOF
    """

    employee: str = ""
    offboarding_date: date | None = None
    activities: list[OffboardingActivity] = []
