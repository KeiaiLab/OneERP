"""가격 규칙 서비스(PricingRuleService) 단위 테스트.

기존 apply_rules(core 래핑) 경로와 신규 엔진 보강 메서드를 함께 검증한다.

신규 엔진 보강(E6) — BR-SELL-014 심화:
- find_applicable_rules: 컨텍스트 기반 규칙 후보 탐색
- resolve_best_rule: 우선순위/구체성/최신성 기반 단일 해소
- calculate_final_rate: 할인 유형(Rate/Discount Percentage/Discount Amount) 적용
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    """Repository를 모킹하여 selling용 PricingRuleService를 생성한다."""
    with patch("oneerp_selling_app.services.pricing_rule_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_selling_app.services.pricing_rule_service import PricingRuleService

        service = PricingRuleService(tenant_id="test-tenant")
    return service, repos["pricing_rules"]


def _make_rule(
    *,
    rule_id: str,
    priority: int = 10,
    applicable_for: str = "item_code",
    applicable_for_value: str = "ITEM-001",
    customer: str | None = None,
    customer_group: str | None = None,
    territory: str | None = None,
    min_qty: str = "1",
    max_qty: str | None = None,
    valid_from: str = "2026-01-01",
    valid_upto: str | None = None,
    rate_or_discount: str = "Discount Percentage",
    rate: str = "0",
    discount_percentage: str = "0",
    discount_amount: str = "0",
    is_active: bool = True,
) -> dict[str, Any]:
    """테스트용 규칙 dict 생성 헬퍼.

    저장소는 dict 형태로 문서를 반환하므로, 모델 변경 없이 신규 필드를
    dict 키로 직접 주입해 엔진을 검증한다.
    """
    return {
        "_id": rule_id,
        "priority": priority,
        "applicable_for": applicable_for,
        "applicable_for_value": applicable_for_value,
        "customer": customer,
        "customer_group": customer_group,
        "territory": territory,
        "min_qty": min_qty,
        "max_qty": max_qty,
        "valid_from": valid_from,
        "valid_upto": valid_upto,
        "rate_or_discount": rate_or_discount,
        "rate": rate,
        "discount_percentage": discount_percentage,
        "discount_amount": discount_amount,
        "is_active": is_active,
    }


# =====================================================================
# 기존 apply_rules 경로 (core 래퍼 계약 보존)
# =====================================================================


class Test가격규칙적용:
    def test_비율할인_적용(self) -> None:
        """10% 비율 할인이 정상 적용된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PRC-001",
                "apply_on": "item",
                "item_code": "ITEM-001",
                "discount_type": "percentage",
                "discount_value": 10,
                "priority": 1,
                "is_active": True,
            },
        ]

        result = service.apply_rules([{"item_code": "ITEM-001", "qty": 5, "rate": 1000}])

        item = result["applied_items"][0]
        assert item["final_rate"] == 900.0
        assert item["discount_amount"] == 500.0  # 1000*5*10%
        assert result["total_discount"] == 500.0

    def test_고정금액_할인(self) -> None:
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PRC-002",
                "apply_on": "item",
                "item_code": "ITEM-001",
                "discount_type": "fixed",
                "discount_value": 200,
                "priority": 1,
                "is_active": True,
            },
        ]

        result = service.apply_rules([{"item_code": "ITEM-001", "qty": 2, "rate": 500}])

        item = result["applied_items"][0]
        assert item["discount_amount"] == 200.0

    def test_규칙_미매칭시_원가유지(self) -> None:
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = []

        result = service.apply_rules([{"item_code": "ITEM-001", "qty": 1, "rate": 1000}])

        item = result["applied_items"][0]
        assert item["final_rate"] == 1000.0
        assert item["discount_amount"] == 0
        assert item["rule_applied"] is None

    def test_우선순위_높은_규칙_우선(self) -> None:
        """우선순위가 높은 규칙이 먼저 적용된다 (기존 core 계약)."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PRC-001",
                "apply_on": "item",
                "item_code": "ITEM-001",
                "discount_type": "percentage",
                "discount_value": 5,
                "priority": 1,
                "is_active": True,
            },
            {
                "_id": "PRC-002",
                "apply_on": "item",
                "item_code": "ITEM-001",
                "discount_type": "percentage",
                "discount_value": 20,
                "priority": 10,
                "is_active": True,
            },
        ]

        result = service.apply_rules([{"item_code": "ITEM-001", "qty": 1, "rate": 1000}])

        item = result["applied_items"][0]
        # 우선순위 10 > 1, 20% 할인 적용
        assert item["rule_applied"] == "PRC-002"
        assert item["final_rate"] == 800.0

    def test_고객별_규칙_적용(self) -> None:
        """고객별 규칙이 party 파라미터로 올바르게 매칭된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PRC-003",
                "apply_on": "customer",
                "customer": "CUST-A",
                "discount_type": "percentage",
                "discount_value": 15,
                "priority": 1,
                "is_active": True,
            },
        ]

        # 매칭되는 고객
        result = service.apply_rules(
            [{"item_code": "ITEM-001", "qty": 1, "rate": 1000}],
            party="CUST-A",
        )
        assert result["applied_items"][0]["final_rate"] == 850.0

        # 매칭되지 않는 고객
        result = service.apply_rules(
            [{"item_code": "ITEM-001", "qty": 1, "rate": 1000}],
            party="CUST-B",
        )
        assert result["applied_items"][0]["final_rate"] == 1000.0


