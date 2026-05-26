"""MRP 순소요량(Net Requirement) 계산 서비스 — Gross-to-Net 폭발 엔진.

표준 MRP 공식 (Oracle/SAP/Wikiversity 표준):
    Net Requirement = (Gross Requirement + Allocations) - (On Hand + Scheduled Receipts)

용어 정의:
- Gross Requirement: BOM 폭발로 산출된 총소요량
- Allocations: 이미 다른 작업지시에 할당된 수량
- On Hand: stock_bins.current_qty (현재 가용 재고)
- Scheduled Receipts: 미래 입고 예정 (구매발주 + 작업지시 미완료분)
- Net Requirement: 실제로 추가 발주/생산이 필요한 수량

처리 흐름:
1. 수요 예측에서 최상위 품목 수량 추출
2. BOM 트리 재귀 폭발 → 각 자재의 Gross Requirement 산출
3. stock_bins/purchase_orders/work_orders에서 가용 정보 수집
4. 자재별 Net Requirement = Gross + Alloc - OnHand - Scheduled
5. BOM 존재 여부로 제조/구매 분기 (BR-MFG-012)

L2 비즈니스 룰 매핑:
- BR-MFG-004: BOM 전개 깊이 제한 (max_depth=10)
- BR-MFG-011: MRP 수요 기반 (forecast_id 필수)
- BR-MFG-012: 제조/구매 자동 분류 (BOM 존재=제조, 없음=구매)
- BR-MFG-013: 부족분만 산출 (net > 0인 경우만)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

MAX_DEPTH = 10


class MRPNetRequirementService:
    """MRP 순소요량(Net Requirement) 계산 비즈니스 로직.

    Gross-to-Net 폭발 알고리즘으로 다단계 BOM의 순소요량을 계산하여
    제조/구매 권고 목록을 생성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._forecast_repo = Repository("demand_forecasts", tenant_id=tenant_id)
        self._bom_repo = Repository("boms", tenant_id=tenant_id)
        self._stock_repo = Repository("stock_bins", tenant_id=tenant_id)
        self._po_repo = Repository("purchase_orders", tenant_id=tenant_id)
        self._wo_repo = Repository("work_orders", tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # 핵심 API
    # ------------------------------------------------------------------

    def calculate_net_requirements(
        self,
        forecast_id: str,
        *,
        consider_scheduled_receipts: bool = True,
        consider_allocations: bool = True,
    ) -> dict[str, Any]:
        """수요예측 기반 순소요량을 계산한다.

        Args:
            forecast_id: 수요예측 문서 ID
            consider_scheduled_receipts: True면 PO/WO 미입고분을 가용으로 가산
            consider_allocations: True면 기존 WO 할당 수량을 소요로 가산

        Returns:
            {
                forecast_id, gross_requirements: {item_code: qty},
                net_requirements: [{item_code, gross, on_hand, scheduled,
                                    allocated, net, action: manufacture|purchase}],
                manufacture_count, purchase_count
            }

        Raises:
            OneERPError(404): 수요예측 문서 미존재
            OneERPError(422): 수요예측 라인이 없음
        """
        forecast = self._forecast_repo.find_by_id(forecast_id)
        if not forecast:
            msg = f"수요예측을 찾을 수 없습니다: {forecast_id}"
            raise_not_found(msg)

        demand_items = forecast.get("items", [])
        if not demand_items:
            msg = "수요예측에 라인이 1개 이상 필요합니다"
            raise_unprocessable("ERR-MFG-NET-001", msg)

        # 1. Gross Requirement 누적 (BOM 폭발)
        gross: dict[str, Decimal] = {}
        for demand in demand_items:
            item_code = str(demand.get("item_code", ""))
            qty = Decimal(str(demand.get("qty", 0)))
            if not item_code or qty <= 0:
                continue
            self._explode_demand(item_code, qty, gross, depth=0)

        # 2. 각 자재의 Net 계산
        net_requirements: list[dict[str, Any]] = []
        manufacture_count = 0
        purchase_count = 0

        for item_code, gross_qty in sorted(gross.items()):
            on_hand = self._get_on_hand(item_code)
            scheduled = (
                self._get_scheduled_receipts(item_code)
                if consider_scheduled_receipts
                else Decimal(0)
            )
            allocated = self._get_allocations(item_code) if consider_allocations else Decimal(0)

            # 표준 MRP 공식: Net=(gross+alloc)-(onHand+scheduled)
            net = (gross_qty + allocated) - (on_hand + scheduled)

            # BR-MFG-013: 부족분만 산출
            if net <= 0:
                continue

            # BR-MFG-012: BOM 존재 → 제조, 없음 → 구매
            has_bom = self._has_bom(item_code)
            action = "manufacture" if has_bom else "purchase"
            if action == "manufacture":
                manufacture_count += 1
            else:
                purchase_count += 1

            net_requirements.append(
                {
                    "item_code": item_code,
                    "gross": gross_qty,
                    "on_hand": on_hand,
                    "scheduled": scheduled,
                    "allocated": allocated,
                    "net": net,
                    "action": action,
                }
            )

        logger.info(
            "MRP 순소요량 계산 완료: %s (총 %d 자재, 제조: %d, 구매: %d)",
            forecast_id,
            len(net_requirements),
            manufacture_count,
            purchase_count,
        )

        return {
            "forecast_id": forecast_id,
            "gross_requirements": gross,
            "net_requirements": net_requirements,
            "manufacture_count": manufacture_count,
            "purchase_count": purchase_count,
            "total_count": len(net_requirements),
        }

    def explode_single_item(
        self,
        item_code: str,
        qty: Decimal,
    ) -> dict[str, Decimal]:
        """단일 품목의 수요를 BOM 폭발하여 Gross Requirement 산출.

        Args:
            item_code: 최상위 품목 코드
            qty: 생산 수량

        Returns:
            {item_code: gross_qty} 자재별 총소요량 dict

        Raises:
            OneERPError(422): qty <= 0
        """
        if qty <= 0:
            msg = f"수량은 0보다 커야 합니다: {qty}"
            raise_unprocessable("ERR-MFG-NET-002", msg)

        gross: dict[str, Decimal] = {}
        self._explode_demand(item_code, qty, gross, depth=0)
        return gross

    # ------------------------------------------------------------------
    # BOM 폭발
    # ------------------------------------------------------------------

    def _explode_demand(
        self,
        item_code: str,
        qty: Decimal,
        accumulator: dict[str, Decimal],
        *,
        depth: int,
    ) -> None:
        """재귀적으로 BOM을 폭발하여 자재별 소요량 누적.

        - BOM이 있으면 라인 자재를 재귀 폭발
        - BOM이 없으면 말단 자재로 누적
        - 최상위 품목 자체도 누적 (제조 vs 구매 결정의 기초)
        """
        if depth >= MAX_DEPTH:
            logger.warning("BOM 폭발 최대 깊이 %d 도달: %s", MAX_DEPTH, item_code)
            accumulator[item_code] = accumulator.get(item_code, Decimal(0)) + qty
            return

        # 현재 품목 누적
        accumulator[item_code] = accumulator.get(item_code, Decimal(0)) + qty

        boms = self._bom_repo.find_many(
            {"item_code": item_code, "is_default": True},
            limit=1,
        )
        if not boms:
            # 기본 BOM이 없으면 일반 BOM 시도
            boms = self._bom_repo.find_many(
                {"item_code": item_code},
                limit=1,
            )

        if not boms:
            return  # 말단 자재

        bom = boms[0]
        bom_qty = Decimal(str(bom.get("quantity", 1)))
        if bom_qty <= 0:
            bom_qty = Decimal(1)

        scale = qty / bom_qty
        for line in bom.get("items", []):
            line_item = str(line.get("item_code", ""))
            line_qty = Decimal(str(line.get("qty", 0))) * scale
            if not line_item or line_qty <= 0:
                continue
            self._explode_demand(line_item, line_qty, accumulator, depth=depth + 1)

    # ------------------------------------------------------------------
    # 가용/할당/예정 수량 조회
    # ------------------------------------------------------------------

    def _get_on_hand(self, item_code: str) -> Decimal:
        """stock_bins에서 현재 가용 수량 합계."""
        bins = self._stock_repo.find_many({"item_code": item_code}, limit=100)
        total = Decimal(0)
        for b in bins:
            total += Decimal(str(b.get("current_qty", 0)))
        return total

    def _get_scheduled_receipts(self, item_code: str) -> Decimal:
        """미래 입고 예정 = 미입고 PO 라인 + 미완료 WO produced_qty.

        - PurchaseOrder의 items 중 status가 draft/submitted인 것
        - WorkOrder의 production_item이 일치하고 status != completed인 것
        """
        scheduled = Decimal(0)

        # 미입고 PO 합산
        pos = self._po_repo.find_many(
            {"status": {"$in": ["draft", "submitted"]}},
            limit=200,
        )
        for po in pos:
            for line in po.get("items", []):
                if str(line.get("item_code", "")) == item_code:
                    scheduled += Decimal(str(line.get("qty", 0)))

        # 미완료 WO 합산
        wos = self._wo_repo.find_many(
            {
                "item_code": item_code,
                "status": {"$in": ["draft", "not_started", "in_progress"]},
            },
            limit=200,
        )
        for wo in wos:
            planned = Decimal(str(wo.get("planned_qty", 0)))
            produced = Decimal(str(wo.get("produced_qty", 0)))
            remaining = planned - produced
            if remaining > 0:
                scheduled += remaining

        return scheduled

    def _get_allocations(self, item_code: str) -> Decimal:
        """이미 할당된 수량 = 진행 중 WO의 required_materials 합계.

        in_progress 상태의 작업지시가 출고 예약한 자재 수량.
        """
        wos = self._wo_repo.find_many(
            {"status": "in_progress"},
            limit=200,
        )
        total = Decimal(0)
        for wo in wos:
            for material in wo.get("required_materials", []):
                if str(material.get("item_code", "")) == item_code:
                    total += Decimal(str(material.get("required_qty", 0)))
        return total

    def _has_bom(self, item_code: str) -> bool:
        """해당 품목에 활성 BOM이 존재하는지 확인."""
        boms = self._bom_repo.find_many(
            {"item_code": item_code},
            limit=1,
        )
        return bool(boms)
