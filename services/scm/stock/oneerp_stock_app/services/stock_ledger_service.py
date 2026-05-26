"""재고 원장 서비스 — 이동평균법 기반 재고 평가 엔진.

입고/출고 시 재고 원장(SLE)을 생성하고, stock_bins를 통해
품목별/창고별 현재 잔고를 O(1)로 관리한다.

L2 비즈니스 룰 매핑:
- BR-STK-001: 이동평균법 입고 (new_value = cur + qty*rate, new_rate = new_value/new_qty)
- BR-STK-002: 이동평균법 출고 (avg_rate = cur_value/cur_qty, 재고 부족 시 에러)
- BR-STK-003: SLE 불변성 (수정/삭제 API 없음, 읽기 전용)
- BR-STK-004: stock_bins 동기 갱신 (SLE 생성 시 current_qty/value/rate 갱신)
- BR-STK-012: 제조 자재 출고 (process_material_issue)
- BR-STK-013: 제조 완제품 입고 (process_production_receipt)
- BR-STK-014: 배치 유통기한 검증 (만료 배치 출고 시 경고만, 차단 안 함)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.document import BaseDocument
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from .valuation_helpers import apply_issue_avg, apply_receipt_avg

logger = logging.getLogger(__name__)


class _StockBin(BaseDocument):
    """품목별/창고별 현재 잔고 캐시 모델."""

    item_code: str = ""
    warehouse: str = ""
    current_qty: Decimal = Decimal(0)
    current_value: Decimal = Decimal(0)
    valuation_rate: Decimal = Decimal(0)


class StockLedgerService:
    """이동평균법 기반 재고 평가 엔진.

    입고/출고 전표 처리 시 SLE를 생성하고 stock_bins를 갱신한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._sle_repo = Repository("stock_ledger_entries", tenant_id=tenant_id)
        self._bin_repo = Repository("stock_bins", tenant_id=tenant_id)

    def process_receipt_payload(
        self,
        purchase_receipt_id: str,
        items: list[dict[str, Any]],
    ) -> list[str]:
        """이벤트 payload 기반으로 입고 원장을 생성한다."""
        return self._process_receipt_items(purchase_receipt_id, items)

    def process_receipt(self, purchase_receipt_id: str) -> list[str]:
        """BR-STK-001/004: 입고전표를 처리하여 SLE를 생성한다.

        BR-STK-001: 이동평균법 입고 계산.
        BR-STK-004: stock_bins 동기 갱신.

        Returns:
            생성된 SLE ID 목록
        """
        pr_repo = Repository("purchase_receipts", tenant_id=self._tenant_id)
        pr_doc = pr_repo.find_by_id(purchase_receipt_id)
        if not pr_doc:
            msg = f"입고전표를 찾을 수 없습니다: {purchase_receipt_id}"
            raise_not_found(msg)

        return self._process_receipt_items(purchase_receipt_id, pr_doc.get("items", []))

    def _process_receipt_items(
        self,
        purchase_receipt_id: str,
        items: list[dict[str, Any]],
    ) -> list[str]:
        """입고 아이템 목록을 기준으로 재고 원장을 생성한다."""

        sle_ids: list[str] = []
        for item in items:
            item_code = item.get("item_code", "")
            warehouse = item.get("warehouse", "")
            qty = Decimal(str(item.get("qty", 0)))
            rate = Decimal(str(item.get("rate", 0)))
            qty * rate

            # 현재 잔고 조회
            cur_qty, cur_value = self._get_current_balance(item_code, warehouse)

            # 이동평균 재계산 — core.valuation.MovingAverageStrategy 위임 (M3 Wave A)
            # amount 변수는 apply_receipt_avg 내부에서 qty*rate 로 재계산되므로
            # 외부 로직과 동일하나 단일 소스로 수렴됨.
            new_qty, new_rate, new_value = apply_receipt_avg(
                prev_qty=cur_qty,
                prev_rate=Decimal(0),  # 입고 공식에서 미사용 (new_rate = new_value/new_qty)
                prev_value=cur_value,
                qty=qty,
                rate=rate,
            )

            # SLE 생성 — valuation_rate는 이동평균 단가(new_rate)를 저장
            sle_id = self._create_sle(
                item_code=item_code,
                warehouse=warehouse,
                qty_change=qty,
                rate=new_rate,
                balance_qty=new_qty,
                balance_value=new_value,
                voucher_type="PurchaseReceipt",
                voucher_no=purchase_receipt_id,
            )
            sle_ids.append(sle_id)

            # stock_bin 갱신
            self._update_stock_bin(item_code, warehouse, new_qty, new_value, new_rate)

        logger.info(
            "입고 처리 완료: %s (SLE %d건 생성)",
            purchase_receipt_id,
            len(sle_ids),
        )
        return sle_ids

    def process_delivery(self, delivery_note_id: str) -> list[str]:
        """납품전표를 처리하여 SLE를 생성한다.

        BR-STK-014: 배치 유통기한 초과 품목은 경고 로그만 남기고 출고 허용.
        재고 부족 시 OneERPError를 발생시킨다.

        Returns:
            생성된 SLE ID 목록
        """
        dn_repo = Repository("delivery_notes", tenant_id=self._tenant_id)
        dn_doc = dn_repo.find_by_id(delivery_note_id)
        if not dn_doc:
            msg = f"납품전표를 찾을 수 없습니다: {delivery_note_id}"
            raise_not_found(msg)

        sle_ids: list[str] = []
        for item in dn_doc.get("items", []):
            item_code = item.get("item_code", "")
            warehouse = item.get("warehouse", "") or dn_doc.get("warehouse", "")
            qty = Decimal(str(item.get("qty", 0)))

            # BR-STK-014: 배치 유통기한 검증 — 만료 배치는 경고만, 차단 안 함
            batch_no = item.get("batch_no", "")
            if batch_no:
                batch_repo = Repository("serial_batch_bundles", tenant_id=self._tenant_id)
                batches = batch_repo.find_many({"batch_no": batch_no}, limit=1)
                if batches:
                    expiry = batches[0].get("expiry_date")
                    if expiry and str(expiry) < str(datetime.now(tz=UTC).date()):
                        logger.warning(
                            "배치 '%s' 유통기한 만료 (%s): 출고를 허용하지만 주의가 필요합니다",
                            batch_no,
                            expiry,
                        )

            # 현재 잔고 조회
            cur_qty, cur_value = self._get_current_balance(item_code, warehouse)

            # 재고 부족 검증
            if cur_qty < qty:
                msg = f"재고 부족: {item_code} @ {warehouse} (잔고: {cur_qty}, 요청: {qty})"
                raise_unprocessable("ERR-STK-001", msg)

            # 이동평균 단가로 출고 평가
            # 이동평균 출고 — core.valuation Strategy 위임 (M3 Wave A)
            new_qty, _new_valuation_rate, new_value, avg_rate = apply_issue_avg(
                prev_qty=cur_qty,
                prev_value=cur_value,
                qty=qty,
            )

            # SLE 생성 (출고는 음수)
            sle_id = self._create_sle(
                item_code=item_code,
                warehouse=warehouse,
                qty_change=-qty,
                rate=avg_rate,
                balance_qty=new_qty,
                balance_value=new_value,
                voucher_type="DeliveryNote",
                voucher_no=delivery_note_id,
            )
            sle_ids.append(sle_id)

            # stock_bin 갱신
            self._update_stock_bin(item_code, warehouse, new_qty, new_value, avg_rate)

        logger.info(
            "출고 처리 완료: %s (SLE %d건 생성)",
            delivery_note_id,
            len(sle_ids),
        )
        return sle_ids

    def process_material_issue(
        self,
        work_order_id: str,
        items: list[dict[str, Any]],
        warehouse: str = "WIP",
    ) -> list[str]:
        """BR-STK-012: 자재 출고를 처리하여 SLE를 생성한다.

        작업지시의 자재 출고 시 각 아이템에 대해 재고를 차감한다.
        이동평균 단가로 출고 평가하며, 재고 부족 시 OneERPError를 발생시킨다.

        Args:
            work_order_id: 작업지시 ID (voucher_no로 사용)
            items: 출고 자재 목록 [{item_code, issued_qty}]
            warehouse: 출고 창고 (기본값: WIP)

        Returns:
            생성된 SLE ID 목록
        """
        sle_ids: list[str] = []
        for item in items:
            item_code = item.get("item_code", "")
            qty = Decimal(str(item.get("issued_qty", 0)))

            # 현재 잔고 조회
            cur_qty, cur_value = self._get_current_balance(item_code, warehouse)

            # 재고 부족 검증
            if cur_qty < qty:
                msg = f"재고 부족: {item_code} @ {warehouse} (잔고: {cur_qty}, 요청: {qty})"
                raise_unprocessable("ERR-STK-001", msg)

            # 이동평균 단가로 출고 평가
            # 이동평균 출고 — core.valuation Strategy 위임 (M3 Wave A)
            new_qty, _new_valuation_rate, new_value, avg_rate = apply_issue_avg(
                prev_qty=cur_qty,
                prev_value=cur_value,
                qty=qty,
            )

            # SLE 생성 (출고는 음수)
            sle_id = self._create_sle(
                item_code=item_code,
                warehouse=warehouse,
                qty_change=-qty,
                rate=avg_rate,
                balance_qty=new_qty,
                balance_value=new_value,
                voucher_type="MaterialIssue",
                voucher_no=work_order_id,
            )
            sle_ids.append(sle_id)

            # stock_bin 갱신
            self._update_stock_bin(item_code, warehouse, new_qty, new_value, avg_rate)

        logger.info(
            "자재 출고 처리 완료: %s (SLE %d건 생성)",
            work_order_id,
            len(sle_ids),
        )
        return sle_ids

    def process_production_receipt(
        self,
        work_order_id: str,
        item_code: str,
        produced_qty: Decimal,
        warehouse: str = "FG",
        rate: Decimal = Decimal(0),
    ) -> list[str]:
        """BR-STK-013: 완제품 입고를 처리하여 SLE를 생성한다.

        작업지시 완료 시 생산된 완제품을 입고 처리한다.
        이동평균법으로 단가를 재계산한다.

        Args:
            work_order_id: 작업지시 ID (voucher_no로 사용)
            item_code: 완제품 품목 코드
            produced_qty: 생산 수량
            warehouse: 입고 창고 (기본값: FG)
            rate: 입고 단가 (0이면 기존 이동평균 단가 유지)

        Returns:
            생성된 SLE ID 목록
        """
        # 현재 잔고 조회
        cur_qty, cur_value = self._get_current_balance(item_code, warehouse)

        # 입고 단가가 0이면 기존 이동평균 단가 사용
        effective_rate = rate if rate > 0 else (cur_value / cur_qty if cur_qty else Decimal(0))
        produced_qty * effective_rate

        # 이동평균 재계산 — core.valuation Strategy 위임 (M3 Wave A)
        new_qty, new_rate, new_value = apply_receipt_avg(
            prev_qty=cur_qty,
            prev_rate=Decimal(0),
            prev_value=cur_value,
            qty=produced_qty,
            rate=effective_rate,
        )

        # SLE 생성
        sle_id = self._create_sle(
            item_code=item_code,
            warehouse=warehouse,
            qty_change=produced_qty,
            rate=effective_rate,
            balance_qty=new_qty,
            balance_value=new_value,
            voucher_type="ProductionReceipt",
            voucher_no=work_order_id,
        )

        # stock_bin 갱신
        self._update_stock_bin(item_code, warehouse, new_qty, new_value, new_rate)

        logger.info(
            "완제품 입고 처리 완료: %s (품목: %s, 수량: %s)",
            work_order_id,
            item_code,
            produced_qty,
        )
        return [sle_id]

    def process_stock_entry(self, stock_entry_id: str) -> list[str]:
        """BR-STK-011: 재고이동(StockEntry)을 처리하여 SLE를 생성한다.

        entry_type에 따라 분기:
        - receipt: 입고 처리
        - issue: 출고 처리
        - transfer: source_warehouse에서 출고 + target_warehouse에 입고
        - manufacture: 자재 출고 + 완제품 입고
        - scrap: 폐기 출고 처리

        Args:
            stock_entry_id: 재고이동 문서 ID

        Returns:
            생성된 SLE ID 목록
        """
        se_repo = Repository("stock_entries", tenant_id=self._tenant_id)
        se_doc = se_repo.find_by_id(stock_entry_id)
        if not se_doc:
            msg = f"재고이동을 찾을 수 없습니다: {stock_entry_id}"
            raise_not_found(msg)

        entry_type = se_doc.get("entry_type", "")
        items = se_doc.get("items", [])

        handler = {
            "receipt": self._process_se_receipt,
            "issue": self._process_se_issue,
            "transfer": self._process_se_transfer,
            "manufacture": self._process_se_manufacture,
            "scrap": self._process_se_scrap,
        }.get(entry_type)

        if handler is None:
            msg = f"지원하지 않는 재고이동 유형입니다: {entry_type}"
            raise_unprocessable("ERR-STK-002", msg)
        else:
            sle_ids = handler(stock_entry_id, items)

        logger.info(
            "재고이동 처리 완료: %s (유형: %s, SLE %d건 생성)",
            stock_entry_id,
            entry_type,
            len(sle_ids),
        )
        return sle_ids

    def _process_se_receipt(self, voucher_no: str, items: list[dict[str, Any]]) -> list[str]:
        """재고이동 입고 처리 — process_receipt과 동일 이동평균 로직."""
        sle_ids: list[str] = []
        for item in items:
            item_code = item.get("item_code", "")
            warehouse = item.get("target_warehouse", "")
            qty = Decimal(str(item.get("qty", 0)))
            rate = Decimal(str(item.get("valuation_rate", 0)))
            qty * rate

            cur_qty, cur_value = self._get_current_balance(item_code, warehouse)
            # 이동평균 입고 — core.valuation Strategy 위임 (M3 Wave A)
            new_qty, new_rate, new_value = apply_receipt_avg(
                prev_qty=cur_qty,
                prev_rate=Decimal(0),
                prev_value=cur_value,
                qty=qty,
                rate=rate,
            )

            sle_id = self._create_sle(
                item_code=item_code,
                warehouse=warehouse,
                qty_change=qty,
                rate=new_rate,
                balance_qty=new_qty,
                balance_value=new_value,
                voucher_type="StockEntry",
                voucher_no=voucher_no,
            )
            sle_ids.append(sle_id)
            self._update_stock_bin(item_code, warehouse, new_qty, new_value, new_rate)
        return sle_ids

    def _process_se_issue(self, voucher_no: str, items: list[dict[str, Any]]) -> list[str]:
        """재고이동 출고 처리 — process_delivery와 동일 이동평균 로직."""
        sle_ids: list[str] = []
        for item in items:
            item_code = item.get("item_code", "")
            warehouse = item.get("source_warehouse", "")
            qty = Decimal(str(item.get("qty", 0)))

            cur_qty, cur_value = self._get_current_balance(item_code, warehouse)
            if cur_qty < qty:
                msg = f"재고 부족: {item_code} @ {warehouse} (잔고: {cur_qty}, 요청: {qty})"
                raise_unprocessable("ERR-STK-001", msg)

            # 이동평균 출고 — core.valuation Strategy 위임 (M3 Wave A)
            new_qty, _new_valuation_rate, new_value, avg_rate = apply_issue_avg(
                prev_qty=cur_qty,
                prev_value=cur_value,
                qty=qty,
            )

            sle_id = self._create_sle(
                item_code=item_code,
                warehouse=warehouse,
                qty_change=-qty,
                rate=avg_rate,
                balance_qty=new_qty,
                balance_value=new_value,
                voucher_type="StockEntry",
                voucher_no=voucher_no,
            )
            sle_ids.append(sle_id)
            self._update_stock_bin(item_code, warehouse, new_qty, new_value, avg_rate)
        return sle_ids

    def _process_se_transfer(self, voucher_no: str, items: list[dict[str, Any]]) -> list[str]:
        """재고이동 이동 처리 — source에서 출고 + target에 입고."""
        sle_ids: list[str] = []
        for item in items:
            item_code = item.get("item_code", "")
            source_wh = item.get("source_warehouse", "")
            target_wh = item.get("target_warehouse", "")
            qty = Decimal(str(item.get("qty", 0)))

            # 출고
            cur_qty, cur_value = self._get_current_balance(item_code, source_wh)
            if cur_qty < qty:
                msg = f"재고 부족: {item_code} @ {source_wh} (잔고: {cur_qty}, 요청: {qty})"
                raise_unprocessable("ERR-STK-001", msg)

            avg_rate = cur_value / cur_qty if cur_qty else Decimal(0)
            new_qty_src = cur_qty - qty
            new_value_src = new_qty_src * avg_rate

            sle_id = self._create_sle(
                item_code=item_code,
                warehouse=source_wh,
                qty_change=-qty,
                rate=avg_rate,
                balance_qty=new_qty_src,
                balance_value=new_value_src,
                voucher_type="StockEntry",
                voucher_no=voucher_no,
            )
            sle_ids.append(sle_id)
            self._update_stock_bin(item_code, source_wh, new_qty_src, new_value_src, avg_rate)

            # 입고 — 출고 시 이동평균 단가로 입고
            amount = qty * avg_rate
            tgt_qty, tgt_value = self._get_current_balance(item_code, target_wh)
            new_qty_tgt = tgt_qty + qty
            new_value_tgt = tgt_value + amount
            new_rate_tgt = new_value_tgt / new_qty_tgt if new_qty_tgt else Decimal(0)

            sle_id = self._create_sle(
                item_code=item_code,
                warehouse=target_wh,
                qty_change=qty,
                rate=new_rate_tgt,
                balance_qty=new_qty_tgt,
                balance_value=new_value_tgt,
                voucher_type="StockEntry",
                voucher_no=voucher_no,
            )
            sle_ids.append(sle_id)
            self._update_stock_bin(item_code, target_wh, new_qty_tgt, new_value_tgt, new_rate_tgt)
        return sle_ids

    def _process_se_manufacture(self, voucher_no: str, items: list[dict[str, Any]]) -> list[str]:
        """재고이동 제조 처리 — 자재 출고(source) + 완제품 입고(target)."""
        sle_ids: list[str] = []
        for item in items:
            item_code = item.get("item_code", "")
            source_wh = item.get("source_warehouse", "")
            target_wh = item.get("target_warehouse", "")
            qty = Decimal(str(item.get("qty", 0)))
            rate = Decimal(str(item.get("valuation_rate", 0)))

            if source_wh:
                # 자재 출고
                cur_qty, cur_value = self._get_current_balance(item_code, source_wh)
                if cur_qty < qty:
                    msg = f"재고 부족: {item_code} @ {source_wh} (잔고: {cur_qty}, 요청: {qty})"
                    raise_unprocessable("ERR-STK-001", msg)

                avg_rate = cur_value / cur_qty if cur_qty else Decimal(0)
                new_qty_src = cur_qty - qty
                new_value_src = new_qty_src * avg_rate

                sle_id = self._create_sle(
                    item_code=item_code,
                    warehouse=source_wh,
                    qty_change=-qty,
                    rate=avg_rate,
                    balance_qty=new_qty_src,
                    balance_value=new_value_src,
                    voucher_type="StockEntry",
                    voucher_no=voucher_no,
                )
                sle_ids.append(sle_id)
                self._update_stock_bin(item_code, source_wh, new_qty_src, new_value_src, avg_rate)

            if target_wh:
                # 완제품 입고
                amount = qty * rate
                tgt_qty, tgt_value = self._get_current_balance(item_code, target_wh)
                new_qty_tgt = tgt_qty + qty
                new_value_tgt = tgt_value + amount
                new_rate_tgt = new_value_tgt / new_qty_tgt if new_qty_tgt else Decimal(0)

                sle_id = self._create_sle(
                    item_code=item_code,
                    warehouse=target_wh,
                    qty_change=qty,
                    rate=new_rate_tgt,
                    balance_qty=new_qty_tgt,
                    balance_value=new_value_tgt,
                    voucher_type="StockEntry",
                    voucher_no=voucher_no,
                )
                sle_ids.append(sle_id)
                self._update_stock_bin(
                    item_code, target_wh, new_qty_tgt, new_value_tgt, new_rate_tgt
                )
        return sle_ids

    def _process_se_scrap(self, voucher_no: str, items: list[dict[str, Any]]) -> list[str]:
        """재고이동 폐기 처리 — 출고와 동일 로직."""
        return self._process_se_issue(voucher_no, items)

    def _get_current_balance(self, item_code: str, warehouse: str) -> tuple[Decimal, Decimal]:
        """stock_bins에서 현재 잔고(수량, 가치)를 조회한다."""
        bins = self._bin_repo.find_many(
            {"item_code": item_code, "warehouse": warehouse},
            limit=1,
        )
        if bins:
            return Decimal(str(bins[0].get("current_qty", 0))), Decimal(
                str(bins[0].get("current_value", 0))
            )
        return Decimal(0), Decimal(0)

    def _update_stock_bin(
        self,
        item_code: str,
        warehouse: str,
        new_qty: Decimal,
        new_value: Decimal,
        rate: Decimal,
    ) -> None:
        """stock_bins 컬렉션을 갱신하거나 신규 생성한다."""
        bins = self._bin_repo.find_many(
            {"item_code": item_code, "warehouse": warehouse},
            limit=1,
        )
        if bins:
            bin_id = bins[0]["_id"]
            self._bin_repo.update_by_id(
                bin_id,
                {
                    "current_qty": new_qty,
                    "current_value": new_value,
                    "valuation_rate": rate,
                },
            )
        else:
            bin_id = generate_name("SBIN", tenant_id=self._tenant_id)
            stock_bin = _StockBin(
                _id=bin_id,
                tenant_id=self._tenant_id,
                item_code=item_code,
                warehouse=warehouse,
                current_qty=new_qty,
                current_value=new_value,
                valuation_rate=rate,
            )
            self._bin_repo.insert(stock_bin)

    def _create_sle(
        self,
        *,
        item_code: str,
        warehouse: str,
        qty_change: Decimal,
        rate: Decimal,
        balance_qty: Decimal,
        balance_value: Decimal,
        voucher_type: str,
        voucher_no: str,
    ) -> str:
        """재고 원장 엔트리(SLE)를 생성한다."""
        from oneerp_stock_app.models.stock_ledger import StockLedgerEntry

        sle_id = generate_name("SLE", tenant_id=self._tenant_id)
        sle = StockLedgerEntry(
            _id=sle_id,
            tenant_id=self._tenant_id,
            item_code=item_code,
            warehouse=warehouse,
            posting_date=datetime.now(tz=UTC).date(),
            qty_change=qty_change,
            valuation_rate=rate,
            balance_qty=balance_qty,
            balance_value=balance_value,
            voucher_type=voucher_type,
            voucher_no=voucher_no,
        )
        self._sle_repo.insert(sle)
        return sle_id
