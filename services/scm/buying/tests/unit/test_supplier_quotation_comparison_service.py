"""공급업체 견적 종합 비교 서비스(SupplierQuotationComparisonService) 단위 테스트.

BR-BUY-NEW-021: 최저가뿐 아니라 납기/최소주문수량/결제조건을 종합한 공급사 추천.

기존 PurchaseProcessService.compare_quotations는 품목별 최저가만 추천한다.
이 서비스는 ERPNext/Odoo의 공급사 비교 모범 사례에 따라
"최저가(price)/납기(delivery_days)/MOQ/결제조건(payment_terms)"를
가중치 기반으로 점수화한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """SupplierQuotationComparisonService와 mock repo를 생성한다."""
    with patch(
        "oneerp_buying_app.services.supplier_quotation_comparison_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_buying_app.services.supplier_quotation_comparison_service import (
            SupplierQuotationComparisonService,
        )

        service = SupplierQuotationComparisonService(tenant_id="test-tenant")

    return service, repos["supplier_quotations"], repos["request_for_quotations"]


class Test종합비교_가격:
    """가격 점수 계산."""

    def test_최저가_공급사_가격점수_100(self) -> None:
        """세 개 견적 중 가장 낮은 단가의 공급사는 가격 점수 100점."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = [
            {
                "_id": "SQ-001",
                "supplier": "SUP-A",
                "delivery_days": 10,
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5000, "qty": 100}],
            },
            {
                "_id": "SQ-002",
                "supplier": "SUP-B",
                "delivery_days": 10,
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 4800, "qty": 100}],
            },
            {
                "_id": "SQ-003",
                "supplier": "SUP-C",
                "delivery_days": 10,
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5200, "qty": 100}],
            },
        ]

        result = service.compare_comprehensive(rfq_id="RFQ-001", item_code="ITEM-001")

        # SUP-B가 최저가이므로 가격 점수 100점
        scores = {s["supplier"]: s for s in result["scores"]}
        assert scores["SUP-B"]["price_score"] == 100.0
        # 최고가(SUP-C=5200)는 가격 점수가 가장 낮다
        assert scores["SUP-C"]["price_score"] < scores["SUP-A"]["price_score"]
        assert scores["SUP-C"]["price_score"] < scores["SUP-B"]["price_score"]


class Test종합비교_납기:
    """납기 점수 계산."""

    def test_최단납기_공급사_납기점수_100(self) -> None:
        """가장 짧은 납기의 공급사는 납기 점수 100점."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = [
            {
                "_id": "SQ-001",
                "supplier": "SUP-A",
                "delivery_days": 5,  # 최단
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5000, "qty": 100}],
            },
            {
                "_id": "SQ-002",
                "supplier": "SUP-B",
                "delivery_days": 20,
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5000, "qty": 100}],
            },
        ]

        result = service.compare_comprehensive(rfq_id="RFQ-001", item_code="ITEM-001")

        scores = {s["supplier"]: s for s in result["scores"]}
        assert scores["SUP-A"]["delivery_score"] == 100.0
        assert scores["SUP-B"]["delivery_score"] < 100.0


class Test종합비교_결제조건:
    """결제조건 점수 계산 (결제 유예가 길수록 유리)."""

    def test_결제_유예_긴_공급사_결제점수_100(self) -> None:
        """결제 유예가 가장 긴 공급사는 결제조건 점수 100점."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = [
            {
                "_id": "SQ-001",
                "supplier": "SUP-A",
                "delivery_days": 10,
                "payment_terms_days": 60,  # 60일 유예 (유리)
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5000, "qty": 100}],
            },
            {
                "_id": "SQ-002",
                "supplier": "SUP-B",
                "delivery_days": 10,
                "payment_terms_days": 0,  # 선금
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5000, "qty": 100}],
            },
        ]

        result = service.compare_comprehensive(rfq_id="RFQ-001", item_code="ITEM-001")

        scores = {s["supplier"]: s for s in result["scores"]}
        assert scores["SUP-A"]["payment_score"] == 100.0
        assert scores["SUP-B"]["payment_score"] < scores["SUP-A"]["payment_score"]


class Test종합비교_추천:
    """가중 총점 기반 추천."""

    def test_종합점수_최고_추천(self) -> None:
        """가격/납기/결제조건 종합 점수 최고의 공급사를 추천한다."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = [
            {
                "_id": "SQ-001",
                "supplier": "SUP-A",
                "delivery_days": 5,  # 최단 납기 (점수 100)
                "payment_terms_days": 60,  # 최장 결제 (점수 100)
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 4800, "qty": 100}],  # 최저가
            },
            {
                "_id": "SQ-002",
                "supplier": "SUP-B",
                "delivery_days": 20,
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5000, "qty": 100}],
            },
        ]

        result = service.compare_comprehensive(rfq_id="RFQ-001", item_code="ITEM-001")

        # SUP-A가 모든 항목에서 우세하므로 추천되어야 한다
        assert result["recommended"]["supplier"] == "SUP-A"
        assert result["recommended"]["total_score"] > 0

    def test_가중치_기본값_적용(self) -> None:
        """기본 가중치: 가격 50%, 납기 30%, 결제 20%."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = [
            {
                "_id": "SQ-001",
                "supplier": "SUP-A",
                "delivery_days": 10,
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5000, "qty": 100}],
            },
        ]

        result = service.compare_comprehensive(rfq_id="RFQ-001", item_code="ITEM-001")

        # 단일 공급사는 모든 항목 점수 100점
        score = result["scores"][0]
        assert score["total_score"] == 100.0


class Test종합비교_예외:
    """예외 케이스."""

    def test_견적_0건_빈결과(self) -> None:
        """견적이 없으면 빈 결과 반환."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = []

        result = service.compare_comprehensive(rfq_id="RFQ-001", item_code="ITEM-001")

        assert result["quotation_count"] == 0
        assert result["scores"] == []
        assert result["recommended"] is None

    def test_품목미매칭_에러(self) -> None:
        """지정 품목이 견적에 없으면 422 에러."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = [
            {
                "_id": "SQ-001",
                "supplier": "SUP-A",
                "delivery_days": 10,
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-999", "rate": 5000, "qty": 100}],
            },
        ]

        with pytest.raises(OneERPError):
            service.compare_comprehensive(rfq_id="RFQ-001", item_code="ITEM-001")

    def test_가중치_커스텀_적용(self) -> None:
        """사용자 정의 가중치가 정상 적용된다."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = [
            {
                "_id": "SQ-001",
                "supplier": "SUP-A",
                "delivery_days": 10,
                "payment_terms_days": 30,
                "min_order_qty": 10,
                "items": [{"item_code": "ITEM-001", "rate": 5000, "qty": 100}],
            },
        ]

        # 납기 100% 가중치
        result = service.compare_comprehensive(
            rfq_id="RFQ-001",
            item_code="ITEM-001",
            weights={"price": 0.0, "delivery": 1.0, "payment": 0.0},
        )

        score = result["scores"][0]
        assert score["total_score"] == 100.0

    def test_가중치_합계_검증(self) -> None:
        """가중치 합계가 1.0이 아니면 400 에러."""
        service, sq_repo, _rfq_repo = _make_service()
        sq_repo.find_many.return_value = []

        with pytest.raises(OneERPError, match="bad_request"):
            service.compare_comprehensive(
                rfq_id="RFQ-001",
                item_code="ITEM-001",
                weights={"price": 0.5, "delivery": 0.3, "payment": 0.3},
            )
