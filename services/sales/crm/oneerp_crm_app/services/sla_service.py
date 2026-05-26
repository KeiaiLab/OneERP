"""SLA 서비스 — SLA 평가, 위반 조회, 이행률 계산, 에스컬레이션.

L2 비즈니스 룰 매핑:
- BR-CRM-004: SLA 자동 평가 (우선순위별 SLA 매칭, 경과시간 비교)
- BR-CRM-005: SLA 위반 에스컬레이션 (breach 기록 + 로그)
- BR-CRM-014: 서비스 계약 유효기간 검증 (end_date < today → 만료)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any, cast

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class SLAService:
    """SLA 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._sla_repo = Repository("service_level_agreements", tenant_id=tenant_id)
        self._fulfillment_repo = Repository("sla_fulfillments", tenant_id=tenant_id)
        self._issue_repo = Repository("issues", tenant_id=tenant_id)
        self._contract_repo = Repository("service_contracts", tenant_id=tenant_id)

    def evaluate_sla(
        self,
        entity_id: str,
        entity_type: str = "issue",
    ) -> dict[str, Any]:
        """BR-CRM-004: 엔티티에 대해 SLA를 매칭하고 이행 여부를 평가한다."""
        # 엔티티 조회
        entity = self._issue_repo.find_by_id(entity_id)
        if not entity:
            raise_not_found(f"엔티티 '{entity_id}'을 찾을 수 없습니다")

        priority = entity.get("priority", "medium")

        # 해당 엔티티 유형과 우선순위에 매칭되는 SLA 조회
        slas = self._sla_repo.find_many(
            {"entity_type": entity_type, "priority": priority, "is_active": True},
            limit=1,
        )
        if not slas:
            return {"entity_id": entity_id, "matched": False, "message": "매칭되는 SLA가 없습니다"}

        sla = slas[0]
        sla_id = sla.get("_id", "")
        resolution_time = float(sla.get("resolution_time", 0))
        response_time = float(sla.get("response_time", 0))

        now = datetime.now(tz=UTC)

        # 생성 시각 파싱
        created_at = entity.get("created_at", now)
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elapsed_hours = (now - created_at).total_seconds() / 3600

        # 응답 시간 계산: first_response_at 기준, 없으면 현재까지 경과 시간
        first_response_at = entity.get("first_response_at")
        if first_response_at:
            if isinstance(first_response_at, str):
                first_response_at = datetime.fromisoformat(first_response_at)
            response_elapsed = (first_response_at - created_at).total_seconds() / 3600
        else:
            response_elapsed = elapsed_hours

        status = entity.get("status", "open")
        is_resolved = status in ("resolved", "closed")

        # 응답/해결 시간 위반 여부 개별 판정
        response_breach = response_time > 0 and response_elapsed > response_time
        resolution_breach = not is_resolved and elapsed_hours > resolution_time

        # 둘 중 하나라도 위반이면 미이행
        is_fulfilled = not response_breach and (is_resolved or elapsed_hours <= resolution_time)

        # 이행 기록 생성
        fulfillment_id = generate_name("SLAF", tenant_id=self._tenant_id)
        self._fulfillment_repo.insert(
            {
                "_id": fulfillment_id,
                "sla": sla_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "is_fulfilled": is_fulfilled,
                "elapsed_hours": round(elapsed_hours, 2),
                "response_elapsed_hours": round(response_elapsed, 2),
                "resolution_time_limit": resolution_time,
                "response_time_limit": response_time,
                "response_breach": response_breach,
                "resolution_breach": resolution_breach,
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("SLA 평가: %s (SLA: %s, 이행: %s)", entity_id, sla_id, is_fulfilled)
        return {
            "entity_id": entity_id,
            "matched": True,
            "sla_id": sla_id,
            "is_fulfilled": is_fulfilled,
            "elapsed_hours": round(elapsed_hours, 2),
            "response_elapsed_hours": round(response_elapsed, 2),
            "response_breach": response_breach,
            "resolution_breach": resolution_breach,
            "fulfillment_id": fulfillment_id,
        }

    def check_violations(self) -> dict[str, Any]:
        """BR-CRM-005: 미해결 이슈 중 SLA 위반 건을 조회한다."""
        # 미해결 이슈 목록 조회
        open_issues = self._issue_repo.find_many(
            {"status": {"$in": ["open", "in_progress"]}}, limit=10000
        )

        violations: list[dict[str, Any]] = []
        for issue in open_issues:
            priority = issue.get("priority", "medium")
            slas = self._sla_repo.find_many(
                {"entity_type": "issue", "priority": priority, "is_active": True},
                limit=1,
            )
            if not slas:
                continue

            sla = slas[0]
            resolution_time = float(sla.get("resolution_time", 0))
            created_at = issue.get("created_at", datetime.now(tz=UTC))
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            elapsed_hours = (datetime.now(tz=UTC) - created_at).total_seconds() / 3600
            if elapsed_hours > resolution_time:
                violations.append(
                    {
                        "issue_id": issue.get("_id"),
                        "sla_id": sla.get("_id"),
                        "elapsed_hours": round(elapsed_hours, 2),
                        "resolution_time_limit": resolution_time,
                        "priority": priority,
                    }
                )

        return {"violations": violations, "total": len(violations)}

    def get_fulfillment_rate(
        self,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> dict[str, Any]:
        """SLA 이행률을 계산한다."""
        query: dict[str, Any] = {}
        if period_start or period_end:
            date_filter: dict[str, Any] = {}
            if period_start:
                date_filter["$gte"] = period_start
            if period_end:
                date_filter["$lte"] = period_end
            query["created_at"] = date_filter

        fulfillments = self._fulfillment_repo.find_many(query, limit=10000)
        total = len(fulfillments)
        fulfilled = sum(1 for f in fulfillments if f.get("is_fulfilled"))
        rate = round(fulfilled / total * 100, 2) if total > 0 else 0.0

        return {
            "total": total,
            "fulfilled": fulfilled,
            "breached": total - fulfilled,
            "fulfillment_rate": rate,
        }

    def list_fulfillments(self, *, skip: int, limit: int) -> dict[str, Any]:
        """SLA 이행 목록을 페이지네이션으로 조회한다."""
        items = self._fulfillment_repo.find_many(skip=skip, limit=limit, sort=[("created_at", -1)])
        total = self._fulfillment_repo.count()
        return {"items": items, "total": total}

    def escalate_breach(
        self,
        entity_id: str,
        breach_type: str,
    ) -> dict[str, Any]:
        """BR-CRM-005: SLA 위반 에스컬레이션을 기록한다."""
        entity = self._issue_repo.find_by_id(entity_id)
        if not entity:
            raise_not_found(f"엔티티 '{entity_id}'을 찾을 수 없습니다")

        # 이슈에 에스컬레이션 플래그 추가
        self._issue_repo.update_by_id(
            entity_id,
            {
                "escalated": True,
                "escalation_type": breach_type,
                "escalated_at": datetime.now(tz=UTC),
            },
        )

        logger.info("SLA 위반 에스컬레이션: %s (유형: %s)", entity_id, breach_type)
        return {
            "entity_id": entity_id,
            "breach_type": breach_type,
            "escalated": True,
        }

    # ------------------------------------------------------------------
    # BR-CRM-014: 서비스 계약 유효기간 검증
    # ------------------------------------------------------------------

    def check_contract_validity(self, contract_id: str) -> dict[str, Any]:
        """BR-CRM-014: 서비스 계약의 유효기간을 확인한다.

        service_contracts 컬렉션에서 end_date < today이면 만료 상태를 반환한다.
        만료된 계약은 is_active를 False로 갱신한다.
        """
        contract = self._contract_repo.find_by_id(contract_id)
        if not contract:
            raise_not_found(f"서비스 계약 '{contract_id}'을 찾을 수 없습니다")

        end_date = contract.get("end_date")
        if end_date is None:
            raise_unprocessable(
                "ERR-CRM-014", f"서비스 계약 '{contract_id}'에 종료일이 설정되지 않았습니다"
            )

        # 문자열이면 date로 파싱
        if isinstance(end_date, str):
            from datetime import date as _date_type

            end_date = _date_type.fromisoformat(end_date)
        if end_date is None:
            raise_unprocessable(
                "ERR-CRM-014", f"서비스 계약 '{contract_id}'에 종료일이 설정되지 않았습니다"
            )
        end_date = cast("date", end_date)

        today = datetime.now(tz=UTC).date()
        is_expired = end_date < today

        if is_expired:
            self._contract_repo.update_by_id(contract_id, {"is_active": False})
            logger.info("서비스 계약 만료 처리: %s (종료일: %s)", contract_id, end_date)

        return {
            "contract_id": contract_id,
            "end_date": str(end_date),
            "is_expired": is_expired,
            "is_active": not is_expired,
        }
