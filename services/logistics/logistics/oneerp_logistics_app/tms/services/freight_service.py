"""운임 계산 서비스 — 운임 자동 계산 및 정산 금액 산출."""

from __future__ import annotations

import logging
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class FreightService:
    """운임 계산 비즈니스 로직.

    BR-TMS-005: 운임 자동 계산
    BR-TMS-006: 유류할증료 계산
    BR-TMS-010: 정산 금액 자동 계산
    BR-TMS-011: 정산 세금 계산 (KRW 원 단위 절사)
    BR-TMS-019: 운임 단가 유효기간 검증
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._rate_repo = Repository("freight_rates", tenant_id=tenant_id)
        self._route_repo = Repository("routes", tenant_id=tenant_id)

    def calculate_freight(
        self,
        carrier_id: str,
        route_id: str | None,
        vehicle_type: str | None,
        total_weight_kg: float,
        dispatch_date: date,
    ) -> dict[str, Any]:
        """배송 건의 운임을 계산한다.

        Args:
            carrier_id: 운송사 ID
            route_id: 경로 ID (없으면 전체 경로 매칭)
            vehicle_type: 차량 유형
            total_weight_kg: 총 중량 (kg)
            dispatch_date: 배차일

        Returns:
            운임 계산 결과 (freight_amount, fuel_surcharge, 상세 내역)
        """
        rate = self._find_matching_rate(
            carrier_id, route_id, vehicle_type, total_weight_kg, dispatch_date
        )

        if not rate:
            logger.warning(
                "운임 단가 미등록 (carrier: %s, route: %s, date: %s)",
                carrier_id,
                route_id,
                dispatch_date,
            )
            return {
                "freight_amount": 0,
                "fuel_surcharge": 0,
                "base_amount": 0,
                "weight_charge": 0,
                "distance_charge": 0,
                "warning": "운임 단가 미등록",
            }

        base = Decimal(str(rate.get("base_amount", 0)))
        per_kg = Decimal(str(rate.get("per_kg_amount", 0)))
        per_km = Decimal(str(rate.get("per_km_amount", 0)))
        fuel_rate = Decimal(str(rate.get("fuel_surcharge_rate", 0)))
        weight_min = Decimal(str(rate.get("weight_min_kg", 0)))

        # 중량 추가 금액
        weight_diff = max(Decimal(0), Decimal(str(total_weight_kg)) - weight_min)
        weight_charge = weight_diff * per_kg

        # 거리 추가 금액
        distance_km = Decimal(0)
        if route_id:
            route = self._route_repo.find_by_id(route_id)
            if route and route.get("distance_km"):
                distance_km = Decimal(str(route["distance_km"]))
        distance_charge = distance_km * per_km

        # 유류할증료 (기본 금액 기준)
        fuel_surcharge = base * fuel_rate

        # 합산 (KRW 원 단위 절사)
        freight_amount = base + weight_charge + distance_charge + fuel_surcharge
        freight_amount = freight_amount.quantize(Decimal(1), rounding=ROUND_DOWN)

        return {
            "freight_amount": int(freight_amount),
            "fuel_surcharge": int(fuel_surcharge.quantize(Decimal(1), rounding=ROUND_DOWN)),
            "base_amount": int(base),
            "weight_charge": int(weight_charge.quantize(Decimal(1), rounding=ROUND_DOWN)),
            "distance_charge": int(distance_charge.quantize(Decimal(1), rounding=ROUND_DOWN)),
        }

    def calculate_settlement(
        self,
        subtotal: float,
        fuel_surcharge: float,
        additional_charges: list[dict[str, Any]] | None = None,
        deductions: list[dict[str, Any]] | None = None,
        currency: str = "KRW",
    ) -> dict[str, Any]:
        """정산 금액을 계산한다.

        BR-TMS-010: total = subtotal + fuel + additional - deductions + tax
        BR-TMS-011: KRW 원 단위 절사

        Args:
            subtotal: 운임 소계
            fuel_surcharge: 유류할증료 합계
            additional_charges: 추가 비용 항목
            deductions: 차감 항목
            currency: 통화 코드

        Returns:
            정산 금액 상세 (taxable, tax_amount, total_amount)
        """
        additional_total = Decimal(0)
        if additional_charges:
            for charge in additional_charges:
                additional_total += Decimal(str(charge.get("amount", 0)))

        deduction_total = Decimal(0)
        if deductions:
            for ded in deductions:
                deduction_total += Decimal(str(ded.get("amount", 0)))

        sub = Decimal(str(subtotal))
        fuel = Decimal(str(fuel_surcharge))

        taxable = sub + fuel + additional_total - deduction_total

        # KRW: 원 미만 절사
        if currency == "KRW":
            tax_amount = (taxable * Decimal("0.1")).quantize(Decimal(1), rounding=ROUND_DOWN)
        else:
            tax_amount = taxable * Decimal("0.1")

        total_amount = taxable + tax_amount

        return {
            "taxable": int(taxable),
            "tax_amount": int(tax_amount),
            "total_amount": int(total_amount),
            "additional_total": int(additional_total),
            "deduction_total": int(deduction_total),
        }

    def calculate_otd_rate(
        self,
        delivered_shipments: list[dict[str, Any]],
    ) -> float:
        """정시 배송률(OTD)을 계산한다.

        expected_delivery가 null인 건은 제외한다.

        Args:
            delivered_shipments: 배송 완료 건 목록

        Returns:
            OTD 비율 (0.0 ~ 100.0)
        """
        eligible = [
            s
            for s in delivered_shipments
            if s.get("expected_delivery") is not None and s.get("actual_delivery") is not None
        ]
        if not eligible:
            return 0.0

        on_time = sum(1 for s in eligible if s["actual_delivery"] <= s["expected_delivery"])
        return round((on_time / len(eligible)) * 100, 2)

    def calculate_carrier_performance(
        self,
        total_delivered: int,
        on_time_count: int,
        accident_count: int,
        pod_required_count: int,
        pod_submitted_count: int,
        min_shipments: int = 10,
    ) -> float | None:
        """운송사 성과 점수를 계산한다 (BR-TMS-020).

        Args:
            total_delivered: 총 배송 완료 건수
            on_time_count: 정시 배송 건수
            accident_count: 사고 건수
            pod_required_count: POD 필수 건수
            pod_submitted_count: POD 제출 건수
            min_shipments: 최소 건수

        Returns:
            성과 점수 (0.0~5.0) 또는 None (최소 건수 미달)
        """
        if total_delivered < min_shipments:
            return None

        otd_score = (on_time_count / total_delivered) * 5.0
        no_accident_score = (1 - (accident_count / total_delivered)) * 5.0
        no_accident_score = max(0.0, no_accident_score)

        pod_score = 5.0
        if pod_required_count > 0:
            pod_score = (pod_submitted_count / pod_required_count) * 5.0

        performance = (otd_score * 0.4) + (no_accident_score * 0.3) + (pod_score * 0.3)
        return round(min(5.0, max(0.0, performance)), 2)

    def _find_matching_rate(
        self,
        carrier_id: str,
        route_id: str | None,
        vehicle_type: str | None,
        weight_kg: float,
        target_date: date,
    ) -> dict[str, Any] | None:
        """매칭되는 운임 단가를 조회한다.

        운송사 + 경로 + 차량유형 + 중량범위 + 유효기간으로 매칭.
        """
        query: dict[str, Any] = {
            "carrier_id": carrier_id,
            "is_active": True,
        }

        # 경로 매칭 (route_id가 있으면 해당 경로, 없으면 null도 포함)
        if route_id:
            query["$or"] = [{"route_id": route_id}, {"route_id": None}]

        if vehicle_type:
            query["$or"] = [{"vehicle_type": vehicle_type}, {"vehicle_type": None}]

        rates = self._rate_repo.find_many(query=query, limit=100)

        # 유효기간 + 중량범위 필터링
        matched = []
        iso_date = target_date.isoformat()
        for rate in rates:
            eff_from = rate.get("effective_from", "")
            eff_to = rate.get("effective_to")

            if eff_from and str(eff_from) > iso_date:
                continue
            if eff_to and str(eff_to) < iso_date:
                continue

            w_min = float(rate.get("weight_min_kg", 0))
            w_max = float(rate.get("weight_max_kg", 999999))
            if w_min <= weight_kg <= w_max:
                matched.append(rate)

        if not matched:
            return None

        # 가장 구체적인 매칭 우선 (route_id가 있는 것 > 없는 것)
        matched.sort(
            key=lambda r: (r.get("route_id") is not None, r.get("vehicle_type") is not None),
            reverse=True,
        )
        return matched[0]
