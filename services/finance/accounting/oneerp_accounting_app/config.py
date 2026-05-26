"""회계(Accounting) 서비스 전용 설정.

바로빌(전자세금계산서), 오픈뱅킹, CODEF(4대보험) API 설정을
CoreSettings에서 분리하여 accounting 서비스에서만 로드한다.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from oneerp_core.config import CoreSettings


class AccountingSettings(CoreSettings):
    """회계 서비스 전용 설정 — CoreSettings를 상속한다."""

    service_name: str = "accounting"

    # 바로빌 전자세금계산서 API 설정
    barobill_api_url: str = ""
    barobill_api_key: str = ""

    # 금융결제원 오픈뱅킹 API 설정
    openbanking_api_url: str = ""
    openbanking_client_id: str = ""
    openbanking_client_secret: str = ""

    # CODEF 4대보험 API 설정
    codef_api_url: str = ""
    codef_api_key: str = ""
    codef_api_secret: str = ""


@lru_cache(maxsize=1)
def get_accounting_settings() -> AccountingSettings:
    """AccountingSettings 싱글턴을 반환한다 (lru_cache로 .env 재읽기 방지)."""
    return AccountingSettings()


# DI 타입 별칭
AccountingSettingsDep = Annotated[AccountingSettings, Depends(get_accounting_settings)]
