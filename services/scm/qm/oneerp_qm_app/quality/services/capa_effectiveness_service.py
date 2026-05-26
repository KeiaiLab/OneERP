"""CAPA 효과성 검증 서비스 — 8D Report 단계 진행 + 마감 후 재발 추적.

BR-QI-CAPA-EXT-001: 8D Report D0~D8 순차 진행 보장
BR-QI-CAPA-EXT-002: 마감 후 6/8개월 effectiveness check 스케줄링
BR-QI-CAPA-EXT-003: 동일 원인 재발 발견 시 CAPA 자동 재개(reopen)

8D 방법론 개요:
- D0: 비상 대응 계획 (Prepare & Plan)
- D1: 팀 구성 (Form a Team)
- D2: 문제 정의 (Define the Problem)
- D3: 봉쇄 조치 (Contain the Problem)
- D4: 근본 원인 분석 (Identify Root Cause)
- D5: 영구 시정조치 도출 (Develop Corrective Actions)
- D6: 시정조치 실행 (Implement Corrective Actions)
- D7: 재발 방지 (Prevent Recurrence)
- D8: 팀 인정 (Recognize the Team) + CAPA 공식 마감
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 8D 단계 순서 — 순차 진행 강제에 사용
EIGHT_D_STEPS: tuple[str, ...] = (
    "D0",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "D8",
)


class CAPAEffectivenessService:
    """CAPA 효과성 검증 및 8D 진행 관리 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._capa_repo = Repository("capas", tenant_id=tenant_id)
        self._nc_repo = Repository("non_conformances", tenant_id=tenant_id)

    def advance_8d_step(
        self,
        capa_id: str,
        next_step: str,
        *,
        notes: str = "",
    ) -> dict[str, Any]:
        """8D 단계를 다음 단계로 순차 진행시킨다.

        Args:
            capa_id: CAPA 문서 ID
            next_step: 다음 단계 (D0~D8 중 하나)
            notes: 단계 전환 시 메모

        Returns:
            {capa_id, current_step, is_closed}

        Raises:
            ValueError: CAPA 미존재 / 단계 순서 위반 / 잘못된 단계명
        """
        if next_step not in EIGHT_D_STEPS:
            msg = f"유효하지 않은 8D 단계: {next_step}"
            raise ValueError(msg)

        capa = self._capa_repo.find_by_id(capa_id)
        if not capa:
            msg = f"CAPA '{capa_id}'를 찾을 수 없습니다"
            raise ValueError(msg)

        current = capa.get("current_8d_step", "D0")
        current_idx = EIGHT_D_STEPS.index(current) if current in EIGHT_D_STEPS else 0
        next_idx = EIGHT_D_STEPS.index(next_step)

        # 순차 진행 강제 — 건너뛰기 금지
        if next_idx != current_idx + 1:
            msg = (
                f"8D 단계 순서 위반: {current} → {next_step} 직접 전환 불가 "
                f"(반드시 다음 단계로만 진행)"
            )
            raise ValueError(msg)

        now = datetime.now(tz=UTC)
        history_entry = {
            "step": next_step,
            "transitioned_at": now.isoformat(),
            "notes": notes,
        }
        existing_history = list(capa.get("step_history", []))
        existing_history.append(history_entry)

        update_payload: dict[str, Any] = {
            "current_8d_step": next_step,
            "step_history": existing_history,
        }

        # D8 도달 시 공식 마감
        is_closed = False
        if next_step == "D8":
            update_payload["is_closed"] = True
            update_payload["closed_at"] = now.date()
            is_closed = True

        self._capa_repo.update_by_id(capa_id, update_payload)

        logger.info(
            "8D 단계 진행: CAPA=%s, %s → %s (마감=%s)",
            capa_id,
            current,
            next_step,
            is_closed,
        )

        return {
            "capa_id": capa_id,
            "previous_step": current,
            "current_step": next_step,
            "is_closed": is_closed,
        }

    def schedule_effectiveness_check(
        self,
        capa_id: str,
        *,
        check_after_months: int = 6,
    ) -> dict[str, Any]:
        """마감된 CAPA의 효과성 검증 예정일을 산출해 기록한다.

        ISO 9001 10.2 best practice: 6개월 또는 8개월 후 재발 여부 확인.

        Args:
            capa_id: CAPA ID
            check_after_months: 마감 후 몇 개월 후 검증할지 (기본 6)

        Returns:
            {capa_id, check_date}

        Raises:
            ValueError: CAPA 미존재 / 미마감 CAPA
        """
        capa = self._capa_repo.find_by_id(capa_id)
        if not capa:
            msg = f"CAPA '{capa_id}'를 찾을 수 없습니다"
            raise ValueError(msg)
        if not capa.get("is_closed", False):
            msg = "마감된 CAPA만 효과성 검증을 예약할 수 있습니다"
            raise ValueError(msg)

        closed_at = capa.get("closed_at")
        if isinstance(closed_at, str):
            closed_at = date.fromisoformat(closed_at)
        elif closed_at is None:
            closed_at = datetime.now(tz=UTC).date()

        # 근사치로 1개월=30일
        check_date = closed_at + timedelta(days=check_after_months * 30)

        self._capa_repo.update_by_id(
            capa_id,
            {"effectiveness_check_date": check_date},
        )

        logger.info(
            "CAPA 효과성 검증 예정: %s → %s (마감=%s, %d개월 후)",
            capa_id,
            check_date,
            closed_at,
            check_after_months,
        )

        return {"capa_id": capa_id, "check_date": check_date}

    def verify_effectiveness(self, capa_id: str) -> dict[str, Any]:
        """CAPA 마감 이후 동일 원인의 재발 여부를 확인해 효과성을 판정한다.

        판정 규칙:
        - CAPA의 root_cause와 동일한 root_cause_ref를 가진 NC가
          closed_at 이후 기간 내에 1건 이상 발견 → 실패(CAPA 재개)
        - 0건 → 성공(effectiveness_verified=True)

        Args:
            capa_id: CAPA ID

        Returns:
            {capa_id, effectiveness_verified, recurrence_count}
        """
        capa = self._capa_repo.find_by_id(capa_id)
        if not capa:
            msg = f"CAPA '{capa_id}'를 찾을 수 없습니다"
            raise ValueError(msg)

        root_cause = capa.get("root_cause", "")
        closed_at = capa.get("closed_at")
        if isinstance(closed_at, str):
            closed_at = date.fromisoformat(closed_at)

        # 마감 이후 동일 root_cause로 발생한 NC 카운트
        recurrence_count = self._nc_repo.count(
            {
                "root_cause_ref": root_cause,
                "created_at": {"$gte": closed_at} if closed_at else {},
            },
        )

        verified = recurrence_count == 0

        update_payload: dict[str, Any] = {
            "effectiveness_verified": verified,
            "effectiveness_verified_at": datetime.now(tz=UTC).isoformat(),
            "recurrence_count": recurrence_count,
        }

        if not verified:
            # 재발 발견 → CAPA 재개(is_closed=False), 새 근본 원인 재분석 필요
            update_payload["is_closed"] = False
            update_payload["reopen_reason"] = (
                f"효과성 검증 실패: 동일 원인 재발 {recurrence_count}건"
            )
            logger.warning(
                "CAPA 효과성 검증 실패: %s (재발 %d건) → 재개",
                capa_id,
                recurrence_count,
            )
        else:
            logger.info("CAPA 효과성 검증 통과: %s", capa_id)

        self._capa_repo.update_by_id(capa_id, update_payload)

        return {
            "capa_id": capa_id,
            "effectiveness_verified": verified,
            "recurrence_count": recurrence_count,
        }
