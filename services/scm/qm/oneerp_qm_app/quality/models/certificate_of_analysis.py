"""분석 성적서(CertificateOfAnalysis) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CertificateOfAnalysisCreate(BaseModel):
    """분석 성적서 생성 요청 스키마."""

    item_code: str
    batch_no: str = ""
    test_date: date | None = None
    test_results: str = ""
    is_passed: bool = True
    issued_by: str = ""


class CertificateOfAnalysisUpdate(BaseModel):
    """분석 성적서 수정 요청 스키마."""

    item_code: str | None = None
    batch_no: str | None = None
    test_date: date | None = None
    test_results: str | None = None
    is_passed: bool | None = None
    issued_by: str | None = None


class CertificateOfAnalysis(BaseDocument):
    """분석 성적서 문서."""

    item_code: str = ""
    batch_no: str = ""
    test_date: date | None = None
    test_results: str = ""
    is_passed: bool = True
    issued_by: str = ""
