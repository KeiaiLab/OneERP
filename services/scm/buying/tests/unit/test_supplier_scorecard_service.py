"""공급업체 평가 서비스(SupplierScorecardService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_buying_app.services.supplier_scorecard_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_buying_app.services.supplier_scorecard_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_buying_app.services.supplier_scorecard_service import SupplierScorecardService

        service = SupplierScorecardService(tenant_id="test-tenant")

    return (
        service,
        repos["supplier_scorecards"],
        repos["purchase_receipts"],
        repos["purchase_returns"],
        repos["purchase_orders"],
    )


class Test공급업체평가:
    """evaluate_supplier 테스트."""

    def test_정상_평가(self) -> None:
        """발주 2건, 입고 2건, 반품 0건 → 높은 점수."""
        service, ssc_repo, receipt_repo, return_repo, po_repo = _make_service()
        po_repo.find_many.return_value = [{"_id": "PO-001"}, {"_id": "PO-002"}]
        receipt_repo.find_many.return_value = [{"_id": "PRCP-001"}, {"_id": "PRCP-002"}]
        return_repo.find_many.return_value = []

        result = service.evaluate_supplier("SUP-001", "2026-Q1")

        assert result["scorecard_id"] == "SSC-001"
        assert result["total_score"] > 0
        # 납기: 2/2 = 100%, 품질: 2/2 = 100%, 가격: 70
        # 가중: 100*0.4 + 100*0.35 + 70*0.25 = 40 + 35 + 17.5 = 92.5
        assert result["total_score"] == 92.5
        ssc_repo.insert.assert_called_once()

    def test_반품_있으면_품질점수_감소(self) -> None:
        """반품이 있으면 품질 점수가 감소한다."""
        service, _ssc, receipt_repo, return_repo, po_repo = _make_service()
        po_repo.find_many.return_value = [{"_id": "PO-001"}]
        receipt_repo.find_many.return_value = [{"_id": "PRCP-001"}, {"_id": "PRCP-002"}]
        return_repo.find_many.return_value = [{"_id": "PRT-001"}]

        result = service.evaluate_supplier("SUP-001", "2026-Q1")

        # 품질: (2-1)/2 = 50%
        assert result["criteria"]["quality"]["score"] == 50.0

    def test_발주없으면_0점(self) -> None:
        """발주 이력이 없으면 모든 점수가 0."""
        service, _ssc, receipt_repo, return_repo, po_repo = _make_service()
        po_repo.find_many.return_value = []
        receipt_repo.find_many.return_value = []
        return_repo.find_many.return_value = []

        result = service.evaluate_supplier("SUP-001", "2026-Q1")

        assert result["total_score"] == 0.0
