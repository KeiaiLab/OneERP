"""영업 파이프라인 서비스 — 리드 전환, 단계 진행, 견적 전환, 파이프라인 집계.

L2 비즈니스 룰 매핑:
- BR-CRM-001: 리드 -> 기회 전환 (lead status=converted, Opportunity 생성)
- BR-CRM-002: 기회 상태 전이 규칙 (open->quotation/won/lost)
- BR-CRM-003: 기회 -> 견적 전환 (OPPORTUNITY_CONVERTED 이벤트)
- BR-CRM-008: 파이프라인 요약 (stage별 deal_count/total_value)
- BR-CRM-009: 전환율 메트릭 (리드->기회, 기회->성사)
- BR-CRM-017: 리드 스코어링 가중치 (criteria별 가중치 적용 → total_score)
- BR-CRM-019: 설문 응답 집계 (평균 점수, 응답 수)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.events.outbox import OutboxMixin
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 기회 단계 전환 규칙: 현재 상태 → 허용 다음 상태
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "open": {"quotation", "won", "lost"},
    "quotation": {"won", "lost"},
}


class PipelineService:
    """영업 파이프라인 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._lead_repo = Repository("leads", tenant_id=tenant_id)
        self._opp_repo = Repository("opportunities", tenant_id=tenant_id)
        self._scoring_repo = Repository("lead_scorings", tenant_id=tenant_id)
        self._survey_repo = Repository("survey_responses", tenant_id=tenant_id)
        # M3 — sales_pipelines 도 PipelineService 가 책임 (route Repository 직접 호출 제거 대응)
        self._pipeline_repo = Repository("sales_pipelines", tenant_id=tenant_id)

    def convert_lead_to_opportunity(
        self,
        lead_id: str,
        opportunity_type: str = "sales",
        expected_amount: Decimal = Decimal(0),
        probability: Decimal = Decimal(0),
        close_date: date | None = None,
    ) -> dict[str, Any]:
        """리드를 기회로 전환한다.

        리드 status를 'converted'로 변경하고 새로운 Opportunity를 생성한다.
        """
        lead = self._lead_repo.find_by_id(lead_id)
        if not lead:
            raise_not_found(f"리드 '{lead_id}'을 찾을 수 없습니다")

        if lead.get("status") == "converted":
            raise_unprocessable("ERR-CRM-001", f"리드 '{lead_id}'은 이미 전환되었습니다")

        # 리드 상태를 converted로 변경
        self._lead_repo.update_by_id(lead_id, {"status": "converted"})

        # 기회 생성
        opp_id = generate_name("OPP", tenant_id=self._tenant_id)
        from oneerp_crm_app.models.opportunity import (
            Opportunity,
            OpportunityStatus,
            OpportunityType,
        )

        opp = Opportunity(
            _id=opp_id,
            tenant_id=self._tenant_id,
            lead_ref=lead_id,
            opportunity_type=OpportunityType(opportunity_type),
            expected_amount=expected_amount,
            probability=probability,
            close_date=close_date,
            status=OpportunityStatus.OPEN,
        )
        self._opp_repo.insert(opp)

        logger.info("리드→기회 전환: %s → %s", lead_id, opp_id)
        return {"lead_id": lead_id, "opportunity_id": opp_id, "status": "open"}

    def advance_stage(
        self,
        opportunity_id: str,
        new_stage: str,
    ) -> dict[str, Any]:
        """기회의 단계를 진행한다 (유효 전환만 허용)."""
        opp = self._opp_repo.find_by_id(opportunity_id)
        if not opp:
            raise_not_found(f"기회 '{opportunity_id}'을 찾을 수 없습니다")

        current = opp.get("status", "open")
        allowed = _VALID_TRANSITIONS.get(current, set())
        if new_stage not in allowed:
            raise_unprocessable(
                "ERR-CRM-002", f"'{current}'에서 '{new_stage}'(으)로 전환할 수 없습니다"
            )

        self._opp_repo.update_by_id(opportunity_id, {"status": new_stage})
        logger.info("기회 단계 진행: %s %s → %s", opportunity_id, current, new_stage)
        return {"opportunity_id": opportunity_id, "previous_stage": current, "new_stage": new_stage}

    def convert_opportunity_to_quotation(
        self,
        opportunity_id: str,
        customer_id: str,
        items: list[dict[str, Any]],
        valid_till: date | None = None,
    ) -> dict[str, Any]:
        """기회를 견적으로 전환한다.

        selling 서비스의 quotations 컬렉션에 직접 쓰지 않고,
        OPPORTUNITY_CONVERTED 이벤트를 Outbox에 기록하여
        selling 서비스가 자체적으로 Quotation을 생성하도록 위임한다.
        """
        opp = self._opp_repo.find_by_id(opportunity_id)
        if not opp:
            raise_not_found(f"기회 '{opportunity_id}'을 찾을 수 없습니다")

        # 기회 상태를 quotation으로 변경하고, Outbox 이벤트를 원자적으로 기록
        outbox_entry = OutboxMixin.create_outbox_entry(
            event_type=EventType.OPPORTUNITY_CONVERTED,
            doc_id=opportunity_id,
            tenant_id=self._tenant_id,
            data={
                "opportunity_id": opportunity_id,
                "customer_id": customer_id,
                "items": items,
                "valid_till": str(valid_till) if valid_till else None,
            },
        )
        self._opp_repo.update_by_id(
            opportunity_id,
            {"status": "quotation", "_outbox_pending": [outbox_entry]},
        )

        logger.info("기회→견적 전환 이벤트 발행: %s", opportunity_id)
        return {"opportunity_id": opportunity_id}

    def mark_won(self, opportunity_id: str) -> dict[str, Any]:
        """기회를 성사(won)로 표시한다."""
        return self.advance_stage(opportunity_id, "won")

    def mark_lost(
        self,
        opportunity_id: str,
        lost_reason: str = "",
        competitor: str = "",
    ) -> dict[str, Any]:
        """기회를 실패(lost)로 표시한다."""
        opp = self._opp_repo.find_by_id(opportunity_id)
        if not opp:
            raise_not_found(f"기회 '{opportunity_id}'을 찾을 수 없습니다")

        current = opp.get("status", "open")
        allowed = _VALID_TRANSITIONS.get(current, set())
        if "lost" not in allowed:
            raise_unprocessable("ERR-CRM-003", f"'{current}'에서 'lost'(으)로 전환할 수 없습니다")

        self._opp_repo.update_by_id(
            opportunity_id,
            {"status": "lost", "lost_reason": lost_reason, "competitor": competitor},
        )
        logger.info("기회 실패 처리: %s (사유: %s)", opportunity_id, lost_reason)
        return {
            "opportunity_id": opportunity_id,
            "status": "lost",
            "lost_reason": lost_reason,
            "competitor": competitor,
        }

    def get_pipeline_summary(self) -> dict[str, Any]:
        """단계별 건수 + 금액을 집계한다."""
        stages = ["open", "quotation", "won", "lost"]
        summary: list[dict[str, Any]] = []

        for stage in stages:
            opps = self._opp_repo.find_many({"status": stage}, limit=10000)
            total_amount = sum(float(o.get("expected_amount", 0)) for o in opps)
            summary.append(
                {
                    "stage": stage,
                    "count": len(opps),
                    "total_amount": total_amount,
                }
            )

        return {"stages": summary}

    def get_conversion_metrics(self) -> dict[str, Any]:
        """리드→기회, 기회→성사 전환율을 계산한다."""
        total_leads = self._lead_repo.count()
        converted_leads = self._lead_repo.count({"status": "converted"})
        lead_to_opp_rate = round(converted_leads / total_leads * 100, 2) if total_leads > 0 else 0.0

        total_opps = self._opp_repo.count()
        won_opps = self._opp_repo.count({"status": "won"})
        opp_to_won_rate = round(won_opps / total_opps * 100, 2) if total_opps > 0 else 0.0

        return {
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "lead_to_opportunity_rate": lead_to_opp_rate,
            "total_opportunities": total_opps,
            "won_opportunities": won_opps,
            "opportunity_to_won_rate": opp_to_won_rate,
        }

    # ------------------------------------------------------------------
    # BR-CRM-017: 리드 스코어링 가중치
    # ------------------------------------------------------------------

    def calculate_lead_score(self, lead_id: str) -> dict[str, Any]:
        """BR-CRM-017: 리드 스코어링 가중치를 적용하여 total_score를 산출한다.

        lead_scorings 컬렉션에서 해당 리드의 criteria를 조회하고,
        리드 속성에 가중치를 곱한 값을 합산하여 총점을 계산한다.
        """
        lead = self._lead_repo.find_by_id(lead_id)
        if not lead:
            raise_not_found(f"리드 '{lead_id}'을 찾을 수 없습니다")

        # 해당 리드의 스코어링 기준 조회
        criteria_list = self._scoring_repo.find_many({"lead_id": lead_id}, limit=1000)
        if not criteria_list:
            raise_unprocessable("ERR-CRM-017", f"리드 '{lead_id}'에 대한 스코어링 기준이 없습니다")

        total_score = Decimal(0)
        details: list[dict[str, Any]] = []
        for criterion in criteria_list:
            field = str(criterion.get("scoring_criteria", ""))
            weight = Decimal(str(criterion.get("score", 0)))
            # 리드 속성 값 확인: 속성이 존재하고 비어있지 않으면 가중치 적용
            lead_value = lead.get(field)
            matched = lead_value is not None and lead_value != "" and lead_value != 0
            applied = weight if matched else Decimal(0)
            total_score += applied
            details.append(
                {
                    "criteria": field,
                    "weight": float(weight),
                    "matched": matched,
                    "applied_score": float(applied),
                }
            )

        # 리드의 score 필드 갱신
        self._lead_repo.update_by_id(lead_id, {"lead_score": float(total_score)})

        logger.info("리드 스코어링: %s → 총점 %s", lead_id, total_score)
        return {
            "lead_id": lead_id,
            "total_score": float(total_score),
            "criteria_count": len(criteria_list),
            "details": details,
        }

    # ------------------------------------------------------------------
    # BR-CRM-019: 설문 응답 집계
    # ------------------------------------------------------------------

    def aggregate_survey_responses(self, survey_id: str) -> dict[str, Any]:
        """BR-CRM-019: 설문 응답을 집계한다 (평균 점수, 응답 수).

        survey_responses 컬렉션에서 해당 survey_id의 응답을 조회하여
        평균 점수와 총 응답 수를 반환한다.
        """
        responses = self._survey_repo.find_many({"survey_id": survey_id}, limit=10000)
        if not responses:
            return {
                "survey_id": survey_id,
                "response_count": 0,
                "average_score": 0.0,
            }

        scores = [float(r.get("score", 0)) for r in responses]
        avg_score = round(sum(scores) / len(scores), 2)

        logger.info("설문 집계: %s → 응답 %d건, 평균 %.2f", survey_id, len(scores), avg_score)
        return {
            "survey_id": survey_id,
            "response_count": len(scores),
            "average_score": avg_score,
        }

    # M3 arch-baseline 감소 — sales_pipelines.py 의 _get_repo() 흡수
    def list_pipelines(self, *, skip: int, limit: int) -> dict[str, Any]:
        """영업파이프라인 목록을 페이지네이션으로 조회 (Route → Service 분리)."""
        data = self._pipeline_repo.find_many(skip=skip, limit=limit, sort=[("created_at", -1)])
        total = self._pipeline_repo.count()
        return {"data": data, "total": total}
