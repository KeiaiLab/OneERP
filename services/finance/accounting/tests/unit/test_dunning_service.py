"""독촉 서비스(DunningService) 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 테스트 전체 기간 동안 모킹한다."""
    with patch(
        "oneerp_accounting_app.services.dunning_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """DunningService와 모킹된 Repository를 반환한다."""
    with patch("oneerp_accounting_app.services.dunning_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.dunning_service import DunningService

        service = DunningService(tenant_id="test-tenant")

    return service, repos["dunnings"], repos["accounts_receivable"]


class Test독촉단계계산:
    """calculate_dunning_level 정적 메서드 테스트."""

    def test_30일미만_독촉없음(self) -> None:
        from oneerp_accounting_app.services.dunning_service import DunningService

        assert DunningService.calculate_dunning_level(29) == 0

    def test_30일_1단계(self) -> None:
        from oneerp_accounting_app.services.dunning_service import DunningService

        assert DunningService.calculate_dunning_level(30) == 1

    def test_60일_2단계(self) -> None:
        from oneerp_accounting_app.services.dunning_service import DunningService

        assert DunningService.calculate_dunning_level(60) == 2

    def test_90일_3단계(self) -> None:
        from oneerp_accounting_app.services.dunning_service import DunningService

        assert DunningService.calculate_dunning_level(90) == 3

    def test_120일_여전히_3단계(self) -> None:
        from oneerp_accounting_app.services.dunning_service import DunningService

        assert DunningService.calculate_dunning_level(120) == 3


class Test독촉수수료계산:
    """calculate_dunning_fee 정적 메서드 테스트."""

    def test_1단계_1퍼센트(self) -> None:
        from oneerp_accounting_app.services.dunning_service import DunningService

        assert DunningService.calculate_dunning_fee(100000, 1) == 1000.0

    def test_2단계_2퍼센트(self) -> None:
        from oneerp_accounting_app.services.dunning_service import DunningService

        assert DunningService.calculate_dunning_fee(100000, 2) == 2000.0

    def test_3단계_5퍼센트(self) -> None:
        from oneerp_accounting_app.services.dunning_service import DunningService

        assert DunningService.calculate_dunning_fee(100000, 3) == 5000.0


class Test독촉장일괄생성:
    """generate_dunnings 테스트."""

    def test_연체고객_독촉장생성(self) -> None:
        """30일 이상 연체 고객에 대해 독촉장이 생성된다."""
        service, dun_repo, ar_repo = _make_service()
        ar_repo.find_many.return_value = [
            {
                "_id": "AREC-001",
                "customer": "CUST-001",
                "outstanding_amount": 50000,
                "due_date": "2025-12-15",  # 95일 연체 (기준일: 2026-03-20)
                "invoice_id": "SI-001",
            },
        ]
        # 기존 독촉장 없음
        dun_repo.find_many.return_value = []

        result = service.generate_dunnings(as_of_date=date(2026, 3, 20))

        assert result["created_count"] == 1
        dunning = result["dunnings"][0]
        assert dunning["customer"] == "CUST-001"
        assert dunning["dunning_level"] == 3  # 95일 → 3단계
        assert dunning["dunning_fee"] == 2500.0  # 50000 x 5%
        assert dunning["outstanding_amount"] == 50000
        dun_repo.insert.assert_called_once()

    def test_연체_아닌_고객_제외(self) -> None:
        """만기 전 고객은 독촉 대상에서 제외된다."""
        service, dun_repo, ar_repo = _make_service()
        ar_repo.find_many.return_value = [
            {
                "_id": "AREC-001",
                "customer": "CUST-001",
                "outstanding_amount": 10000,
                "due_date": "2026-04-01",  # 아직 만기 전
                "invoice_id": "SI-001",
            },
        ]

        result = service.generate_dunnings(as_of_date=date(2026, 3, 20))

        assert result["created_count"] == 0
        dun_repo.insert.assert_not_called()

    def test_이미_독촉장_존재시_중복_미생성(self) -> None:
        """같은 고객/단계의 독촉장이 있으면 중복 생성하지 않는다."""
        service, dun_repo, ar_repo = _make_service()
        ar_repo.find_many.return_value = [
            {
                "_id": "AREC-001",
                "customer": "CUST-001",
                "outstanding_amount": 30000,
                "due_date": "2026-01-01",  # 78일 연체
                "invoice_id": "SI-001",
            },
        ]
        # 이미 2단계 독촉장 존재
        dun_repo.find_many.return_value = [{"_id": "DUN-001"}]

        result = service.generate_dunnings(as_of_date=date(2026, 3, 20))

        assert result["created_count"] == 0

    def test_복수고객_독촉장(self) -> None:
        """여러 고객에 대해 각각 독촉장이 생성된다."""
        service, dun_repo, ar_repo = _make_service()
        ar_repo.find_many.return_value = [
            {
                "_id": "AREC-001",
                "customer": "CUST-001",
                "outstanding_amount": 10000,
                "due_date": "2026-02-01",  # 47일 연체
                "invoice_id": "SI-001",
            },
            {
                "_id": "AREC-002",
                "customer": "CUST-002",
                "outstanding_amount": 20000,
                "due_date": "2025-12-01",  # 109일 연체
                "invoice_id": "SI-002",
            },
        ]
        dun_repo.find_many.return_value = []

        result = service.generate_dunnings(as_of_date=date(2026, 3, 20))

        assert result["created_count"] == 2
        customers = {d["customer"] for d in result["dunnings"]}
        assert customers == {"CUST-001", "CUST-002"}

    def test_잔액0원_제외(self) -> None:
        """잔액이 0원이면 독촉 대상에서 제외된다."""
        service, _dun_repo, ar_repo = _make_service()
        ar_repo.find_many.return_value = [
            {
                "_id": "AREC-001",
                "customer": "CUST-001",
                "outstanding_amount": 0,
                "due_date": "2025-12-01",
                "invoice_id": "SI-001",
            },
        ]

        result = service.generate_dunnings(as_of_date=date(2026, 3, 20))

        assert result["created_count"] == 0

    def test_동일고객_복수미수금_합산(self) -> None:
        """같은 고객의 여러 미수금은 합산하여 1건의 독촉장을 생성한다."""
        service, dun_repo, ar_repo = _make_service()
        ar_repo.find_many.return_value = [
            {
                "_id": "AREC-001",
                "customer": "CUST-001",
                "outstanding_amount": 10000,
                "due_date": "2026-02-01",
                "invoice_id": "SI-001",
            },
            {
                "_id": "AREC-002",
                "customer": "CUST-001",
                "outstanding_amount": 20000,
                "due_date": "2026-01-15",  # 더 오래된 연체
                "invoice_id": "SI-002",
            },
        ]
        dun_repo.find_many.return_value = []

        result = service.generate_dunnings(as_of_date=date(2026, 3, 20))

        assert result["created_count"] == 1
        dunning = result["dunnings"][0]
        assert dunning["outstanding_amount"] == 30000  # 합산
