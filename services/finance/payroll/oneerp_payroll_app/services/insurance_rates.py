"""4대보험 요율 설정 — 환경변수로 주입.

요율 하드코딩 금지 원칙에 따라 모든 요율은 환경변수로 오버라이드 가능하다.
기본값은 2026년 기준 요율이다.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class InsuranceRates(BaseSettings):
    """4대보험 요율 설정 — 환경변수로 주입."""

    model_config = SettingsConfigDict(env_prefix="ONEERP_INS_", extra="ignore")

    # 국민연금
    national_pension_rate: float = 0.045
    national_pension_cap: float = 5_530_000  # 상한 기준급여

    # 건강보험
    health_insurance_rate: float = 0.03545
    long_term_care_rate: float = 0.1281  # 건강보험 대비 비율

    # 고용보험
    employment_insurance_rate: float = 0.009

    # 산재보험
    industrial_accident_rate: float = 0.007

    # 적용 연도
    rates_year: int = 2026


@lru_cache(maxsize=1)
def get_insurance_rates() -> InsuranceRates:
    """InsuranceRates 싱글턴을 반환한다."""
    return InsuranceRates()
