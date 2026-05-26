"""발주 변경 관리 서비스(PurchaseOrderAmendmentService) 단위 테스트.

BR-BUY-NEW-022: 제출된 PO의 수량/단가/일자 변경을 이력으로 추적하고 차액을 산출.

참조: ERPNext/Cornell Purchase Order Amendment (POA), 일반 P2P 모범사례.
- 제출된(docstatus=1) PO는 원본 수정 불가
- Amendment는 새 리비전으로 추적 (amendment_no 증가)
- 변경 사항별 차액(old vs new, qty/rate/amount)과 누적 delta 계산
- Draft(docstatus=0) PO에 대한 amendment는 금지 (일반 수정 사용)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 리비전 번호 기반으로 모킹."""
    with patch(
        "oneerp_buying_app.services.purchase_order_amendment_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """PurchaseOrderAmendmentService와 mock repo를 생성한다."""
    with patch(
        "oneerp_buying_app.services.purchase_order_amendment_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_buying_app.services.purchase_order_amendment_service import (
            PurchaseOrderAmendmentService,
        )

        service = PurchaseOrderAmendmentService(tenant_id="test-tenant")

    return (
        service,
        repos["purchase_orders"],
        repos["purchase_order_amendments"],
    )


class Test발주변경_수량:
    """수량 변경 시나리오."""

    def test_수량_증가_차액_계산(self) -> None:
        """수량을 100 -> 120으로 증가 시 차액 +100,000 계산."""
        service, po_repo, amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,  # 제출됨
            "supplier_id": "SUP-001",
            "grand_total": 500_000,
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 100,
                    "rate": 5000,
                    "amount": 500_000,
                },
            ],
        }

        result = service.amend_order(
            po_id="PO-001",
            changes=[{"item_code": "ITEM-001", "new_qty": 120}],
            reason="추가 수요 발생",
        )

        assert result["amendment_id"] == "POAM-001"
        assert result["po_id"] == "PO-001"
        # 수량 변경: 20 * 5000 = 100,000 증가
        assert result["delta"]["amount_delta"] == 100_000
        assert result["new_grand_total"] == 600_000
        assert result["old_grand_total"] == 500_000
        amend_repo.insert.assert_called_once()

    def test_수량_감소_차액_음수(self) -> None:
        """수량을 100 -> 80으로 감소 시 차액 -100,000."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "grand_total": 500_000,
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 100,
                    "rate": 5000,
                    "amount": 500_000,
                },
            ],
        }

        result = service.amend_order(
            po_id="PO-001",
            changes=[{"item_code": "ITEM-001", "new_qty": 80}],
            reason="수요 감소",
        )

        assert result["delta"]["amount_delta"] == -100_000
        assert result["new_grand_total"] == 400_000


class Test발주변경_단가:
    """단가 변경 시나리오."""

    def test_단가_인상_차액(self) -> None:
        """단가 5000 -> 5500 인상 시 차액 +50,000."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "grand_total": 500_000,
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 100,
                    "rate": 5000,
                    "amount": 500_000,
                },
            ],
        }

        result = service.amend_order(
            po_id="PO-001",
            changes=[{"item_code": "ITEM-001", "new_rate": 5500}],
            reason="공급사 단가 인상",
        )

        # 100 * (5500 - 5000) = 50,000
        assert result["delta"]["amount_delta"] == 50_000
        assert result["new_grand_total"] == 550_000

    def test_수량_단가_동시변경(self) -> None:
        """수량과 단가 동시 변경."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "grand_total": 500_000,
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 100,
                    "rate": 5000,
                    "amount": 500_000,
                },
            ],
        }

        result = service.amend_order(
            po_id="PO-001",
            changes=[{"item_code": "ITEM-001", "new_qty": 120, "new_rate": 5200}],
            reason="물량 확대 + 단가 재협상",
        )

        # new = 120 * 5200 = 624,000, old = 500,000
        assert result["new_grand_total"] == 624_000
        assert result["delta"]["amount_delta"] == 124_000


