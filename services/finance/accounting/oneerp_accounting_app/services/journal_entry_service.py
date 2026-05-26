"""분개전표 서비스 계층 — route와 Repository 사이의 경계(OE002).

route는 Repository를 직접 인스턴스화하지 않고, 본 서비스의 팩토리를 통해
접근한다. 비즈니스 로직(승인/제출/이벤트 발행 등)은 route에 남아있지만,
데이터 접근 지점은 이 모듈로 일원화된다.
"""

from __future__ import annotations

from oneerp_core.repository import Repository

_JOURNAL_COLLECTION = "journal_entries"
_TEMPLATE_COLLECTION = "journal_entry_templates"
_PERIOD_COLLECTION = "accounting_periods"


def get_journal_entry_repo(tenant_id: str) -> Repository:
    """분개전표 Repository를 반환한다."""
    return Repository(_JOURNAL_COLLECTION, tenant_id=tenant_id)


def get_template_repo(tenant_id: str) -> Repository:
    """반복 전표 템플릿 Repository를 반환한다."""
    return Repository(_TEMPLATE_COLLECTION, tenant_id=tenant_id)


def get_accounting_period_repo(tenant_id: str) -> Repository:
    """회계기간 Repository를 반환한다 (마감 기간 확인용)."""
    return Repository(_PERIOD_COLLECTION, tenant_id=tenant_id)
