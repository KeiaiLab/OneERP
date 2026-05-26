"""MRP 서비스 — 자재소요계획(MRP) 실행 및 자동 발주/작업지시 생성.

L2 비즈니스 룰 매핑:
- BR-MFG-011: MRP 수요 기반 (forecast_id 필수)
- BR-MFG-012: 제조/구매 자동 분류 (BOM 존재=제조, 없음=구매)
- BR-MFG-013: 부족분만 산출 (required - current > 0)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class MRPService:
    """MRP(Material Requirements Planning) 비즈니스 로직.

    수요예측 → 재고확인 → 부족분 자동 발주/작업지시 생성.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._forecast_repo = Repository("demand_forecasts", tenant_id=tenant_id)
        self._mrp_repo = Repository("mrp_runs", tenant_id=tenant_id)
        self._bom_repo = Repository("boms", tenant_id=tenant_id)
        self._stock_repo = Repository("stock_balances", tenant_id=tenant_id)

    def run_mrp(
        self,
        forecast_id: str,
    ) -> dict[str, Any]:
        """MRP를 실행한다.

        수요예측을 기반으로 BOM 전개 → 재고 확인 → 부족분 산출.

        Args:
            forecast_id: 수요예측 ID

        Returns:
            MRP 실행 결과 (purchase_requests, work_orders)
        """
        forecast = self._forecast_repo.find_by_id(forecast_id)
        if not forecast:
            raise OneERPError(
                status_code=404,
                error="ERR-MFG-002",
                detail=f"수요예측 '{forecast_id}'을 찾을 수 없습니다",
            )

        demand_items = forecast.get("items", [])

        purchase_requests: list[dict[str, Any]] = []
        work_orders: list[dict[str, Any]] = []

        for demand in demand_items:
            item_code = demand.get("item_code", "")
            required_qty = float(demand.get("qty", 0))

            # 현재 재고 확인
            stock = self._stock_repo.find_many({"item_code": item_code}, limit=1)
            current_qty = float(stock[0].get("qty", 0)) if stock else 0

            shortage = required_qty - current_qty
            if shortage <= 0:
                continue

            # BOM 존재 여부로 제조/구매 결정
            bom = self._bom_repo.find_many({"item_code": item_code}, limit=1)

            if bom:
                # BOM 있음 → 작업지시 생성
                work_orders.append(
                    {
                        "item_code": item_code,
                        "qty": shortage,
                        "bom_id": bom[0].get("_id", ""),
                        "type": "manufacture",
                    }
                )
            else:
                # BOM 없음 → 구매요청 생성
                purchase_requests.append(
                    {
                        "item_code": item_code,
                        "qty": shortage,
                        "type": "purchase",
                    }
                )

        # MRP 실행 결과 저장
        mrp_id = generate_name("MRP", tenant_id=self._tenant_id)
        self._mrp_repo.insert(
            {
                "_id": mrp_id,
                "forecast_id": forecast_id,
                "purchase_requests": purchase_requests,
                "work_orders": work_orders,
                "tenant_id": self._tenant_id,
            }
        )

        logger.info(
            "MRP 실행: %s (구매: %d건, 제조: %d건)",
            mrp_id,
            len(purchase_requests),
            len(work_orders),
        )

        return {
            "mrp_id": mrp_id,
            "forecast_id": forecast_id,
            "purchase_request_count": len(purchase_requests),
            "work_order_count": len(work_orders),
            "purchase_requests": purchase_requests,
            "work_orders": work_orders,
        }
