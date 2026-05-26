"""공급업체 견적 종합 비교 서비스.

BR-BUY-NEW-021: 최저가뿐 아니라 납기/결제조건을 종합한 공급사 추천.

기존 PurchaseProcessService.compare_quotations는 품목별 최저가만 추천한다.
이 서비스는 ERPNext/Odoo의 공급사 비교 모범 사례에 따라
"가격(price) / 납기(delivery) / 결제조건(payment)"을
가중치 기반으로 점수화(0~100)하고 종합 1위를 추천한다.

참조:
- ERPNext Supplier Quotation Comparison Report (docs.frappe.io)
- Odoo Purchase: supplier evaluation, qualification score
- P2P best practice: 3-way matching before recommendation

점수 공식:
- price_score: 100 x (min_rate / self_rate) — 낮을수록 높은 점수
- delivery_score: 100 x (min_days / self_days) — 짧을수록 높은 점수
- payment_score: 100 x (self_days / max_days) — 길수록 높은 점수
- total_score: price*w1 + delivery*w2 + payment*w3
  (기본 가중치: price 0.5, delivery 0.3, payment 0.2)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 기본 가중치 (합계 1.0)
_DEFAULT_WEIGHTS: dict[str, float] = {
    "price": 0.5,
    "delivery": 0.3,
    "payment": 0.2,
}

_WEIGHT_SUM_TOLERANCE = 0.001


class SupplierQuotationComparisonService:
    """공급업체 견적 종합 비교 비즈니스 로직.

    RFQ에 대한 공급사 견적을 가격/납기/결제조건으로 점수화하여
    종합 1위 공급사를 추천한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._sq_repo = Repository("supplier_quotations", tenant_id=tenant_id)
        self._rfq_repo = Repository("request_for_quotations", tenant_id=tenant_id)

    def compare_comprehensive(
        self,
        *,
        rfq_id: str,
        item_code: str,
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """특정 품목에 대한 공급사 견적을 종합 비교한다.

        Args:
            rfq_id: 견적 요청 ID
            item_code: 비교할 품목 코드 (단일 품목 기준 점수화)
            weights: 가중치 dict (기본값: price 0.5 / delivery 0.3 / payment 0.2)

        Returns:
            {rfq_id, item_code, weights, quotation_count, scores, recommended}

        Raises:
            OneERPError: 가중치 합이 1.0 아닐 때(400),
                         지정 품목이 모든 견적에 없을 때(422)
        """
        effective_weights = self._validate_weights(weights)

        quotations = self._sq_repo.find_many(
            {"rfq_reference": rfq_id},
            limit=100,
        )

        if not quotations:
            return {
                "rfq_id": rfq_id,
                "item_code": item_code,
                "weights": effective_weights,
                "quotation_count": 0,
                "scores": [],
                "recommended": None,
            }

        # 품목 정보 추출 + 공급사별 기본 지표 수집
        candidates: list[dict[str, Any]] = []
        for sq in quotations:
            items = sq.get("items", [])
            matched = next(
                (i for i in items if i.get("item_code") == item_code),
                None,
            )
            if matched is None:
                continue
            candidates.append(
                {
                    "quotation_id": sq.get("_id", ""),
                    "supplier": sq.get("supplier", ""),
                    "rate": float(matched.get("rate", 0)),
                    "qty": float(matched.get("qty", 0)),
                    "delivery_days": float(sq.get("delivery_days", 0)) or 1.0,
                    "payment_terms_days": float(sq.get("payment_terms_days", 0)),
                    "min_order_qty": float(sq.get("min_order_qty", 0)),
                }
            )

        if not candidates:
            raise_unprocessable(
                "ERR-BUY-034",
                f"품목 '{item_code}'이 RFQ '{rfq_id}'의 견적에 포함되어 있지 않습니다",
            )

        # 기준값 산출 (0 방어)
        min_rate = min(c["rate"] for c in candidates) or 1.0
        min_delivery = min(c["delivery_days"] for c in candidates) or 1.0
        max_payment = max(c["payment_terms_days"] for c in candidates)

        # 점수 산정
        scores: list[dict[str, Any]] = []
        for c in candidates:
            price_score = round(100.0 * (min_rate / c["rate"]), 2) if c["rate"] > 0 else 0.0
            delivery_score = (
                round(100.0 * (min_delivery / c["delivery_days"]), 2)
                if c["delivery_days"] > 0
                else 0.0
            )
            payment_score = (
                round(100.0 * (c["payment_terms_days"] / max_payment), 2)
                if max_payment > 0
                else 100.0
            )
            total = round(
                price_score * effective_weights["price"]
                + delivery_score * effective_weights["delivery"]
                + payment_score * effective_weights["payment"],
                2,
            )
            scores.append(
                {
                    "supplier": c["supplier"],
                    "quotation_id": c["quotation_id"],
                    "rate": c["rate"],
                    "delivery_days": c["delivery_days"],
                    "payment_terms_days": c["payment_terms_days"],
                    "price_score": price_score,
                    "delivery_score": delivery_score,
                    "payment_score": payment_score,
                    "total_score": total,
                }
            )

        # 총점 내림차순 정렬
        scores.sort(key=lambda s: s["total_score"], reverse=True)
        recommended = scores[0] if scores else None

        logger.info(
            "공급사 종합 비교: RFQ=%s, 품목=%s, 후보=%d개, 추천=%s (%.2f점)",
            rfq_id,
            item_code,
            len(scores),
            recommended["supplier"] if recommended else "-",
            recommended["total_score"] if recommended else 0,
        )

        return {
            "rfq_id": rfq_id,
            "item_code": item_code,
            "weights": effective_weights,
            "quotation_count": len(candidates),
            "scores": scores,
            "recommended": recommended,
        }

    @staticmethod
    def _validate_weights(weights: dict[str, float] | None) -> dict[str, float]:
        """가중치 유효성 검증 + 정규화.

        가중치 dict이 None이면 기본값 사용.
        합계가 1.0과 다르면(오차 허용) 400 에러.
        """
        if weights is None:
            return dict(_DEFAULT_WEIGHTS)

        required_keys = {"price", "delivery", "payment"}
        missing = required_keys - set(weights.keys())
        if missing:
            raise_bad_request(f"가중치에 필수 키가 누락되었습니다: {sorted(missing)}")

        total = sum(float(weights[k]) for k in required_keys)
        if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
            raise_bad_request(f"가중치 합계는 1.0이어야 합니다 (현재: {total:.4f})")

        return {
            "price": float(weights["price"]),
            "delivery": float(weights["delivery"]),
            "payment": float(weights["payment"]),
        }
