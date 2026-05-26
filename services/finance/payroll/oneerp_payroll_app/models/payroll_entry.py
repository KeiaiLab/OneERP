"""급여대장(PayrollEntry) 문서 모델 — Payroll 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class PayrollEmployeeEntry(BaseModel):
    """급여대장 직원 항목 — HR 마스터의 읽기 전용 스냅샷.

    HR Employee 문서에서 비정규화 복사된 데이터이다.
    EMPLOYEE_UPDATED 이벤트로 DRAFT 상태의 급여대장에서 자동 동기화된다.
    SUBMITTED/CANCELLED 상태의 급여대장은 확정 이력 보존을 위해 갱신하지 않는다.

    동기화 대상 필드: employee_name, department, designation
    """

    employee_id: str = ""
    employee_name: str = ""
    department: str = ""
    designation: str = ""
    base_salary: Decimal = Decimal(0)
    overtime_hours: Decimal = Decimal(0)
    bonus: Decimal = Decimal(0)
    allowances: Decimal = Decimal(0)
    dependents: int = 1


class PayrollEntryCreate(BaseModel):
    """급여대장 생성 요청 스키마.

    E2E 흐름에서 사용하는 필드:
    - company, posting_date, payroll_frequency
    - start_date, end_date: 급여 기간
    - salary_structure_id: 급여구조 참조
    - department: 대상 부서
    - employee_ids: 대상 직원 ID 목록 (employees 자동 생성용)
    """

    payroll_date: date | None = None
    posting_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    company: str = ""
    department: str = ""
    payroll_frequency: str = ""
    salary_structure_id: str = ""
    employee_ids: list[str] = Field(default_factory=list, description="급여 대상 직원 ID 목록")
    employees: list[dict[str, Any]] = Field(
        default_factory=list,
        description="직원별 급여 데이터 (PayrollEmployeeEntry 스키마 참조)",
    )
    total_amount: Decimal = Decimal(0)


class PayrollEntryUpdate(BaseModel):
    """급여대장 수정 요청 스키마."""

    payroll_date: date | None = None
    posting_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    company: str | None = None
    department: str | None = None
    payroll_frequency: str | None = None
    salary_structure_id: str | None = None
    total_amount: Decimal | None = None


class PayrollEntry(BaseDocument):
    """급여대장 문서 — Payroll 급여 트랜잭션.

    naming prefix: PRLE

    employees 배열은 HR Employee 마스터의 **읽기 전용 스냅샷**이다.
    - 생성 시점에 HR에서 복사된 employee_name, department, designation 등을 포함한다.
    - DRAFT 상태에서는 EMPLOYEE_UPDATED 이벤트를 통해 최신 정보로 자동 동기화된다.
    - SUBMITTED/CANCELLED 상태에서는 확정 이력 보존을 위해 갱신하지 않는다.
    """

    payroll_date: date | None = None
    posting_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    company: str = ""
    department: str = ""
    payroll_frequency: str = ""
    salary_structure_id: str = ""
    employee_ids: list[str] = Field(default_factory=list, description="급여 대상 직원 ID 목록")
    employees: list[dict[str, Any]] = Field(
        default_factory=list,
        description="HR 마스터의 읽기 전용 스냅샷 — EMPLOYEE_UPDATED 이벤트로 동기화",
    )
    total_amount: Decimal = Decimal(0)
