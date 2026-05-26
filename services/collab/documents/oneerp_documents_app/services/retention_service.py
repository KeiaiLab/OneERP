"""보존 정책 서비스 — 보존 만료일 계산 및 만료 문서 처리.

BR-DOC-003: 보존 정책 자동 적용.
BR-DOC-011: 보존 기간 내 삭제 금지.
BR-DOC-012: 폐기 결재 필수.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from dateutil.relativedelta import relativedelta
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class RetentionService:
    """보존 정책 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._rp_repo = Repository("retention_policies", tenant_id=tenant_id)
        self._doc_repo = Repository("documents", tenant_id=tenant_id)

    def calculate_retention_until(
        self,
        policy_id: str,
        base_date: datetime | None = None,
    ) -> datetime | None:
        """보존 만료일을 계산한다.

        수식: retention_until = base_date + relativedelta(years, months)
        """
        policy = self._rp_repo.find_by_id(policy_id)
        if not policy:
            return None

        if not base_date:
            base_date = datetime.now(tz=UTC)

        years = policy.get("retention_years", 0)
        months = policy.get("retention_months", 0)

        return base_date + relativedelta(years=years, months=months)

    def find_expired_documents(self) -> list[dict[str, Any]]:
        """보존 기간이 만료된 문서를 조회한다."""
        now = datetime.now(tz=UTC)
        return self._doc_repo.find_many(
            {
                "retention_until": {"$lte": now},
                "status": {"$in": ["published", "archived"]},
                "is_deleted": False,
            },
            limit=1000,
        )

    def is_under_retention(self, document_id: str) -> bool:
        """문서가 보존 기간 내인지 확인한다."""
        doc = self._doc_repo.find_by_id(document_id)
        if not doc:
            return False

        retention_until = doc.get("retention_until")
        if not retention_until:
            return False

        return retention_until > datetime.now(tz=UTC)
