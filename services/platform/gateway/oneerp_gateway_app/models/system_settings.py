"""시스템설정(SystemSettings) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SystemSettingsCreate(BaseModel):
    """시스템설정 생성 요청 스키마."""

    setting_key: str
    setting_value: str = ""
    description: str = ""


class SystemSettingsUpdate(BaseModel):
    """시스템설정 수정 요청 스키마."""

    setting_key: str | None = None
    setting_value: str | None = None
    description: str | None = None


class SystemSettings(BaseDocument):
    """시스템설정 문서 — Setup 시스템설정 마스터.

    naming prefix: SYSS
    """

    setting_key: str = ""
    setting_value: str = ""
    description: str = ""
