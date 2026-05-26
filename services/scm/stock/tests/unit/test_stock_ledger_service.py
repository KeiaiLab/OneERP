"""재고 원장 서비스(StockLedgerService) 단위 테스트.

이동평균법 기반 재고 평가 엔진의 정확성을 검증한다.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@contextmanager
def _service_context(
    *,
    pr_doc: dict | None = None,
    dn_doc: dict | None = None,
    bin_docs: list[dict] | None = None,
):
    """mock을 유지하며 서비스 인스턴스와 리포지토리를 제공한다."""
    with (
        patch("oneerp_stock_app.services.stock_ledger_service.Repository") as mock_repo_cls,
        patch(
            "oneerp_stock_app.services.stock_ledger_service.generate_name",
            side_effect=lambda prefix, **kw: f"{prefix}-2026-00001",
        ),
    ):
        repos: dict[str, MagicMock] = {}
        repo_docs: dict[str, dict | None] = {
            "purchase_receipts": pr_doc,
            "delivery_notes": dn_doc,
        }

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name in repos:
                return repos[collection_name]
            repo = MagicMock()
            repos[collection_name] = repo

            if collection_name in repo_docs:
                repo.find_by_id.return_value = repo_docs[collection_name]

            if collection_name == "stock_bins":
                repo.find_many.return_value = bin_docs if bin_docs is not None else []

            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

        service = StockLedgerService(tenant_id="test-tenant")
        yield service, repos


class Test입고_이동평균_계산:
    """입고 시 이동평균 단가 계산을 검증한다."""

    def test_입고_payload로_원장_생성(self) -> None:
        """이벤트 payload만으로도 입고 원장 생성이 가능해야 한다."""
        items = [{"item_code": "ITEM-EVT", "warehouse": "WH-01", "qty": 4, "rate": 2500.0}]

        with _service_context(bin_docs=[]) as (service, repos):
            sle_ids = service.process_receipt_payload("PR-EVT-001", items)

            assert len(sle_ids) == 1

            sle_repo = repos["stock_ledger_entries"]
            sle_repo.insert.assert_called_once()
            sle_doc = sle_repo.insert.call_args[0][0]
            assert sle_doc.voucher_no == "PR-EVT-001"
            assert sle_doc.item_code == "ITEM-EVT"
            assert sle_doc.balance_qty == 4
            assert sle_doc.balance_value == 10000

            bin_repo = repos["stock_bins"]
            bin_repo.insert.assert_called_once()
            bin_doc = bin_repo.insert.call_args[0][0]
            assert bin_doc.item_code == "ITEM-EVT"
            assert bin_doc.current_qty == 4
            assert bin_doc.current_value == 10000

    def test_입고_이동평균_계산(self) -> None:
        """100개@10원 + 50개@20원 → 평균 13.33원."""
        pr_doc = {
            "_id": "PRCP-001",
            "items": [{"item_code": "ITEM-A", "warehouse": "WH-01", "qty": 50, "rate": 20.0}],
            "warehouse": "WH-01",
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 100.0, "current_value": 1000.0}]

        with _service_context(pr_doc=pr_doc, bin_docs=bin_docs) as (service, repos):
            sle_ids = service.process_receipt("PRCP-001")

            assert len(sle_ids) == 1

            # SLE 생성 검증
            sle_repo = repos["stock_ledger_entries"]
            sle_repo.insert.assert_called_once()
            sle_doc = sle_repo.insert.call_args[0][0]
            assert sle_doc.balance_qty == 150
            assert sle_doc.balance_value == 2000  # 1000 + 50*20
            # 이동평균 단가: 2000/150 ≈ 13.33
            assert abs(float(sle_doc.balance_value / sle_doc.balance_qty) - 13.33) < 0.01

            # stock_bin 갱신 검증
            bin_repo = repos["stock_bins"]
            bin_repo.update_by_id.assert_called_once()
            update_args = bin_repo.update_by_id.call_args[0]
            assert update_args[0] == "SBIN-001"
            update_data = update_args[1]
            assert update_data["current_qty"] == 150
            assert update_data["current_value"] == 2000
            assert abs(float(update_data["valuation_rate"]) - 13.333333333333334) < 0.01

    def test_입고_sle_valuation_rate는_이동평균_단가(self) -> None:
        """SLE의 valuation_rate는 입고단가가 아니라 이동평균 단가여야 한다."""
        pr_doc = {
            "_id": "PRCP-004",
            "items": [{"item_code": "ITEM-A", "warehouse": "WH-01", "qty": 50, "rate": 20.0}],
            "warehouse": "WH-01",
        }
        # 기존 잔고: 100개 @ 10원 = 1000원
        bin_docs = [{"_id": "SBIN-001", "current_qty": 100.0, "current_value": 1000.0}]

        with _service_context(pr_doc=pr_doc, bin_docs=bin_docs) as (service, repos):
            service.process_receipt("PRCP-004")

            sle_repo = repos["stock_ledger_entries"]
            sle_doc = sle_repo.insert.call_args[0][0]
            # 이동평균 단가 = (1000 + 50*20) / (100 + 50) = 2000/150 ≈ 13.33
            # SLE.valuation_rate에 입고단가(20)가 아닌 이동평균(≈13.33)이 저장되어야 함
            assert abs(float(sle_doc.valuation_rate) - 13.333333333333334) < 0.01
            assert float(sle_doc.valuation_rate) != 20.0

    def test_입고_첫번째(self) -> None:
        """stock_bin 없는 상태에서 첫 입고 → 신규 생성."""
        pr_doc = {
            "_id": "PRCP-002",
            "items": [{"item_code": "ITEM-NEW", "warehouse": "WH-01", "qty": 100, "rate": 10.0}],
            "warehouse": "WH-01",
        }

        with _service_context(pr_doc=pr_doc, bin_docs=[]) as (service, repos):
            sle_ids = service.process_receipt("PRCP-002")

            assert len(sle_ids) == 1

            # stock_bin 신규 생성 검증
            bin_repo = repos["stock_bins"]
            bin_repo.insert.assert_called_once()
            bin_doc = bin_repo.insert.call_args[0][0]
            assert bin_doc.item_code == "ITEM-NEW"
            assert bin_doc.current_qty == 100
            assert bin_doc.current_value == 1000
            assert bin_doc.valuation_rate == 10


class Test출고_이동평균_적용:
    """출고 시 이동평균 단가 적용을 검증한다."""

    def test_출고_이동평균_적용(self) -> None:
        """잔고 150개/2000원에서 30개 출고 → 잔고 120개, 가치 1600원."""
        dn_doc = {
            "_id": "DN-001",
            "items": [{"item_code": "ITEM-A", "warehouse": "WH-01", "qty": 30}],
            "warehouse": "WH-01",
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 150.0, "current_value": 2000.0}]

        with _service_context(dn_doc=dn_doc, bin_docs=bin_docs) as (service, repos):
            sle_ids = service.process_delivery("DN-001")

            assert len(sle_ids) == 1

            # SLE 검증: 출고 수량은 음수
            sle_repo = repos["stock_ledger_entries"]
            sle_doc = sle_repo.insert.call_args[0][0]
            assert sle_doc.qty_change == -30
            assert sle_doc.balance_qty == 120
            # 출고 후 잔고 가치: 120 * (2000/150) = 1600
            assert abs(float(sle_doc.balance_value) - 1600.0) < 0.01


class Test재고_부족_예외:
    """재고 부족 시 예외를 검증한다."""

    def test_재고_부족_예외(self) -> None:
        """잔고 초과 출고 시 OneERPError(ERR-STK-001)."""
        dn_doc = {
            "_id": "DN-002",
            "items": [{"item_code": "ITEM-A", "warehouse": "WH-01", "qty": 200}],
            "warehouse": "WH-01",
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 100.0, "current_value": 1000.0}]

        with _service_context(dn_doc=dn_doc, bin_docs=bin_docs) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.process_delivery("DN-002")
            assert exc_info.value.status_code == 422
            assert exc_info.value.error == "ERR-STK-001"
            assert "재고 부족" in (exc_info.value.detail or "")

    def test_빈_재고_출고(self) -> None:
        """잔고 0에서 출고 시도 → OneERPError(ERR-STK-001)."""
        dn_doc = {
            "_id": "DN-003",
            "items": [{"item_code": "ITEM-B", "warehouse": "WH-01", "qty": 10}],
            "warehouse": "WH-01",
        }

        with _service_context(dn_doc=dn_doc, bin_docs=[]) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.process_delivery("DN-003")
            assert exc_info.value.status_code == 422
            assert exc_info.value.error == "ERR-STK-001"
            assert "재고 부족" in (exc_info.value.detail or "")


class Test배치_유통기한_경고:
    """BR-STK-014: 만료 배치 출고 시 경고만 남기고 차단하지 않음을 검증한다."""

    def test_만료_배치_출고_경고만(self) -> None:
        """유통기한 만료 배치 출고 시 차단 없이 경고 로그만 남긴다."""
        dn_doc = {
            "_id": "DN-BATCH-001",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "warehouse": "WH-01",
                    "qty": 10,
                    "batch_no": "BATCH-EXP-001",
                },
            ],
            "warehouse": "WH-01",
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 100.0, "current_value": 1000.0}]

        with (
            patch("oneerp_stock_app.services.stock_ledger_service.Repository") as mock_repo_cls,
            patch(
                "oneerp_stock_app.services.stock_ledger_service.generate_name",
                side_effect=lambda prefix, **kw: f"{prefix}-2026-00001",
            ),
        ):
            repos: dict[str, MagicMock] = {}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name in repos:
                    return repos[collection_name]
                repo = MagicMock()
                repos[collection_name] = repo

                if collection_name == "delivery_notes":
                    repo.find_by_id.return_value = dn_doc
                elif collection_name == "stock_bins":
                    repo.find_many.return_value = bin_docs
                elif collection_name == "serial_batch_bundles":
                    # 유통기한이 과거인 배치
                    repo.find_many.return_value = [
                        {"batch_no": "BATCH-EXP-001", "expiry_date": "2025-01-01"}
                    ]

                return repo

            mock_repo_cls.side_effect = _repo_factory
            from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

            service = StockLedgerService(tenant_id="test-tenant")

            # 차단(raise)이 아니라 정상 출고되어야 한다
            sle_ids = service.process_delivery("DN-BATCH-001")
            assert len(sle_ids) == 1

    def test_만료_배치_출고_경고_로그_발생(self) -> None:
        """유통기한 만료 배치 출고 시 logger.warning이 호출된다."""
        dn_doc = {
            "_id": "DN-BATCH-002",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "warehouse": "WH-01",
                    "qty": 5,
                    "batch_no": "BATCH-EXP-002",
                },
            ],
            "warehouse": "WH-01",
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 50.0, "current_value": 500.0}]

        with (
            patch("oneerp_stock_app.services.stock_ledger_service.Repository") as mock_repo_cls,
            patch(
                "oneerp_stock_app.services.stock_ledger_service.generate_name",
                side_effect=lambda prefix, **kw: f"{prefix}-2026-00001",
            ),
            patch("oneerp_stock_app.services.stock_ledger_service.logger") as mock_logger,
        ):
            repos: dict[str, MagicMock] = {}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name in repos:
                    return repos[collection_name]
                repo = MagicMock()
                repos[collection_name] = repo

                if collection_name == "delivery_notes":
                    repo.find_by_id.return_value = dn_doc
                elif collection_name == "stock_bins":
                    repo.find_many.return_value = bin_docs
                elif collection_name == "serial_batch_bundles":
                    repo.find_many.return_value = [
                        {"batch_no": "BATCH-EXP-002", "expiry_date": "2024-06-01"}
                    ]

                return repo

            mock_repo_cls.side_effect = _repo_factory
            from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

            service = StockLedgerService(tenant_id="test-tenant")
            service.process_delivery("DN-BATCH-002")

            # logger.warning이 배치 유통기한 관련으로 호출되었는지 검증
            mock_logger.warning.assert_any_call(
                "배치 '%s' 유통기한 만료 (%s): 출고를 허용하지만 주의가 필요합니다",
                "BATCH-EXP-002",
                "2024-06-01",
            )


class Test다중_창고:
    """같은 품목 다른 창고 독립 관리를 검증한다."""

    def test_다중_창고(self) -> None:
        """같은 품목이 다른 창고에서 독립적으로 관리된다."""
        pr_doc = {
            "_id": "PRCP-003",
            "items": [
                {"item_code": "ITEM-A", "warehouse": "WH-01", "qty": 50, "rate": 10.0},
                {"item_code": "ITEM-A", "warehouse": "WH-02", "qty": 30, "rate": 15.0},
            ],
            "warehouse": "",
        }

        # 두 창고 모두 빈 상태 — find_many를 warehouse별로 분기
        with (
            patch("oneerp_stock_app.services.stock_ledger_service.Repository") as mock_repo_cls,
            patch(
                "oneerp_stock_app.services.stock_ledger_service.generate_name",
                side_effect=lambda prefix, **kw: f"{prefix}-2026-00001",
            ),
        ):
            repos: dict[str, MagicMock] = {}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name in repos:
                    return repos[collection_name]
                repo = MagicMock()
                repos[collection_name] = repo

                if collection_name == "purchase_receipts":
                    repo.find_by_id.return_value = pr_doc
                elif collection_name == "stock_bins":
                    repo.find_many.return_value = []  # 빈 상태

                return repo

            mock_repo_cls.side_effect = _repo_factory
            from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

            service = StockLedgerService(tenant_id="test-tenant")
            sle_ids = service.process_receipt("PRCP-003")

            assert len(sle_ids) == 2

            # SLE가 2건 생성됨
            sle_repo = repos["stock_ledger_entries"]
            assert sle_repo.insert.call_count == 2

            # 각 SLE의 잔고가 독립적으로 계산됨
            first_sle = sle_repo.insert.call_args_list[0][0][0]
            second_sle = sle_repo.insert.call_args_list[1][0][0]

            assert first_sle.warehouse == "WH-01"
            assert first_sle.balance_qty == 50
            assert first_sle.balance_value == 500

            assert second_sle.warehouse == "WH-02"
            assert second_sle.balance_qty == 30
            assert second_sle.balance_value == 450

            # stock_bin 신규 생성 2건
            bin_repo = repos["stock_bins"]
            assert bin_repo.insert.call_count == 2


# -- StockEntry(process_stock_entry) 테스트 --


@contextmanager
def _se_service_context(
    *,
    se_doc: dict | None = None,
    bin_docs: list[dict] | None = None,
):
    """StockEntry 테스트용 mock 컨텍스트."""
    with (
        patch("oneerp_stock_app.services.stock_ledger_service.Repository") as mock_repo_cls,
        patch(
            "oneerp_stock_app.services.stock_ledger_service.generate_name",
            side_effect=lambda prefix, **kw: f"{prefix}-2026-00001",
        ),
    ):
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name in repos:
                return repos[collection_name]
            repo = MagicMock()
            repos[collection_name] = repo

            if collection_name == "stock_entries":
                repo.find_by_id.return_value = se_doc
            elif collection_name == "stock_bins":
                repo.find_many.return_value = bin_docs if bin_docs is not None else []

            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

        service = StockLedgerService(tenant_id="test-tenant")
        yield service, repos


class TestStockEntry_입고:
    """BR-STK-011: StockEntry receipt 유형 테스트."""

    def test_receipt_입고_sle_생성(self) -> None:
        """receipt 유형은 target_warehouse에 입고 SLE를 생성한다."""
        se_doc = {
            "_id": "SE-001",
            "entry_type": "receipt",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "target_warehouse": "WH-01",
                    "qty": 100,
                    "valuation_rate": 10.0,
                },
            ],
        }

        with _se_service_context(se_doc=se_doc, bin_docs=[]) as (service, repos):
            sle_ids = service.process_stock_entry("SE-001")
            assert len(sle_ids) == 1

            sle_repo = repos["stock_ledger_entries"]
            sle_doc = sle_repo.insert.call_args[0][0]
            assert sle_doc.qty_change == 100
            assert sle_doc.balance_qty == 100
            assert sle_doc.voucher_type == "StockEntry"


class TestStockEntry_출고:
    """BR-STK-011: StockEntry issue 유형 테스트."""

    def test_issue_출고_sle_생성(self) -> None:
        """issue 유형은 source_warehouse에서 출고 SLE를 생성한다."""
        se_doc = {
            "_id": "SE-002",
            "entry_type": "issue",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "source_warehouse": "WH-01",
                    "qty": 30,
                },
            ],
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 100.0, "current_value": 1000.0}]

        with _se_service_context(se_doc=se_doc, bin_docs=bin_docs) as (service, repos):
            sle_ids = service.process_stock_entry("SE-002")
            assert len(sle_ids) == 1

            sle_repo = repos["stock_ledger_entries"]
            sle_doc = sle_repo.insert.call_args[0][0]
            assert sle_doc.qty_change == -30
            assert sle_doc.balance_qty == 70

    def test_issue_재고부족_에러(self) -> None:
        """재고 부족 시 OneERPError(ERR-STK-001)를 발생시킨다."""
        se_doc = {
            "_id": "SE-003",
            "entry_type": "issue",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "source_warehouse": "WH-01",
                    "qty": 200,
                },
            ],
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 50.0, "current_value": 500.0}]

        with _se_service_context(se_doc=se_doc, bin_docs=bin_docs) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.process_stock_entry("SE-003")
            assert exc_info.value.error == "ERR-STK-001"


class TestStockEntry_이동:
    """BR-STK-011: StockEntry transfer 유형 테스트."""

    def test_transfer_출고입고_sle_2건(self) -> None:
        """transfer 유형은 출고 + 입고 SLE 2건을 생성한다."""
        se_doc = {
            "_id": "SE-004",
            "entry_type": "transfer",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "source_warehouse": "WH-01",
                    "target_warehouse": "WH-02",
                    "qty": 20,
                },
            ],
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 100.0, "current_value": 1000.0}]

        with _se_service_context(se_doc=se_doc, bin_docs=bin_docs) as (service, repos):
            sle_ids = service.process_stock_entry("SE-004")
            assert len(sle_ids) == 2

            sle_repo = repos["stock_ledger_entries"]
            # 첫 번째: 출고 (음수)
            first_sle = sle_repo.insert.call_args_list[0][0][0]
            assert first_sle.qty_change == -20
            assert first_sle.warehouse == "WH-01"

            # 두 번째: 입고 (양수)
            second_sle = sle_repo.insert.call_args_list[1][0][0]
            assert second_sle.qty_change == 20
            assert second_sle.warehouse == "WH-02"


class TestStockEntry_제조:
    """BR-STK-011: StockEntry manufacture 유형 테스트."""

    def test_manufacture_자재출고_완제품입고(self) -> None:
        """manufacture 유형: source_warehouse가 있으면 출고, target_warehouse가 있으면 입고."""
        se_doc = {
            "_id": "SE-005",
            "entry_type": "manufacture",
            "items": [
                {
                    "item_code": "RM-01",
                    "source_warehouse": "WH-RM",
                    "target_warehouse": "",
                    "qty": 50,
                    "valuation_rate": 10,
                },
                {
                    "item_code": "FG-01",
                    "source_warehouse": "",
                    "target_warehouse": "WH-FG",
                    "qty": 10,
                    "valuation_rate": 100,
                },
            ],
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 200.0, "current_value": 2000.0}]

        with _se_service_context(se_doc=se_doc, bin_docs=bin_docs) as (service, _repos):
            sle_ids = service.process_stock_entry("SE-005")
            # 자재 출고 1건 + 완제품 입고 1건 = 2건
            assert len(sle_ids) == 2


class TestStockEntry_폐기:
    """BR-STK-011: StockEntry scrap 유형 테스트."""

    def test_scrap_출고_처리(self) -> None:
        """scrap 유형은 출고와 동일하게 처리한다."""
        se_doc = {
            "_id": "SE-006",
            "entry_type": "scrap",
            "items": [
                {
                    "item_code": "ITEM-A",
                    "source_warehouse": "WH-01",
                    "qty": 5,
                },
            ],
        }
        bin_docs = [{"_id": "SBIN-001", "current_qty": 100.0, "current_value": 1000.0}]

        with _se_service_context(se_doc=se_doc, bin_docs=bin_docs) as (service, repos):
            sle_ids = service.process_stock_entry("SE-006")
            assert len(sle_ids) == 1

            sle_repo = repos["stock_ledger_entries"]
            sle_doc = sle_repo.insert.call_args[0][0]
            assert sle_doc.qty_change == -5
            assert sle_doc.balance_qty == 95


class TestStockEntry_미존재:
    """StockEntry 미존재 시 예외를 검증한다."""

    def test_미존재_stock_entry(self) -> None:
        """존재하지 않는 StockEntry는 404를 발생시킨다."""
        with _se_service_context(se_doc=None) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.process_stock_entry("SE-NONEXIST")
            assert exc_info.value.status_code == 404


class TestStockEntry_미지원_유형:
    """지원하지 않는 entry_type 시 예외를 검증한다."""

    def test_미지원_entry_type(self) -> None:
        """알 수 없는 entry_type은 422를 발생시킨다."""
        se_doc = {
            "_id": "SE-BAD",
            "entry_type": "unknown_type",
            "items": [],
        }
        with _se_service_context(se_doc=se_doc) as (service, _repos):
            with pytest.raises(OneERPError) as exc_info:
                service.process_stock_entry("SE-BAD")
            assert exc_info.value.status_code == 422
            assert exc_info.value.error == "ERR-STK-002"
