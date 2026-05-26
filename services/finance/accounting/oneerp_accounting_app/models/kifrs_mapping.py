"""K-IFRS 매핑(KIFRS Mapping) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class KIFRSMappingCreate(BaseModel):
    """K-IFRS 매핑 생성 요청 스키마."""

    k_ifrs_account: str
    local_account: str
    mapping_type: str
    effective_date: date | None = None
    is_active: bool = True


class KIFRSMappingUpdate(BaseModel):
    """K-IFRS 매핑 수정 요청 스키마."""

    k_ifrs_account: str | None = None
    local_account: str | None = None
    mapping_type: str | None = None
    effective_date: date | None = None
    is_active: bool | None = None


class KIFRSMapping(BaseDocument):
    """K-IFRS 매핑 문서 — 한국채택국제회계기준 계정 매핑.

    naming prefix: KIFRS
    """

    k_ifrs_account: str = ""
    local_account: str = ""
    mapping_type: str = ""
    effective_date: date | None = None
    is_active: bool = True
