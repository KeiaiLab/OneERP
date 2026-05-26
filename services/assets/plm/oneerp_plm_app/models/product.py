"""제품 마스터(Product) 문서 모델.

제품의 전체 수명주기를 추적하는 중앙 마스터 레코드.
제품 기본 정보, 분류, 속성, 수명주기 상태를 관리한다.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ProductType(StrEnum):
    """제품 유형."""

    FINISHED_GOOD = "finished_good"
    SEMI_FINISHED = "semi_finished"
    RAW_MATERIAL = "raw_material"
    ASSEMBLY = "assembly"
    COMPONENT = "component"


class LifecycleStatus(StrEnum):
    """제품 수명주기 상태."""

    CONCEPT = "concept"
    DESIGN = "design"
    PROTOTYPE = "prototype"
    PRE_PRODUCTION = "pre_production"
    PRODUCTION = "production"
    PHASE_OUT = "phase_out"
    END_OF_LIFE = "end_of_life"


# 수명주기 상태 전이 규칙
LIFECYCLE_TRANSITIONS: dict[LifecycleStatus, list[LifecycleStatus]] = {
    LifecycleStatus.CONCEPT: [LifecycleStatus.DESIGN],
    LifecycleStatus.DESIGN: [LifecycleStatus.PROTOTYPE, LifecycleStatus.CONCEPT],
    LifecycleStatus.PROTOTYPE: [LifecycleStatus.PRE_PRODUCTION, LifecycleStatus.DESIGN],
    LifecycleStatus.PRE_PRODUCTION: [LifecycleStatus.PRODUCTION, LifecycleStatus.PROTOTYPE],
    LifecycleStatus.PRODUCTION: [LifecycleStatus.PHASE_OUT],
    LifecycleStatus.PHASE_OUT: [LifecycleStatus.END_OF_LIFE, LifecycleStatus.PRODUCTION],
    LifecycleStatus.END_OF_LIFE: [],
}


class Dimensions(BaseModel):
    """치수 — 임베디드 모델."""

    width: float | None = Field(default=None, description="가로(mm)")
    height: float | None = Field(default=None, description="세로(mm)")
    depth: float | None = Field(default=None, description="높이(mm)")


class ProductAttribute(BaseModel):
    """커스텀 속성 — 임베디드 모델."""

    key: str = Field(description="속성 키")
    value: str = Field(description="속성 값")
    unit: str | None = Field(default=None, description="단위")


class ProductCreate(BaseModel):
    """제품 마스터 생성 요청 스키마."""

    product_code: str = Field(min_length=1, max_length=50)
    product_name: str = Field(min_length=1, max_length=200)
    product_type: ProductType = ProductType.FINISHED_GOOD
    category_id: str | None = None
    family_id: str | None = None
    description: str = ""
    uom: str = "EA"
    weight: float | None = None
    dimensions: Dimensions | None = None
    attributes: list[ProductAttribute] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None
    responsible_engineer: str | None = None


class ProductUpdate(BaseModel):
    """제품 마스터 수정 요청 스키마."""

    product_name: str | None = None
    product_type: ProductType | None = None
    category_id: str | None = None
    family_id: str | None = None
    description: str | None = None
    uom: str | None = None
    weight: float | None = None
    dimensions: Dimensions | None = None
    attributes: list[ProductAttribute] | None = None
    tags: list[str] | None = None
    thumbnail_url: str | None = None
    responsible_engineer: str | None = None


class Product(BaseDocument):
    """제품 마스터 문서 — 제품의 전체 수명주기를 추적.

    naming prefix: PRD
    """

    product_code: str = Field(default="", description="제품 코드")
    product_name: str = Field(default="", description="제품명")
    product_type: ProductType = Field(default=ProductType.FINISHED_GOOD, description="제품 유형")
    category_id: str | None = Field(default=None, description="제품 분류 ID")
    family_id: str | None = Field(default=None, description="제품 패밀리 ID")
    description: str = Field(default="", description="제품 설명")
    lifecycle_status: LifecycleStatus = Field(
        default=LifecycleStatus.CONCEPT, description="수명주기 상��"
    )
    item_code: str | None = Field(default=None, description="재고 품목 코드 연동")
    uom: str = Field(default="EA", description="기본 단위")
    weight: float | None = Field(default=None, description="중량(kg)")
    dimensions: Dimensions | None = Field(default=None, description="치수")
    attributes: list[ProductAttribute] = Field(default_factory=list, description="커스텀 속성")
    tags: list[str] = Field(default_factory=list, description="검색 태그")
    thumbnail_url: str | None = Field(default=None, description="제품 대표 이미지")
    active_ebom_id: str | None = Field(default=None, description="활성 E-BOM ID")
    active_mbom_id: str | None = Field(default=None, description="활성 M-BOM ID")
    responsible_engineer: str | None = Field(default=None, description="담당 설계 엔지니어 ID")
    deleted_at: str | None = Field(default=None, description="소프트 삭제 시각")
