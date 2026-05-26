"""통화(Currency) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CurrencyCreate(BaseModel):
    """통화 생성 요청 스키마."""

    currency_code: str
    currency_name: str = ""
    symbol: str = ""
    fraction: str = ""
    fraction_units: int = 100
    is_enabled: bool = True


class CurrencyUpdate(BaseModel):
    """통화 수정 요청 스키마."""

    currency_code: str | None = None
    currency_name: str | None = None
    symbol: str | None = None
    fraction: str | None = None
    fraction_units: int | None = None
    is_enabled: bool | None = None


class Currency(BaseDocument):
    """통화 문서 — Setup 통화 마스터.

    naming prefix: CUR
    """

    currency_code: str = Field(default="", description="통화 코드")
    currency_name: str = Field(default="", description="통화명")
    symbol: str = Field(default="", description="통화 기호")
    fraction: str = Field(default="", description="보조 단위명")
    fraction_units: int = Field(default=100, description="보조 단위 환산 비율")
    is_enabled: bool = Field(default=True, description="활성 여부")
