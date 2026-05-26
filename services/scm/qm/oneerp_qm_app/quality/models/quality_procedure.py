"""품질 절차(QualityProcedure) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class QualityProcedureCreate(BaseModel):
    """품질 절차 생성 요청 스키마."""

    procedure_name: str
    description: str = ""
    process_owner: str = ""
    revision: str = "1.0"
    is_active: bool = True


class QualityProcedureUpdate(BaseModel):
    """품질 절차 수정 요청 스키마."""

    procedure_name: str | None = None
    description: str | None = None
    process_owner: str | None = None
    revision: str | None = None
    is_active: bool | None = None


class QualityProcedure(BaseDocument):
    """품질 절차 문서."""

    procedure_name: str = ""
    description: str = ""
    process_owner: str = ""
    revision: str = "1.0"
    is_active: bool = True
