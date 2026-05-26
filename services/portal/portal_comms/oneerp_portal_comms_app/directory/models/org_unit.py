"""조직 단위(OrgUnit) 마스터 모델 — 부서/팀/실/본부 등.

BR-DIR-003: 조직 단위는 반드시 상위 조직(org_id)에 소속되어야 한다.
BR-DIR-004: 조직 단위 코드는 동일 조직 내에서 고유해야 한다.
BR-DIR-005: 조직 단위는 계층 구조(parent_unit_id)를 가질 수 있다.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class UnitType(StrEnum):
    """조직 단위 유형."""

    DIVISION = "division"  # 본부
    DEPARTMENT = "department"  # 부서
    TEAM = "team"  # 팀
    GROUP = "group"  # 그룹/파트
    CENTER = "center"  # 센터
    BRANCH = "branch"  # 지사/지점


class UnitStatus(StrEnum):
    """조직 단위 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MERGED = "merged"


class OrgUnitCreate(BaseModel):
    """조직 단위 생성 요청 스키마.

    BR-DIR-003: org_id는 필수이다.
    BR-DIR-004: unit_code는 필수이다.
    """

    org_id: str
    unit_code: str
    unit_name: str
    unit_name_en: str = ""
    unit_type: UnitType = UnitType.DEPARTMENT
    parent_unit_id: str | None = None
    head_employee_id: str | None = None
    cost_center: str = ""
    sort_order: int = 0

    @field_validator("org_id")
    @classmethod
    def org_id_required(cls, v: str) -> str:
        """BR-DIR-003: 소속 조직은 필수이다."""
        if not v.strip():
            msg = "ERR-DIR-003: 소속 조직 ID는 필수입니다"
            raise ValueError(msg)
        return v.strip()

    @field_validator("unit_code")
    @classmethod
    def unit_code_required(cls, v: str) -> str:
        """BR-DIR-004: 조직 단위 코드는 필수이다."""
        if not v.strip():
            msg = "ERR-DIR-004: 조직 단위 코드는 필수입니다"
            raise ValueError(msg)
        return v.strip()

    @field_validator("unit_name")
    @classmethod
    def unit_name_required(cls, v: str) -> str:
        """BR-DIR-004: 조직 단위 명칭은 필수이다."""
        if not v.strip():
            msg = "ERR-DIR-005: 조직 단위 명칭은 필수입니다"
            raise ValueError(msg)
        return v.strip()


class OrgUnitUpdate(BaseModel):
    """조직 단위 수정 요청 스키마."""

    unit_code: str | None = None
    unit_name: str | None = None
    unit_name_en: str | None = None
    unit_type: UnitType | None = None
    parent_unit_id: str | None = None
    head_employee_id: str | None = None
    cost_center: str | None = None
    sort_order: int | None = None
    status: UnitStatus | None = None


class OrgUnit(BaseDocument):
    """조직 단위 마스터 — 부서/팀/실/본부 등 계층형 단위.

    naming prefix: UNIT
    BR-DIR-003, BR-DIR-004, BR-DIR-005
    """

    org_id: str = Field(default="", description="소속 조직 ID")
    unit_code: str = Field(default="", description="조직 단위 코드")
    unit_name: str = Field(default="", description="조직 단위 명칭")
    unit_name_en: str = Field(default="", description="조직 단위 영문 명칭")
    unit_type: UnitType = Field(default=UnitType.DEPARTMENT, description="단위 유형")
    parent_unit_id: str | None = Field(default=None, description="상위 조직 단위 ID")
    head_employee_id: str | None = Field(default=None, description="조직장 직원 ID")
    cost_center: str = Field(default="", description="코스트센터")
    sort_order: int = Field(default=0, description="정렬 순서")
    status: UnitStatus = Field(default=UnitStatus.ACTIVE, description="상태")
