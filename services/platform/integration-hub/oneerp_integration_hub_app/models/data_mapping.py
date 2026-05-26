"""데이터 매핑 모델 — 외부/내부 시스템 간 필드 매핑 규칙을 관리한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class FieldMapping(BaseModel):
    """개별 필드 매핑 규칙."""

    source_field: str = ""
    target_field: str = ""
    transform: str = ""  # direct/uppercase/lowercase/format/custom
    default_value: str = ""
    required: bool = False


class DataMappingCreate(BaseModel):
    """데이터 매핑 생성 요청 스키마."""

    mapping_name: str
    source_system: str = ""
    target_system: str = ""
    source_entity: str = ""
    target_entity: str = ""
    field_mappings: list[dict] = []
    description: str = ""


class DataMappingUpdate(BaseModel):
    """데이터 매핑 수정 요청 스키마."""

    mapping_name: str | None = None
    field_mappings: list[dict] | None = None
    description: str | None = None
    is_active: bool | None = None


class DataMapping(BaseDocument):
    """데이터 매핑 문서 — 시스템 간 필드 매핑 규칙을 저장한다."""

    mapping_name: str = ""
    source_system: str = ""
    target_system: str = ""
    source_entity: str = ""
    target_entity: str = ""
    field_mappings: list[dict] = []
    description: str = ""
    is_active: bool = True
