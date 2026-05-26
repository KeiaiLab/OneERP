"""HRSettings 단위 테스트 — CoreSettings 상속 + lru_cache DI 검증."""

from __future__ import annotations

from oneerp_hr_app.config import HRSettings, get_hr_settings


def test_hr_settings_defaults() -> None:
    """HRSettings 기본값 — SCIM 비활성, LDAP URL 빈 값 또는 ldaps:// 접두."""
    s = HRSettings()
    assert s.hr_scim_enabled is False
    assert s.hr_ldap_url == "" or s.hr_ldap_url.startswith("ldaps://")
    assert s.hr_payroll_webhook == ""


def test_get_hr_settings_is_cached() -> None:
    """get_hr_settings 는 lru_cache 로 동일 인스턴스를 반환한다."""
    a = get_hr_settings()
    b = get_hr_settings()
    assert a is b
