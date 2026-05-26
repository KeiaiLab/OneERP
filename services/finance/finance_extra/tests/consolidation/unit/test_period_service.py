"""연결 기간 서비스(PeriodService) 단위 테스트.

BR-CSL-008: 이전 기간 마감 후 개시
ERR-CSL-031: 이전 기간 미마감
ERR-CSL-032: 이미 개시된 기간
ERR-CSL-037: 마감 기간 수정 차단
ERR-CSL-039: closed 외 재개 불가
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_finance_extra_app.consolidation.models.consolidation_period import PeriodStatus


def _make_service():
    """PeriodService와 모킹된 Repository들을 반환한다."""
    with patch(
        "oneerp_finance_extra_app.consolidation.services.period_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_finance_extra_app.consolidation.services.period_service import PeriodService

        service = PeriodService(tenant_id="test-tenant")

    return service, repos


def _not_started_period(period_id: str = "CPER-001") -> dict:
    """미시작 기간 문서를 반환한다."""
    return {
        "_id": period_id,
        "period_name": "2026-03",
        "status": PeriodStatus.NOT_STARTED,
        "total_entities": 0,
    }


def _review_period(period_id: str = "CPER-001") -> dict:
    """검토 중 기간 문서를 반환한다."""
    return {
        "_id": period_id,
        "period_name": "2026-03",
        "status": PeriodStatus.REVIEW,
    }


def _closed_period(period_id: str = "CPER-001") -> dict:
    """마감 기간 문서를 반환한다."""
    return {
        "_id": period_id,
        "period_name": "2026-03",
        "status": PeriodStatus.CLOSED,
    }


class Test상태전이검증:
    """상태 전이 유효성 검증 테스트."""

    def test_not_started에서_open(self) -> None:
        service, _ = _make_service()
        assert service.validate_transition(PeriodStatus.NOT_STARTED, PeriodStatus.OPEN) is True

    def test_open에서_in_progress(self) -> None:
        service, _ = _make_service()
        assert service.validate_transition(PeriodStatus.OPEN, PeriodStatus.IN_PROGRESS) is True

    def test_closed에서_reopened(self) -> None:
        service, _ = _make_service()
        assert service.validate_transition(PeriodStatus.CLOSED, PeriodStatus.REOPENED) is True

    def test_잘못된_전이_not_started에서_closed(self) -> None:
        service, _ = _make_service()
        assert service.validate_transition(PeriodStatus.NOT_STARTED, PeriodStatus.CLOSED) is False


class Test기간개시:
    """기간 개시 테스트."""

    def test_정상개시(self) -> None:
        """not_started → open 정상 전환."""
        service, repos = _make_service()
        repos["consolidation_periods"].find_by_id.return_value = _not_started_period()
        repos["consolidation_periods"].find_many.return_value = [_not_started_period()]
        repos["consolidation_entities"].find_many.return_value = [
            {"_id": "CENT-001", "entity_name": "원얼프 주식회사", "status": "active"},
            {"_id": "CENT-002", "entity_name": "일본법인", "status": "active"},
        ]

        result = service.open_period("CPER-001", user_id="user-001")

        assert result["status"] == PeriodStatus.OPEN
        assert result["total_entities"] == 2
        repos["consolidation_periods"].update_by_id.assert_called_once()

    def test_이미개시된_기간(self) -> None:
        """이미 open 상태면 ERR-CSL-032."""
        service, repos = _make_service()
        repos["consolidation_periods"].find_by_id.return_value = {
            "_id": "CPER-001",
            "status": PeriodStatus.OPEN,
        }

        with pytest.raises(OneERPError) as exc_info:
            service.open_period("CPER-001")

        assert exc_info.value.error == "ERR-CSL-032"

    def test_이전기간_미마감(self) -> None:
        """이전 기간이 미마감이면 ERR-CSL-031."""
        service, repos = _make_service()
        repos["consolidation_periods"].find_by_id.return_value = _not_started_period("CPER-002")
        repos["consolidation_periods"].find_many.return_value = [
            _not_started_period("CPER-002"),
            {
                "_id": "CPER-001",
                "period_name": "2026-02",
                "status": PeriodStatus.REVIEW,  # 미마감
            },
        ]

        with pytest.raises(OneERPError) as exc_info:
            service.open_period("CPER-002")

        assert exc_info.value.error == "ERR-CSL-031"


class Test기간마감:
    """기간 마감 테스트."""

    def test_정상마감(self) -> None:
        """review → closed 정상 전환."""
        service, repos = _make_service()
        repos["consolidation_periods"].find_by_id.return_value = _review_period()

        result = service.close_period("CPER-001", user_id="user-001")

        assert result["status"] == PeriodStatus.CLOSED
        repos["consolidation_periods"].update_by_id.assert_called_once()

    def test_review_아닌_상태에서_마감(self) -> None:
        """review가 아니면 ERR-CSL-037."""
        service, repos = _make_service()
        repos["consolidation_periods"].find_by_id.return_value = {
            "_id": "CPER-001",
            "status": PeriodStatus.IN_PROGRESS,
        }

        with pytest.raises(OneERPError) as exc_info:
            service.close_period("CPER-001")

        assert exc_info.value.error == "ERR-CSL-037"


class Test기간재개:
    """기간 재개 테스트."""

    def test_정상재개(self) -> None:
        """closed → reopened 정상 전환, 보고서 superseded."""
        service, repos = _make_service()
        repos["consolidation_periods"].find_by_id.return_value = _closed_period()
        repos["consolidated_reports"].find_many.return_value = [
            {"_id": "CRPT-001", "status": "final"},
            {"_id": "CRPT-002", "status": "final"},
        ]

        result = service.reopen_period("CPER-001")

        assert result["status"] == PeriodStatus.REOPENED
        # 보고서 2건 superseded
        assert repos["consolidated_reports"].update_by_id.call_count == 2

    def test_미마감_상태에서_재개(self) -> None:
        """closed가 아니면 ERR-CSL-039."""
        service, repos = _make_service()
        repos["consolidation_periods"].find_by_id.return_value = {
            "_id": "CPER-001",
            "status": PeriodStatus.REVIEW,
        }

        with pytest.raises(OneERPError) as exc_info:
            service.reopen_period("CPER-001")

        assert exc_info.value.error == "ERR-CSL-039"

    def test_기간못찾으면_404(self) -> None:
        """존재하지 않는 기간이면 404."""
        service, repos = _make_service()
        repos["consolidation_periods"].find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.reopen_period("CPER-NONE")

        assert exc_info.value.status_code == 404
