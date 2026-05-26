"""바코드 설정(BarcodeConfiguration) 문서 모델."""

from __future__ import annotations

from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class BarcodeConfigurationCreate(BaseModel):
    """바코드 설정 생성 요청 스키마."""

    barcode_type: str
    prefix: str = ""
    ai_codes: list[dict[str, Any]] = []
    label_template: str = ""
    printer_config: dict[str, Any] = {}
    auto_generate: bool = False


class BarcodeConfigurationUpdate(BaseModel):
    """바코드 설정 수정 요청 스키마."""

    barcode_type: str | None = None
    prefix: str | None = None
    ai_codes: list[dict[str, Any]] | None = None
    label_template: str | None = None
    printer_config: dict[str, Any] | None = None
    auto_generate: bool | None = None


class BarcodeConfiguration(BaseDocument):
    """바코드 설정 문서."""

    barcode_type: str = ""
    prefix: str = ""
    ai_codes: list[dict[str, Any]] = []
    label_template: str = ""
    printer_config: dict[str, Any] = {}
    auto_generate: bool = False
