"""입사절차(EmployeeOnboarding) 문서 모델 — HR 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class OnboardingActivity(BaseModel):
    """입사절차 활동 항목."""

    task: str
    status: str = "pending"
    responsible: str = ""


class EmployeeOnboardingCreate(BaseModel):
    """입사절차 생성 요청 스키마."""

    employee: str
    onboarding_date: date | None = None
    activities: list[OnboardingActivity] = []


class EmployeeOnboardingUpdate(BaseModel):
    """입사절차 수정 요청 스키마."""

    employee: str | None = None
    onboarding_date: date | None = None
    activities: list[OnboardingActivity] | None = None


class EmployeeOnboarding(BaseDocument):
    """입사절차 문서 — HR 입사 온보딩 트랜잭션.

    naming prefix: EON
    """

    employee: str = ""
    onboarding_date: date | None = None
    activities: list[OnboardingActivity] = []