class Test발주변경_복수품목:
    """복수 품목 동시 변경."""

    def test_복수품목_변경_집계(self) -> None:
        """두 품목 동시 변경 시 총 delta 집계."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "grand_total": 800_000,
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 100,
                    "rate": 5000,
                    "amount": 500_000,
                },
                {
                    "item_code": "ITEM-002",
                    "item_name": "원자재B",
                    "qty": 60,
                    "rate": 5000,
                    "amount": 300_000,
                },
            ],
        }

        result = service.amend_order(
            po_id="PO-001",
            changes=[
                {"item_code": "ITEM-001", "new_qty": 120},  # +100,000
                {"item_code": "ITEM-002", "new_qty": 50},  # -50,000
            ],
            reason="생산 계획 조정",
        )

        # +100,000 + (-50,000) = +50,000
        assert result["delta"]["amount_delta"] == 50_000
        assert result["new_grand_total"] == 850_000
        assert len(result["delta"]["item_changes"]) == 2


class Test발주변경_예외:
    """예외 케이스."""

    def test_PO_미존재_404(self) -> None:
        """존재하지 않는 PO 조회 시 404 에러."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.amend_order(
                po_id="PO-999",
                changes=[{"item_code": "ITEM-001", "new_qty": 50}],
                reason="test",
            )

    def test_Draft_PO_amendment_금지(self) -> None:
        """Draft(docstatus=0) PO는 amendment 금지 (일반 수정 사용)."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 0,  # Draft
            "supplier_id": "SUP-001",
            "grand_total": 500_000,
            "items": [],
        }

        with pytest.raises(OneERPError, match="ERR-BUY"):
            service.amend_order(
                po_id="PO-001",
                changes=[{"item_code": "ITEM-001", "new_qty": 50}],
                reason="test",
            )

    def test_취소된_PO_amendment_금지(self) -> None:
        """취소(docstatus=2)된 PO는 amendment 금지."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 2,  # Cancelled
            "supplier_id": "SUP-001",
            "grand_total": 500_000,
            "items": [],
        }

        with pytest.raises(OneERPError, match="ERR-BUY"):
            service.amend_order(
                po_id="PO-001",
                changes=[{"item_code": "ITEM-001", "new_qty": 50}],
                reason="test",
            )

    def test_품목미존재_에러(self) -> None:
        """PO에 없는 품목 amendment는 422 에러."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "grand_total": 500_000,
            "items": [
                {
                    "item_code": "ITEM-001",
                    "qty": 100,
                    "rate": 5000,
                    "amount": 500_000,
                },
            ],
        }

        with pytest.raises(OneERPError):
            service.amend_order(
                po_id="PO-001",
                changes=[{"item_code": "ITEM-999", "new_qty": 50}],
                reason="test",
            )

    def test_빈_변경_사항_에러(self) -> None:
        """빈 변경 사항은 400 에러."""
        service, po_repo, _amend_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "items": [{"item_code": "ITEM-001", "qty": 100, "rate": 5000, "amount": 500_000}],
        }

        with pytest.raises(OneERPError, match="bad_request"):
            service.amend_order(po_id="PO-001", changes=[], reason="test")


class Test발주변경_이력조회:
    """이력 조회 기능."""

    def test_PO_amendment_history_조회(self) -> None:
        """특정 PO의 변경 이력을 조회한다."""
        service, _po_repo, amend_repo = _make_service()
        amend_repo.find_many.return_value = [
            {
                "_id": "POAM-001",
                "po_id": "PO-001",
                "amendment_no": 1,
                "delta": {"amount_delta": 100_000},
                "reason": "추가 수요",
            },
            {
                "_id": "POAM-002",
                "po_id": "PO-001",
                "amendment_no": 2,
                "delta": {"amount_delta": -20_000},
                "reason": "품목 일부 취소",
            },
        ]

        history = service.get_amendment_history("PO-001")

        assert len(history) == 2
        assert history[0]["amendment_no"] == 1
        assert history[1]["amendment_no"] == 2
