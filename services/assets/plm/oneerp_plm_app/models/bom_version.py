"""BOM 버전(BOMVersion) 문서 모델.

제품의 자재 명세서(BOM)를 버전 관리한다.
E-BOM(엔지니어링)과 M-BOM(제조) 유형을 분리하여 관리한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class BOMType(StrEnum):
    """BOM 유형."""

    EBOM = "ebom"
    MBOM = "mbom"


class BOMVersionStatus(StrEnum):
    """BOM 버전 상태."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    RELEASED = "released"
    SUPERSEDED = "superseded"
    OBSOLETE = "obsolete"


class BOMItem(BaseModel):
    """BOM 구성 품목 — 임베디드 모델."""

    line_no: int = Field(default=0, description="행 번호")
    item_code: str = Field(description="구성 품목 코드")
    item_name: str = Field(description="구성 품목명")
    quantity: float = Field(description="소요 수량")
    uom: str = Field(default="EA", description="단위")
    unit_cost: Decimal = Field(default=Decimal(0), description="단가")
    find_number: str | None = Field(default=None, description="도면 내 위치 번호")
    reference_designator: str | None = Field(default=None, description="회로 참조 부호")
    is_phantom: bool = Field(default=False, description="팬텀 BOM 여부")
    substitute_group: str | None = Field(default=None, description="대체 부품 그룹 ID")
    child_bom_id: str | None = Field(default=None, description="하위 BOM 참조")
    notes: str = Field(default="", description="비고")


class BOMItemCreate(BaseModel):
    """BOM 구성 품목 생성 스키마."""

    item_code: str
    item_name: str
    quantity: float
    uom: str = "EA"
    unit_cost: Decimal = Decimal(0)
    find_number: str | None = None
    reference_designator: str | None = None
    is_phantom: bool = False
    substitute_group: str | None = None
    child_bom_id: str | None = None
    notes: str = ""


class BOMVersionCreate(BaseModel):
    """BOM 버전 생성 요청 스키마."""

    product_id: str
    bom_type: BOMType
    base_quantity: float = 1.0
    items: list[BOMItemCreate] = Field(default_factory=list)
    eco_id: str | None = None
    parent_version_id: str | None = None
    source_ebom_id: str | None = None
    effectivity_start: date | None = None
    effectivity_end: date | None = None
    notes: str = ""


class BOMVersionUpdate(BaseModel):
    """BOM 버전 수정 요청 스키마."""

    base_quantity: float | None = None
    items: list[BOMItemCreate] | None = None
    effectivity_start: date | None = None
    effectivity_end: date | None = None
    notes: str | None = None


class BOMVersion(BaseDocument):
    """BOM 버전 문서 — 제품 BOM을 버전 관리.

    naming prefix: BV
    """

    product_id: str = Field(default="", description="제품 참조")
    bom_type: BOMType = Field(default=BOMType.EBOM, description="BOM 유형")
    version_major: int = Field(default=1, description="메이저 버전")
    version_minor: int = Field(default=0, description="마이너 버전")
    version_label: str = Field(default="1.0", description="버전 표시")
    status: BOMVersionStatus = Field(default=BOMVersionStatus.DRAFT, description="BOM 상태")
    base_quantity: float = Field(default=1.0, description="기준 생산 수량")
    items: list[BOMItem] = Field(default_factory=list, description="BOM 구성 품목 목록")
    eco_id: str | None = Field(default=None, description="관련 ECO")
    parent_version_id: str | None = Field(default=None, description="이전 버전")
    source_ebom_id: str | None = Field(default=None, description="M-BOM의 원본 E-BOM")
    effectivity_start: date | None = Field(default=None, description="유효 시작일")
    effectivity_end: date | None = Field(default=None, description="��효 종료일")
    total_cost: Decimal | None = Field(default=None, description="총 원가")
    notes: str = Field(default="", description="변경 메모")
    released_by: str | None = Field(default=None, description="릴리즈 승인자")
    released_at: datetime | None = Field(default=None, description="릴리즈 시각")
    deleted_at: str | None = Field(default=None, description="삭제 시각")
