"""바코드 설정(BarcodeConfiguration) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class BarcodeConfigurationCreate(BaseModel):
    """바코드 설정 생성 요청 스키마."""

    barcode_type: str
    prefix: str = ""
    length: int = 13
    is_active: bool = True


class BarcodeConfigurationUpdate(BaseModel):
    """바코드 설정 수정 요청 스키마."""

    barcode_type: str | None = None
    prefix: str | None = None
    length: int | None = None
    is_active: bool | None = None


class BarcodeConfiguration(BaseDocument):
    """바코드 설정 문서."""

    barcode_type: str = ""
    prefix: str = ""
    length: int = 13
    is_active: bool = True
