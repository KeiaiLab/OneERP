"""HR 서비스 전용 설정.

LDAP/SCIM(SSO 연계), 급여 웹훅 등 HR 고유 환경변수를 CoreSettings 에서 분리해
hr 서비스에서만 로드한다. accounting 서비스 `AccountingSettings` 패턴을 미러한다.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from oneerp_core.config import CoreSettings


class HRSettings(CoreSettings):
    """HR 서비스 전용 설정 — CoreSettings 를 상속한다."""

    service_name: str = "hr"

    # LDAP/SCIM 연계 (디렉터리 동기화)
    hr_ldap_url: str = ""
    hr_scim_enabled: bool = False

    # 외부 급여 시스템 연동 웹훅
    hr_payroll_webhook: str = ""


@lru_cache(maxsize=1)
def get_hr_settings() -> HRSettings:
    """HRSettings 싱글턴을 반환한다 (lru_cache 로 .env 재읽기 방지)."""
    return HRSettings()


# DI 타입 별칭 — FastAPI Depends 주입용
HRSettingsDep = Annotated[HRSettings, Depends(get_hr_settings)]
