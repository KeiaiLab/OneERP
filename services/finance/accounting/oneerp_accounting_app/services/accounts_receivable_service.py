"""매출채권(Accounts Receivable) 서비스 계층 — route와 Repository 경계(OE002).

route는 Repository를 직접 인스턴스화하지 않고, 본 모듈의 팩토리를 통해
Repository에 접근한다. 비즈니스 로직(집계/필터/독촉 인덱싱)은 route에 남아있지만,
데이터 접근 지점은 이 모듈로 일원화된다.
"""

from __future__ import annotations

from oneerp_core.repository import Repository

_COLLECTION = "accounts_receivable"
_DUNNING_COLLECTION = "dunnings"


def get_receivable_repo(tenant_id: str) -> Repository:
    """매출채권 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def get_dunning_repo(tenant_id: str) -> Repository:
    """독촉장 Repository를 반환한다."""
    return Repository(_DUNNING_COLLECTION, tenant_id=tenant_id)
