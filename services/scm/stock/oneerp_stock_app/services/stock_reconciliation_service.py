"""재고 실사 조정 서비스 — 실측 vs 장부 차이 SLE 보정 처리.

ERPNext Stock Reconciliation 베스트 프랙티스를 참고하여, 실사 결과를
재고 원장(SLE) 보정 항목으로 변환한다. 차이 수량과 가치 변동을
voucher_type="StockReconciliation"으로 SLE에 기록하고, stock_bins를
이동평균 단가로 갱신한다.

L2 비즈니스 룰 매핑:
- BR-STK-001/002: 이동평균법 입고/출고 (보정 시에도 동일 평가 적용)
- BR-STK-003: SLE 불변성 (보정도 새로운 SLE 행으로 추가)
- BR-STK-004: stock_bins 동기 갱신 (실사 후 잔고/가치 동기화)
- BR-STK-018: 순환재고조사 차이 처리 (다중 라인 일괄 처리)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class StockReconciliationService:
    """재고 실사(Stock Reconciliation) 차이 조정 비즈니스 로직.

    실사 결과(목표 수량/단가)와 장부(stock_bins) 차이를 계산하고,
    차이만큼 SLE 보정 행을 생성하여 재고 원장과 잔고를 정합화한다.

    워크플로우:
    1. 실사 문서 조회 (status=draft|in_progress)
    2. 라인별 차이 계산: variance_qty = target_qty - current_qty
    3. SLE 보정 행 생성 (qty_change=variance, voucher_type=StockReconciliation)
    4. stock_bins 갱신 (target_qty/target_value/target_rate)
    5. 실사 문서 status=submitted로 전환
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._sr_repo = Repository("stock_reconciliations", tenant_id=tenant_id)
        self._sle_repo = Repository("stock_ledger_entries", tenant_id=tenant_id)
        self._bin_repo = Repository("stock_bins", tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # 핵심 API
    # ------------------------------------------------------------------

    def submit_reconciliation(self, reconciliation_id: str) -> dict[str, Any]:
        """실사 문서를 제출하여 차이를 SLE 보정으로 반영한다.

        Args:
            reconciliation_id: 재고 실사 문서 ID (StockReconciliation _id)

        Returns:
            {
                reconciliation_id, items: [{item_code, warehouse, system_qty,
                target_qty, variance_qty, variance_value}],
                sle_ids, total_variance_qty, total_variance_value
            }

        Raises:
            OneERPError(404): 실사 문서 미존재
            OneERPError(422): 이미 제출된 실사 문서 (status=submitted)
            OneERPError(422): 라인이 1개도 없는 실사 문서
        """
        sr_doc = self._sr_repo.find_by_id(reconciliation_id)
        if not sr_doc:
            msg = f"재고 실사 문서를 찾을 수 없습니다: {reconciliation_id}"
            raise_not_found(msg)

        status = sr_doc.get("status", "draft")
        if status == "submitted":
            msg = f"이미 제출된 실사 문서입니다: {reconciliation_id}"
            raise_unprocessable("ERR-STK-RECON-001", msg)

        items = sr_doc.get("items", [])
        if not items:
            msg = "실사 문서에 라인이 1개 이상 필요합니다"
            raise_unprocessable("ERR-STK-RECON-002", msg)

        result_items: list[dict[str, Any]] = []
        sle_ids: list[str] = []
        total_var_qty = Decimal(0)
        total_var_value = Decimal(0)

        for line in items:
            item_code = str(line.get("item_code", ""))
            warehouse = str(line.get("warehouse", ""))
            target_qty = Decimal(str(line.get("qty", 0)))
            target_rate = Decimal(str(line.get("valuation_rate", 0)))

            if not item_code or not warehouse:
                msg = f"실사 라인에 item_code/warehouse가 누락되었습니다: {line}"
                raise_unprocessable("ERR-STK-RECON-003", msg)

            # 현재 잔고 조회
            cur_qty, cur_value = self._get_current_balance(item_code, warehouse)

            # 목표 단가가 0이면 현재 이동평균 단가를 유지
            effective_rate = (
                target_rate if target_rate > 0 else (cur_value / cur_qty if cur_qty else Decimal(0))
            )
            target_value = target_qty * effective_rate

            variance_qty = target_qty - cur_qty
            variance_value = target_value - cur_value

            # 차이 0이면 SLE 생성 생략 (성능 최적화)
            if variance_qty == 0 and variance_value == 0:
                result_items.append(
                    {
                        "item_code": item_code,
                        "warehouse": warehouse,
                        "system_qty": cur_qty,
                        "system_value": cur_value,
                        "target_qty": target_qty,
                        "target_value": target_value,
                        "variance_qty": variance_qty,
                        "variance_value": variance_value,
                        "sle_id": None,
                    }
                )
                continue

            sle_id = self._create_adjustment_sle(
                item_code=item_code,
                warehouse=warehouse,
                qty_change=variance_qty,
                rate=effective_rate,
                balance_qty=target_qty,
                balance_value=target_value,
                voucher_no=reconciliation_id,
            )
            sle_ids.append(sle_id)

            self._update_stock_bin(
                item_code=item_code,
                warehouse=warehouse,
                new_qty=target_qty,
                new_value=target_value,
                rate=effective_rate,
            )

            total_var_qty += variance_qty
            total_var_value += variance_value

            result_items.append(
                {
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "system_qty": cur_qty,
                    "system_value": cur_value,
                    "target_qty": target_qty,
                    "target_value": target_value,
                    "variance_qty": variance_qty,
                    "variance_value": variance_value,
                    "sle_id": sle_id,
                }
            )

        # 실사 문서 상태 업데이트
        self._sr_repo.update_by_id(
            reconciliation_id,
            {
                "status": "submitted",
                "submitted_at": datetime.now(tz=UTC).isoformat(),
                "total_variance_qty": total_var_qty,
                "total_variance_value": total_var_value,
            },
        )

        logger.info(
            "재고 실사 제출 완료: %s (라인 %d건, 차이 수량: %s, 차이 가치: %s)",
            reconciliation_id,
            len(items),
            total_var_qty,
            total_var_value,
        )

        return {
            "reconciliation_id": reconciliation_id,
            "items": result_items,
            "sle_ids": sle_ids,
            "line_count": len(items),
            "total_variance_qty": total_var_qty,
            "total_variance_value": total_var_value,
        }

    def calculate_variance_summary(self, reconciliation_id: str) -> dict[str, Any]:
        """실사 문서의 차이 요약을 계산한다 (커밋 없이 미리보기).

        제출 전 사용자가 차이를 검토할 수 있도록 조회 전용으로 동작한다.

        Args:
            reconciliation_id: 실사 문서 ID

        Returns:
            {reconciliation_id, items: [...], net_variance_qty, net_variance_value,
             positive_count, negative_count, zero_count}

        Raises:
            OneERPError(404): 실사 문서 미존재
        """
        sr_doc = self._sr_repo.find_by_id(reconciliation_id)
        if not sr_doc:
            msg = f"재고 실사 문서를 찾을 수 없습니다: {reconciliation_id}"
            raise_not_found(msg)

        items = sr_doc.get("items", [])
        preview_items: list[dict[str, Any]] = []
        net_qty = Decimal(0)
        net_value = Decimal(0)
        positive = 0
        negative = 0
        zero = 0

        for line in items:
            item_code = str(line.get("item_code", ""))
            warehouse = str(line.get("warehouse", ""))
            target_qty = Decimal(str(line.get("qty", 0)))
            target_rate = Decimal(str(line.get("valuation_rate", 0)))

            cur_qty, cur_value = self._get_current_balance(item_code, warehouse)
            effective_rate = (
                target_rate if target_rate > 0 else (cur_value / cur_qty if cur_qty else Decimal(0))
            )
            target_value = target_qty * effective_rate

            variance_qty = target_qty - cur_qty
            variance_value = target_value - cur_value

            if variance_qty > 0:
                positive += 1
            elif variance_qty < 0:
                negative += 1
            else:
                zero += 1

            net_qty += variance_qty
            net_value += variance_value

            preview_items.append(
                {
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "system_qty": cur_qty,
                    "target_qty": target_qty,
                    "variance_qty": variance_qty,
                    "variance_value": variance_value,
                }
            )

        return {
            "reconciliation_id": reconciliation_id,
            "items": preview_items,
            "net_variance_qty": net_qty,
            "net_variance_value": net_value,
            "positive_count": positive,
            "negative_count": negative,
            "zero_count": zero,
        }

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _get_current_balance(self, item_code: str, warehouse: str) -> tuple[Decimal, Decimal]:
        """stock_bins에서 현재 잔고(수량, 가치)를 조회한다."""
        bins = self._bin_repo.find_many(
            {"item_code": item_code, "warehouse": warehouse},
            limit=1,
        )
        if bins:
            return (
                Decimal(str(bins[0].get("current_qty", 0))),
                Decimal(str(bins[0].get("current_value", 0))),
            )
        return Decimal(0), Decimal(0)

    def _create_adjustment_sle(
        self,
        *,
        item_code: str,
        warehouse: str,
        qty_change: Decimal,
        rate: Decimal,
        balance_qty: Decimal,
        balance_value: Decimal,
        voucher_no: str,
    ) -> str:
        """재고 실사 보정 SLE를 생성한다.

        voucher_type="StockReconciliation"으로 일반 입출고와 구분한다.
        """
        sle_id = generate_name("SLE", tenant_id=self._tenant_id)
        sle_doc = {
            "_id": sle_id,
            "tenant_id": self._tenant_id,
            "item_code": item_code,
            "warehouse": warehouse,
            "posting_date": datetime.now(tz=UTC).date().isoformat(),
            "qty_change": qty_change,
            "valuation_rate": rate,
            "balance_qty": balance_qty,
            "balance_value": balance_value,
            "voucher_type": "StockReconciliation",
            "voucher_no": voucher_no,
        }
        self._sle_repo.insert(sle_doc)
        return sle_id

    def _update_stock_bin(
        self,
        *,
        item_code: str,
        warehouse: str,
        new_qty: Decimal,
        new_value: Decimal,
        rate: Decimal,
    ) -> None:
        """stock_bins 캐시를 갱신하거나 신규 생성한다."""
        bins = self._bin_repo.find_many(
            {"item_code": item_code, "warehouse": warehouse},
            limit=1,
        )
        if bins:
            self._bin_repo.update_by_id(
                bins[0]["_id"],
                {
                    "current_qty": new_qty,
                    "current_value": new_value,
                    "valuation_rate": rate,
                },
            )
        else:
            bin_id = generate_name("SBIN", tenant_id=self._tenant_id)
            self._bin_repo.insert(
                {
                    "_id": bin_id,
                    "tenant_id": self._tenant_id,
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "current_qty": new_qty,
                    "current_value": new_value,
                    "valuation_rate": rate,
                }
            )
