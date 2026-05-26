"""수출통제 준수점검 서비스 — 거부당사자·제재·이중용도 품목 스크리닝."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 점검 유형별 가중치
_RISK_WEIGHTS: dict[str, int] = {
    "denied_party": 10,
    "embargo": 8,
    "sanction": 9,
    "dual_use": 7,
}


class ComplianceService:
    """수출통제 준수점검 비즈니스 로직.

    거부당사자 목록(DPL), 제재 목록, 이중용도 품목 등을
    스크리닝하고 위험 수준을 판정한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._check_repo = Repository("compliance_checks", tenant_id=tenant_id)
        self._agreement_repo = Repository("trade_agreements", tenant_id=tenant_id)
        self._hs_repo = Repository("hs_classifications", tenant_id=tenant_id)

    def screen_entity(
        self,
        entity_name: str,
        entity_country: str,
        check_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """거래 상대방을 스크리닝한다.

        Args:
            entity_name: 검사 대상 엔티티명 (기업/개인)
            entity_country: 대상 국가 코드
            check_types: 점검 유형 목록 (미지정 시 전체)

        Returns:
            스크리닝 결과 (result, risk_level, details)
        """
        types_to_check = check_types or list(_RISK_WEIGHTS.keys())
        total_score = 0
        details: list[dict[str, Any]] = []

        for check_type in types_to_check:
            matched = self._run_check(check_type, entity_name, entity_country)
            weight = _RISK_WEIGHTS.get(check_type, 5)
            score = weight if matched else 0
            total_score += score
            details.append(
                {
                    "check_type": check_type,
                    "matched": matched,
                    "score": score,
                }
            )

        risk_level = self._calculate_risk_level(total_score)
        result = "fail" if risk_level in ("high", "critical") else "pass"

        logger.info(
            "엔티티 스크리닝 완료: %s (%s) — 결과: %s, 위험: %s",
            entity_name,
            entity_country,
            result,
            risk_level,
        )

        return {
            "entity_name": entity_name,
            "entity_country": entity_country,
            "result": result,
            "risk_level": risk_level,
            "total_score": total_score,
            "details": details,
            "checked_at": datetime.now(tz=UTC),
        }

    def check_export_eligibility(
        self,
        item_code: str,
        destination_country: str,
    ) -> dict[str, Any]:
        """수출 적격성을 확인한다.

        HS 분류 정보와 무역협정을 기반으로 수출 가능 여부와
        적용 가능한 특혜 관세를 판단한다.

        Args:
            item_code: 품목 코드
            destination_country: 수출 대상 국가 코드

        Returns:
            수출 적격성 결과 (eligible, agreements, duty_info)
        """
        # HS 분류 조회
        hs_records = self._hs_repo.find_many(
            {"item_code": item_code, "is_active": True},
            limit=10,
        )

        if not hs_records:
            return {
                "item_code": item_code,
                "destination_country": destination_country,
                "eligible": False,
                "reason": "HS 분류 정보가 없습니다",
                "agreements": [],
            }

        # 적용 가능한 무역협정 조회
        applicable_agreements = self._agreement_repo.find_many(
            {"is_active": True},
            limit=50,
        )

        matched_agreements: list[dict[str, Any]] = []
        for agreement in applicable_agreements:
            country_codes = agreement.get("country_codes", [])
            if destination_country in country_codes:
                matched_agreements.append(
                    {
                        "agreement_code": agreement.get("agreement_code", ""),
                        "agreement_name": agreement.get("agreement_name", ""),
                        "agreement_type": agreement.get("agreement_type", ""),
                    }
                )

        hs_record = hs_records[0]
        duty_rate = hs_record.get("duty_rate", 0)
        preferential_rate = hs_record.get("preferential_rate")

        result: dict[str, Any] = {
            "item_code": item_code,
            "destination_country": destination_country,
            "eligible": True,
            "hs_code": hs_record.get("hs_code", ""),
            "duty_rate": duty_rate,
            "preferential_rate": preferential_rate,
            "agreements": matched_agreements,
        }

        logger.info(
            "수출 적격성 확인: %s → %s — 협정 %d건",
            item_code,
            destination_country,
            len(matched_agreements),
        )

        return result

    def _run_check(
        self,
        check_type: str,
        entity_name: str,
        entity_country: str,
    ) -> bool:
        """개별 점검을 실행한다.

        실제 환경에서는 외부 API(DPL/SDN 등)를 호출한다.
        현재는 기존 점검 이력에서 fail 기록이 있는지 조회한다.
        """
        existing_fails = self._check_repo.find_many(
            {
                "check_type": check_type,
                "entity_name": entity_name,
                "entity_country": entity_country,
                "result": "fail",
            },
            limit=1,
        )
        return len(existing_fails) > 0

    def _calculate_risk_level(self, score: int) -> str:
        """점수 기반 위험 수준을 판정한다."""
        if score >= 15:
            return "critical"
        if score >= 10:
            return "high"
        if score >= 5:
            return "medium"
        return "low"
