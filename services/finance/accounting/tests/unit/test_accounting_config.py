"""회계 서비스 전용 설정(AccountingSettings) 단위 테스트."""

from __future__ import annotations

from oneerp_accounting_app.config import AccountingSettings, get_accounting_settings
from oneerp_core.config import CoreSettings


def test_accounting_settings_inherits_core() -> None:
    """AccountingSettings는 CoreSettings를 상속한다."""
    assert issubclass(AccountingSettings, CoreSettings)


def test_accounting_settings_default_service_name() -> None:
    """기본 service_name은 'accounting'이다."""
    settings = AccountingSettings()
    assert settings.service_name == "accounting"


def test_accounting_settings_has_barobill_fields() -> None:
    """바로빌 API 설정 필드가 존재한다."""
    settings = AccountingSettings()
    assert settings.barobill_api_url == ""
    assert settings.barobill_api_key == ""


def test_accounting_settings_has_openbanking_fields() -> None:
    """오픈뱅킹 API 설정 필드가 존재한다."""
    settings = AccountingSettings()
    assert settings.openbanking_api_url == ""
    assert settings.openbanking_client_id == ""
    assert settings.openbanking_client_secret == ""


def test_accounting_settings_has_codef_fields() -> None:
    """CODEF API 설정 필드가 존재한다."""
    settings = AccountingSettings()
    assert settings.codef_api_url == ""
    assert settings.codef_api_key == ""
    assert settings.codef_api_secret == ""


def test_core_settings_does_not_have_accounting_fields() -> None:
    """CoreSettings에는 accounting 전용 필드가 없다."""
    core = CoreSettings()
    assert not hasattr(core, "barobill_api_url")
    assert not hasattr(core, "openbanking_api_url")
    assert not hasattr(core, "codef_api_url")


def test_get_accounting_settings_returns_singleton() -> None:
    """get_accounting_settings는 동일 인스턴스를 반환한다 (lru_cache)."""
    get_accounting_settings.cache_clear()
    s1 = get_accounting_settings()
    s2 = get_accounting_settings()
    assert s1 is s2
    get_accounting_settings.cache_clear()
