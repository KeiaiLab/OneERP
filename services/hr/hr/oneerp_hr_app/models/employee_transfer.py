"""인사이동(EmployeeTransfer) 문서 모델 — HR 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class EmployeeTransferCreate(BaseModel):
    """인사이동 생성 요청 스키마."""

    employee: str
    employee_name: str = ""
    transfer_date: date | None = None
    from_department: str = ""
    to_department: str = ""
    from_designation: str = ""
    to_designation: str = ""
    reason: str = ""


class EmployeeTransferUpdate(BaseModel):
    """인사이동 수정 요청 스키마."""

    employee: str | None = None
    employee_name: str | None = None
    transfer_date: date | None = None
    from_department: str | None = None
    to_department: str | None = None
    from_designation: str | None = None
    to_designation: str | None = None
    reason: str | None = None


class EmployeeTransfer(BaseDocument):
    """인사이동 문서 — HR 인사이동 트랜잭션.

    naming prefix: ETR
    """

    employee: str = ""
    employee_name: str = ""
    transfer_date: date | None = None
    from_department: str = ""
    to_department: str = ""
    from_designation: str = ""
    to_designation: str = ""
    reason: str = ""
