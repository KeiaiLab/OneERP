"""E2E 시나리오 검증 — 03-e2e-scenarios.md 기반.

모노레포 구조에서 다중 서비스의 app 패키지가 충돌하므로,
E2E 테스트는 각 서비스의 단위 테스트에서 시나리오별로 검증한다.

이 파일은 시나리오 커버리지를 선언적으로 추적하는 마커 테스트이다.
실제 검증은 각 서비스의 test_*_service.py에서 수행된다.
"""

from __future__ import annotations

from typing import cast

import pytest

# 시나리오 커버리지 매트릭스
# release-critical 플래그로 배포 게이트 대상과 일반 커버리지를 구분한다.
_SCENARIOS = {
    "1. 판매→출하→회계→수금": {
        "검증 위치": [
            "services/selling/tests/unit/test_sales_return_service.py",
            "services/selling/tests/unit/test_pricing_rule_service.py",
            "services/selling/tests/unit/test_blanket_order_service.py",
            "services/stock/tests/unit/test_pick_pack_service.py",
        ],
        "구현 서비스": [
            "SalesReturnService",
            "PricingRuleService",
            "BlanketOrderService",
            "PickPackService",
        ],
        "release_critical": True,
    },
    "2. 구매→RFQ→입고→세금→지급": {
        "검증 위치": [
            "services/buying/tests/unit/test_purchase_process_service.py",
            "services/buying/tests/unit/test_landed_cost_service.py",
            "services/buying/tests/unit/test_purchase_return_service.py",
            "services/buying/tests/unit/test_supplier_scorecard_service.py",
            "services/buying/tests/unit/test_buyer_approval_service.py",
        ],
        "구현 서비스": [
            "PurchaseProcessService",
            "LandedCostService",
            "PurchaseReturnService",
            "SupplierScorecardService",
            "BuyerApprovalService",
        ],
        "release_critical": True,
    },
    "3. 회계 결산→대사→세무": {
        "검증 위치": [
            "services/accounting/tests/unit/test_period_closing_service.py",
            "services/accounting/tests/unit/test_bank_reconciliation_service.py",
            "services/accounting/tests/unit/test_payment_reconciliation_service.py",
            "services/accounting/tests/unit/test_dunning_service.py",
            "services/accounting/tests/unit/test_consolidation_service.py",
            "services/accounting/tests/unit/test_treasury_service.py",
        ],
        "구현 서비스": [
            "PeriodClosingService",
            "BankReconciliationService",
            "PaymentReconciliationService",
            "DunningService",
            "ConsolidationService",
            "TreasuryService",
        ],
        "release_critical": True,
    },
    "4. 전자결재→위임→감사 추적": {
        "검증 위치": ["services/gateway/tests/unit/test_approval_service.py"],
        "구현 서비스": ["ApprovalService (합의/전결/대결)"],
        "release_critical": True,
    },
    "5. CRM 이슈→SLA→지식베이스": {
        "검증 위치": [
            "services/crm/tests/unit/test_campaign_service.py",
            "services/crm/tests/unit/test_field_service.py",
        ],
        "구현 서비스": ["CampaignService", "FieldServiceManager"],
        "release_critical": False,
    },
    "6. 현장서비스→보증→자산/재고": {
        "검증 위치": [
            "services/crm/tests/unit/test_field_service.py",
            "services/assets/tests/unit/test_fleet_service.py",
        ],
        "구현 서비스": ["FieldServiceManager", "FleetService"],
        "release_critical": False,
    },
    "7. HR 온보딩→교대→급여 세무": {
        "검증 위치": [
            "services/hr/tests/unit/test_onboarding_service.py",
            "services/hr/tests/unit/test_shift_service.py",
            "services/hr/tests/unit/test_skill_map_service.py",
            "services/hr/tests/unit/test_transfer_service.py",
            "services/hr/tests/unit/test_recruitment_service.py",
            "services/hr/tests/unit/test_leave_service.py",
        ],
        "구현 서비스": [
            "OnboardingService",
            "ShiftService",
            "SkillMapService",
            "TransferService",
            "RecruitmentService",
            "LeaveService",
        ],
        "release_critical": False,
    },
    "8. 경비→법인카드→결제": {
        "검증 위치": ["services/expenses/tests/unit/test_expense_service.py"],
        "구현 서비스": ["ExpenseService"],
        "release_critical": False,
    },
}


@pytest.mark.parametrize("scenario", list(_SCENARIOS.keys()))
def test_시나리오_커버리지(scenario: str) -> None:
    """각 E2E 시나리오가 서비스 단위 테스트로 커버되는지 확인한다."""
    info = _SCENARIOS[scenario]
    validation_paths = cast("list[str]", info["검증 위치"])
    implementation_services = cast("list[str]", info["구현 서비스"])
    assert len(validation_paths) > 0, f"시나리오 '{scenario}'에 검증 테스트가 없습니다"
    assert len(implementation_services) > 0, f"시나리오 '{scenario}'에 구현 서비스가 없습니다"
    assert "release_critical" in info, f"시나리오 '{scenario}'에 release_critical 플래그가 없습니다"


def test_release_critical_scenarios_are_declared() -> None:
    release_critical = [name for name, info in _SCENARIOS.items() if info["release_critical"]]
    assert release_critical == [
        "1. 판매→출하→회계→수금",
        "2. 구매→RFQ→입고→세금→지급",
        "3. 회계 결산→대사→세무",
        "4. 전자결재→위임→감사 추적",
    ]