# =====================================================================
# 신규 엔진: find_applicable_rules
# =====================================================================


class Test적용가능_규칙탐색:
    """find_applicable_rules: 컨텍스트 기반 규칙 후보 탐색."""

    def test_item_code_단일_매칭(self) -> None:
        """item_code가 일치하는 규칙만 반환된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-001", applicable_for_value="ITEM-001"),
            _make_rule(rule_id="PRC-002", applicable_for_value="ITEM-999"),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            transaction_date=date(2026, 3, 1),
        )

        ids = [r["_id"] for r in rules]
        assert "PRC-001" in ids
        assert "PRC-002" not in ids

    def test_customer_일치_필터(self) -> None:
        """customer가 지정된 규칙은 동일 customer에서만 매칭된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-A", customer="CUST-A"),
            _make_rule(rule_id="PRC-B", customer="CUST-B"),
            _make_rule(rule_id="PRC-X", customer=None),  # 전체 적용
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            customer="CUST-A",
            transaction_date=date(2026, 3, 1),
        )

        ids = {r["_id"] for r in rules}
        assert ids == {"PRC-A", "PRC-X"}

    def test_customer_group_일치(self) -> None:
        """customer 불일치더라도 customer_group이 맞으면 매칭된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-CG", customer_group="VIP"),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            customer="CUST-A",
            customer_group="VIP",
            transaction_date=date(2026, 3, 1),
        )

        assert len(rules) == 1
        assert rules[0]["_id"] == "PRC-CG"

    def test_territory_일치(self) -> None:
        """territory 조건 매칭을 확인한다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-T1", territory="KR"),
            _make_rule(rule_id="PRC-T2", territory="JP"),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            territory="KR",
            transaction_date=date(2026, 3, 1),
        )

        assert [r["_id"] for r in rules] == ["PRC-T1"]

    def test_수량_min_qty_미달_제외(self) -> None:
        """qty가 min_qty보다 작으면 제외된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-MIN", min_qty="10"),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            qty=Decimal(5),
            transaction_date=date(2026, 3, 1),
        )

        assert rules == []

    def test_수량_max_qty_초과_제외(self) -> None:
        """qty가 max_qty를 초과하면 제외된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-MAX", min_qty="1", max_qty="100"),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            qty=Decimal(150),
            transaction_date=date(2026, 3, 1),
        )

        assert rules == []

    def test_수량_정상_범위(self) -> None:
        """min_qty <= qty <= max_qty 범위면 매칭된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-RNG", min_qty="10", max_qty="100"),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            qty=Decimal(50),
            transaction_date=date(2026, 3, 1),
        )

        assert len(rules) == 1
        assert rules[0]["_id"] == "PRC-RNG"

    def test_기간_valid_from_이전_제외(self) -> None:
        """transaction_date가 valid_from보다 이전이면 제외된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-FT", valid_from="2026-06-01"),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            transaction_date=date(2026, 3, 1),
        )

        assert rules == []

    def test_기간_valid_upto_이후_제외(self) -> None:
        """transaction_date가 valid_upto보다 이후면 제외된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-UT", valid_from="2026-01-01", valid_upto="2026-02-28"),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            transaction_date=date(2026, 3, 1),
        )

        assert rules == []

    def test_기간_정상_무한_상한(self) -> None:
        """valid_upto가 None이면 상한이 무한이다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(rule_id="PRC-OPEN", valid_from="2025-01-01", valid_upto=None),
        ]

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            transaction_date=date(2099, 12, 31),
        )

        assert len(rules) == 1

    def test_빈_결과(self) -> None:
        """저장소가 비었으면 빈 리스트를 반환한다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = []

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            transaction_date=date(2026, 3, 1),
        )

        assert rules == []

    def test_transaction_date_None_시_오늘_기준(self) -> None:
        """transaction_date가 None이면 오늘로 처리한다."""
        service, rule_repo = _make_service()
        # 오늘(2026-04-10)을 포함하는 규칙
        rule_repo.find_many.return_value = [
            _make_rule(
                rule_id="PRC-TODAY",
                valid_from="2025-01-01",
                valid_upto=None,
            ),
        ]

        rules = service.find_applicable_rules(item_code="ITEM-001")

        assert len(rules) == 1
        assert rules[0]["_id"] == "PRC-TODAY"


# =====================================================================
# 신규 엔진: resolve_best_rule
# =====================================================================


class Test최적규칙_해소:
    """resolve_best_rule: 구체성/우선순위/최신성 기반 단일 규칙 결정."""

    def test_규칙_없음(self) -> None:
        """빈 리스트면 None을 반환한다."""
        service, _ = _make_service()
        assert service.resolve_best_rule([]) is None

    def test_단일_규칙(self) -> None:
        """규칙이 하나면 그 규칙이 선택된다."""
        service, _ = _make_service()
        rule = _make_rule(rule_id="PRC-ONLY")
        assert service.resolve_best_rule([rule]) == rule

    def test_priority_낮은_숫자_우선(self) -> None:
        """priority 값이 낮을수록 우선(1이 최우선)."""
        service, _ = _make_service()
        low = _make_rule(rule_id="PRC-LOW", priority=1)
        high = _make_rule(rule_id="PRC-HIGH", priority=99)
        best = service.resolve_best_rule([high, low])
        assert best["_id"] == "PRC-LOW"

    def test_구체성_customer_우선(self) -> None:
        """동일 priority에서 customer 매칭이 customer_group 매칭을 이긴다."""
        service, _ = _make_service()
        by_customer = _make_rule(rule_id="PRC-CUST", priority=10, customer="CUST-A")
        by_group = _make_rule(rule_id="PRC-GRP", priority=10, customer_group="VIP")
        best = service.resolve_best_rule([by_group, by_customer])
        assert best["_id"] == "PRC-CUST"

    def test_구체성_group_이_territory_보다_우선(self) -> None:
        """customer_group 매칭이 territory 매칭을 이긴다."""
        service, _ = _make_service()
        by_group = _make_rule(rule_id="PRC-GRP", priority=10, customer_group="VIP")
        by_territory = _make_rule(rule_id="PRC-TER", priority=10, territory="KR")
        best = service.resolve_best_rule([by_territory, by_group])
        assert best["_id"] == "PRC-GRP"

    def test_동률_시_valid_from_최신_우선(self) -> None:
        """같은 priority·같은 구체성이면 valid_from이 더 최근인 규칙이 이긴다."""
        service, _ = _make_service()
        older = _make_rule(rule_id="PRC-OLD", priority=5, valid_from="2025-01-01")
        newer = _make_rule(rule_id="PRC-NEW", priority=5, valid_from="2026-03-15")
        best = service.resolve_best_rule([older, newer])
        assert best["_id"] == "PRC-NEW"


# =====================================================================
# 신규 엔진: calculate_final_rate
# =====================================================================


class Test최종단가_계산:
    """calculate_final_rate: 적용 규칙을 반영한 최종 단가 산출."""

    def test_Rate_모드_규칙_단가_사용(self) -> None:
        """rate_or_discount=Rate이면 rule.rate를 그대로 사용한다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(
                rule_id="PRC-RATE",
                rate_or_discount="Rate",
                rate="900",
                discount_percentage="0",
            ),
        ]

        final_rate, rule = service.calculate_final_rate(
            item_code="ITEM-001",
            base_rate=Decimal(1000),
            transaction_date=date(2026, 3, 1),
        )

        assert final_rate == Decimal(900)
        assert rule is not None
        assert rule["_id"] == "PRC-RATE"

    def test_Discount_Percentage_모드(self) -> None:
        """discount_percentage=15이면 base_rate * 0.85."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(
                rule_id="PRC-PCT",
                rate_or_discount="Discount Percentage",
                discount_percentage="15",
            ),
        ]

        final_rate, rule = service.calculate_final_rate(
            item_code="ITEM-001",
            base_rate=Decimal(1000),
            transaction_date=date(2026, 3, 1),
        )

        assert final_rate == Decimal("850.00")
        assert rule["_id"] == "PRC-PCT"

    def test_Discount_Amount_모드(self) -> None:
        """discount_amount=200이면 base_rate - 200."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(
                rule_id="PRC-AMT",
                rate_or_discount="Discount Amount",
                discount_amount="200",
            ),
        ]

        final_rate, rule = service.calculate_final_rate(
            item_code="ITEM-001",
            base_rate=Decimal(1000),
            transaction_date=date(2026, 3, 1),
        )

        assert final_rate == Decimal(800)
        assert rule["_id"] == "PRC-AMT"

    def test_Discount_Amount_음수_방지(self) -> None:
        """discount_amount가 base_rate보다 커도 최종 단가는 0 이상이다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(
                rule_id="PRC-AMT2",
                rate_or_discount="Discount Amount",
                discount_amount="5000",
            ),
        ]

        final_rate, rule = service.calculate_final_rate(
            item_code="ITEM-001",
            base_rate=Decimal(1000),
            transaction_date=date(2026, 3, 1),
        )

        assert final_rate == Decimal(0)
        assert rule["_id"] == "PRC-AMT2"

    def test_적용_규칙_없음_원가_반환(self) -> None:
        """매칭 규칙이 없으면 base_rate를 그대로 반환하고 rule은 None."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = []

        final_rate, rule = service.calculate_final_rate(
            item_code="ITEM-001",
            base_rate=Decimal(1000),
            transaction_date=date(2026, 3, 1),
        )

        assert final_rate == Decimal(1000)
        assert rule is None

    def test_여러_규칙_중_구체성_높은_것_적용(self) -> None:
        """여러 후보 중 customer 매칭 규칙이 적용된다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            _make_rule(
                rule_id="PRC-GEN",
                rate_or_discount="Discount Percentage",
                discount_percentage="5",
            ),
            _make_rule(
                rule_id="PRC-CUST",
                rate_or_discount="Discount Percentage",
                discount_percentage="25",
                customer="CUST-A",
            ),
        ]

        final_rate, rule = service.calculate_final_rate(
            item_code="ITEM-001",
            base_rate=Decimal(1000),
            customer="CUST-A",
            transaction_date=date(2026, 3, 1),
        )

        # customer 매칭 규칙이 구체성 우선으로 선택되어 25% 할인 적용
        assert rule["_id"] == "PRC-CUST"
        assert final_rate == Decimal("750.00")


# =====================================================================
# 경계 조건 / 방어적 처리
# =====================================================================


class Test엣지케이스:
    """비활성/잘못된 입력/결측 필드에 대한 방어적 처리."""

    def test_비활성_규칙_제외(self) -> None:
        """is_active=False인 규칙은 저장소 쿼리 단계에서 제외되어야 한다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = []

        rules = service.find_applicable_rules(
            item_code="ITEM-001",
            transaction_date=date(2026, 3, 1),
        )

        # Repository.find_many 호출 시 is_active=True 필터가 전달되었는지 확인
        call_args = rule_repo.find_many.call_args
        assert call_args is not None
        query = call_args.args[0] if call_args.args else call_args.kwargs.get("query")
        assert query.get("is_active") is True
        assert rules == []

    def test_결측_priority_기본값(self) -> None:
        """priority 필드가 없어도 안전하게 정렬 가능해야 한다.

        기본값은 0으로 처리되므로 priority=0(결측) 쪽이 priority=5 쪽보다
        우선한다. 즉 결측은 더 공격적인 기본값이다.
        """
        service, _ = _make_service()
        rule_a = {"_id": "PRC-A"}  # priority 없음 → 0으로 해석
        rule_b = _make_rule(rule_id="PRC-B", priority=5)

        best = service.resolve_best_rule([rule_a, rule_b])
        # priority 낮은 숫자 우선: 결측(0) < 5
        assert best["_id"] == "PRC-A"

    def test_결측_rate_or_discount_기본_percentage(self) -> None:
        """rate_or_discount 미지정 시 Discount Percentage로 처리한다."""
        service, rule_repo = _make_service()
        rule_repo.find_many.return_value = [
            {
                "_id": "PRC-DEF",
                "applicable_for": "item_code",
                "applicable_for_value": "ITEM-001",
                "min_qty": "1",
                "valid_from": "2025-01-01",
                "priority": 10,
                "is_active": True,
                "discount_percentage": "10",
            },
        ]

        final_rate, rule = service.calculate_final_rate(
            item_code="ITEM-001",
            base_rate=Decimal(1000),
            transaction_date=date(2026, 3, 1),
        )

        assert final_rate == Decimal("900.00")
        assert rule is not None


@pytest.mark.parametrize(
    ("base_rate", "discount_percentage", "expected"),
    [
        ("1000", "10", "900.00"),
        ("1000", "0", "1000.00"),
        ("1500", "25", "1125.00"),
        ("999.99", "50", "499.995"),
    ],
)
def test_퍼센트할인_파라미터라이즈(base_rate: str, discount_percentage: str, expected: str) -> None:
    """여러 비율/원가 조합에서 Discount Percentage 모드가 일관 동작한다."""
    service, rule_repo = _make_service()
    rule_repo.find_many.return_value = [
        _make_rule(
            rule_id="PRC-PARAM",
            rate_or_discount="Discount Percentage",
            discount_percentage=discount_percentage,
        ),
    ]

    final_rate, _ = service.calculate_final_rate(
        item_code="ITEM-001",
        base_rate=Decimal(base_rate),
        transaction_date=date(2026, 3, 1),
    )

    assert final_rate == Decimal(expected)
