"""재고 실사 조정 서비스(StockReconciliationService) 단위 테스트.

submit_reconciliation, calculate_variance_summary 메서드의
정상·예외·경계값 시나리오를 검증한다.
"""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@contextmanager
def _service_context(
    *,
    sr_doc: dict | None = None,
    bin_docs: dict[tuple[str, str], list[dict]] | None = None,
):
    """mock 컨텍스트와 서비스/리포지토리 dict를 yield한다."""
    with (
        patch(
            "oneerp_stock_app.services.stock_reconciliation_service.Repository",
        ) as mock_repo_cls,
        patch(
            "oneerp_stock_app.services.stock_reconciliation_service.generate_name",
            side_effect=lambda prefix, **_: f"{prefix}-MOCK-001",
        ),
    ):
        repos: dict[str, MagicMock] = {}
        bin_lookup = bin_docs or {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name in repos:
                return repos[collection_name]
            repo = MagicMock()
            repos[collection_name] = repo

            if collection_name == "stock_reconciliations":
                repo.find_by_id.return_value = sr_doc
            elif collection_name == "stock_bins":

                def _bin_find(query, limit=1, **kwargs):
                    key = (query.get("item_code", ""), query.get("warehouse", ""))
                    return bin_lookup.get(key, [])

                repo.find_many.side_effect = _bin_find
            elif collection_name == "stock_ledger_entries":
                # SLE는 insert만 호출됨
                pass

            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_stock_app.services.stock_reconciliation_service import (
            StockReconciliationService,
        )

        service = StockReconciliationService(tenant_id="test-tenant")
        yield service, repos


# ======================================================================
# 정상 케이스
# ======================================================================


class Test실사제출_정상:
    """재고 실사 제출 정상 시나리오."""

    def test_단일_라인_차이_조정(self) -> None:
        """단일 품목의 차이를 SLE 보정으로 반영한다."""
        sr_doc = {
            "_id": "SREC-001",
            "status": "draft",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "warehouse": "WH-01",
                    "qty": 120,
                    "valuation_rate": 1000,
                }
            ],
        }
        bin_docs = {
            ("ITEM-A", "WH-01"): [
                {
                    "_id": "SBIN-1",
                    "current_qty": 100,
                    "current_value": 100000,
                }
            ]
        }

        with _service_context(sr_doc=sr_doc, bin_docs=bin_docs) as (service, repos):
            result = service.submit_reconciliation("SREC-001")

            assert result["reconciliation_id"] == "SREC-001"
            assert len(result["items"]) == 1
            line = result["items"][0]
            assert line["system_qty"] == Decimal(100)
            assert line["target_qty"] == Decimal(120)
            assert line["variance_qty"] == Decimal(20)
            assert line["variance_value"] == Decimal(20000)
            assert line["sle_id"] == "SLE-MOCK-001"
            assert result["total_variance_qty"] == Decimal(20)
            assert result["total_variance_value"] == Decimal(20000)

            # SLE insert 호출 검증
            sle_repo = repos["stock_ledger_entries"]
            sle_repo.insert.assert_called_once()

            # bin update 검증
            bin_repo = repos["stock_bins"]
            bin_repo.update_by_id.assert_called_once()

            # SR 문서 status=submitted 검증
            sr_repo = repos["stock_reconciliations"]
            update_call = sr_repo.update_by_id.call_args[0]
            assert update_call[1]["status"] == "submitted"

    def test_다중_라인_누적(self) -> None:
        """여러 라인의 차이가 누적되어 합계로 반환된다."""
        sr_doc = {
            "_id": "SREC-002",
            "status": "in_progress",
            "items": [
                {"item_code": "ITEM-A", "warehouse": "WH-01", "qty": 50, "valuation_rate": 100},
                {"item_code": "ITEM-B", "warehouse": "WH-01", "qty": 20, "valuation_rate": 200},
            ],
        }
        bin_docs = {
            ("ITEM-A", "WH-01"): [{"_id": "B1", "current_qty": 30, "current_value": 3000}],
            ("ITEM-B", "WH-01"): [{"_id": "B2", "current_qty": 30, "current_value": 6000}],
        }

        with _service_context(sr_doc=sr_doc, bin_docs=bin_docs) as (service, _repos):
            result = service.submit_reconciliation("SREC-002")

            assert len(result["items"]) == 2
            assert result["total_variance_qty"] == Decimal(10)  # +20 - 10
            # ITEM-A: +20 x 100 = 2000, ITEM-B: -10 x 200 = -2000 -> 0
            assert result["total_variance_value"] == Decimal(0)

    def test_단가_미지정시_이동평균_사용(self) -> None:
        """valuation_rate=0이면 기존 이동평균 단가를 사용한다."""
        sr_doc = {
            "_id": "SREC-003",
            "status": "draft",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "warehouse": "WH-01",
                    "qty": 150,
                    "valuation_rate": 0,  # 미지정
                }
            ],
        }
        bin_docs = {
            ("ITEM-A", "WH-01"): [
                {
                    "_id": "B1",
                    "current_qty": 100,
                    "current_value": 200000,  # 평균 단가 2000
                }
            ]
        }

        with _service_context(sr_doc=sr_doc, bin_docs=bin_docs) as (service, _repos):
            result = service.submit_reconciliation("SREC-003")

            line = result["items"][0]
            # 변경 가치 = 150 x 2000 = 300000
            # 차이 가치 = 300000 - 200000 = 100000
            assert line["variance_value"] == Decimal(100000)

    def test_차이_0이면_SLE_생성_생략(self) -> None:
        """차이가 0인 라인은 SLE를 생성하지 않는다 (성능 최적화)."""
        sr_doc = {
            "_id": "SREC-004",
            "status": "draft",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "warehouse": "WH-01",
                    "qty": 100,
                    "valuation_rate": 1000,
                }
            ],
        }
        bin_docs = {
            ("ITEM-A", "WH-01"): [{"_id": "B1", "current_qty": 100, "current_value": 100000}]
        }

        with _service_context(sr_doc=sr_doc, bin_docs=bin_docs) as (service, repos):
            result = service.submit_reconciliation("SREC-004")

            assert result["items"][0]["variance_qty"] == Decimal(0)
            assert result["items"][0]["sle_id"] is None
            sle_repo = repos["stock_ledger_entries"]
            sle_repo.insert.assert_not_called()


