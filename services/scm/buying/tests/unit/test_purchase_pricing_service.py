"""구매 가격 규칙 서비스(PurchasePricingService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """Repository를 모킹하여 PurchasePricingService 인스턴스를 생성한다."""
    with patch("oneerp_buying_app.services.purchase_pricing_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_buying_app.services.purchase_pricing_service import PurchasePricingService

        service = PurchasePricingService(tenant_id="test-tenant")
    return service, repos["purchase_pricing_rules"]


class Test구매가격규칙적용:
    def test_공급업체별_비율할인(self) -> None:
        """공급업체별 비율 할인이 정상 적용된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PPRC-001",
                "apply_on": "supplier",
                "supplier": "SUP-001",
                "discount_type": "percentage",
                "discount_value": 5,
                "priority": 1,
                "is_active": True,
            },
        ]

        result = service.apply_rules(
            [{"item_code": "ITEM-001", "qty": 10, "rate": 2000}],
            party="SUP-001",
        )

        item = result["applied_items"][0]
        assert item["final_rate"] == 1900.0
        assert item["discount_amount"] == 1000.0  # 2000 * 10 * 5%
        assert result["total_discount"] == 1000.0

    def test_아이템별_고정금액_할인(self) -> None:
        """아이템별 고정 금액 할인이 정상 적용된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PPRC-002",
                "apply_on": "item",
                "item_code": "RAW-001",
                "discount_type": "fixed",
                "discount_value": 500,
                "priority": 1,
                "is_active": True,
            },
        ]

        result = service.apply_rules(
            [{"item_code": "RAW-001", "qty": 5, "rate": 1000}],
        )

        item = result["applied_items"][0]
        assert item["discount_amount"] == 500.0

    def test_규칙_미매칭시_원가유지(self) -> None:
        """매칭되는 규칙이 없으면 원가를 유지한다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = []

        result = service.apply_rules(
            [{"item_code": "ITEM-001", "qty": 1, "rate": 3000}],
            party="SUP-001",
        )

        item = result["applied_items"][0]
        assert item["final_rate"] == 3000.0
        assert item["discount_amount"] == 0
        assert item["rule_applied"] is None

    def test_공급업체_미일치시_규칙_미적용(self) -> None:
        """다른 공급업체의 규칙은 적용되지 않는다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PPRC-003",
                "apply_on": "supplier",
                "supplier": "SUP-999",
                "discount_type": "percentage",
                "discount_value": 10,
                "priority": 1,
                "is_active": True,
            },
        ]

        result = service.apply_rules(
            [{"item_code": "ITEM-001", "qty": 1, "rate": 1000}],
            party="SUP-001",
        )

        assert result["applied_items"][0]["rule_applied"] is None

    def test_최소수량_조건_충족시_적용(self) -> None:
        """최소 수량 조건을 충족하면 규칙이 적용된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PPRC-004",
                "apply_on": "item",
                "item_code": "BULK-001",
                "discount_type": "percentage",
                "discount_value": 15,
                "min_qty": 50,
                "priority": 1,
                "is_active": True,
            },
        ]

        # 수량 미달 — 규칙 미적용
        result = service.apply_rules(
            [{"item_code": "BULK-001", "qty": 10, "rate": 100}],
        )
        assert result["applied_items"][0]["rule_applied"] is None

        # 수량 충족 — 규칙 적용
        result = service.apply_rules(
            [{"item_code": "BULK-001", "qty": 100, "rate": 100}],
        )
        assert result["applied_items"][0]["rule_applied"] == "PPRC-004"
        assert result["applied_items"][0]["final_rate"] == 85.0