# ======================================================================
# 예외 케이스
# ======================================================================


class Test실사제출_예외:
    """예외 시나리오."""

    def test_미존재_문서_404(self) -> None:
        """존재하지 않는 실사 문서는 404 발생."""
        with _service_context(sr_doc=None) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.submit_reconciliation("SREC-NONE")
            assert exc_info.value.status_code == 404

    def test_이미_제출된_문서_422(self) -> None:
        """status=submitted인 문서 재제출 시 422."""
        sr_doc = {
            "_id": "SREC-DONE",
            "status": "submitted",
            "items": [{"item_code": "X", "warehouse": "Y", "qty": 1, "valuation_rate": 1}],
        }
        with _service_context(sr_doc=sr_doc) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.submit_reconciliation("SREC-DONE")
            assert exc_info.value.status_code == 422
            assert exc_info.value.error == "ERR-STK-RECON-001"

    def test_라인_없음_422(self) -> None:
        """라인이 빈 실사 문서는 422 발생."""
        sr_doc = {"_id": "SREC-EMPTY", "status": "draft", "items": []}
        with _service_context(sr_doc=sr_doc) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.submit_reconciliation("SREC-EMPTY")
            assert exc_info.value.status_code == 422
            assert exc_info.value.error == "ERR-STK-RECON-002"

    def test_라인_필수필드_누락_422(self) -> None:
        """item_code 또는 warehouse가 누락된 라인은 422 발생."""
        sr_doc = {
            "_id": "SREC-BAD",
            "status": "draft",
            "items": [{"qty": 10, "valuation_rate": 100}],
        }
        with _service_context(sr_doc=sr_doc) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.submit_reconciliation("SREC-BAD")
            assert exc_info.value.error == "ERR-STK-RECON-003"


class Test차이미리보기:
    """calculate_variance_summary는 커밋 없이 차이만 반환한다."""

    def test_차이_요약_조회(self) -> None:
        """양수/음수/0 차이 카운트가 정확하다."""
        sr_doc = {
            "_id": "SREC-PRV",
            "status": "draft",
            "items": [
                {"item_code": "A", "warehouse": "W", "qty": 50, "valuation_rate": 10},
                {"item_code": "B", "warehouse": "W", "qty": 30, "valuation_rate": 10},
                {"item_code": "C", "warehouse": "W", "qty": 20, "valuation_rate": 10},
            ],
        }
        bin_docs = {
            ("A", "W"): [{"current_qty": 30, "current_value": 300}],  # +20
            ("B", "W"): [{"current_qty": 50, "current_value": 500}],  # -20
            ("C", "W"): [{"current_qty": 20, "current_value": 200}],  # 0
        }

        with _service_context(sr_doc=sr_doc, bin_docs=bin_docs) as (service, repos):
            result = service.calculate_variance_summary("SREC-PRV")

            assert result["positive_count"] == 1
            assert result["negative_count"] == 1
            assert result["zero_count"] == 1
            assert result["net_variance_qty"] == Decimal(0)  # +20 -20 +0
            assert len(result["items"]) == 3

            # 미리보기는 SLE/bin 변경 없음
            sr_repo = repos["stock_reconciliations"]
            sr_repo.update_by_id.assert_not_called()

    def test_미존재_문서는_404(self) -> None:
        """존재하지 않는 문서는 404."""
        with _service_context(sr_doc=None) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.calculate_variance_summary("SREC-NONE")
            assert exc_info.value.status_code == 404
