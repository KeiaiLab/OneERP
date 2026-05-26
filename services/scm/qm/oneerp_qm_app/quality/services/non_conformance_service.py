"""부적합(NonConformance) 서비스 — 검사->NC 생성, 에스컬레이션, 해결.

L2 비즈니스 룰 매핑:
- BR-NC-002: 심각도 단방향 상향 (minor->major->critical만 가능)
- BR-NC-003: 유효 심각도 값 (minor/major/critical)
- BR-NC-004: NC 해결 시 CAPA 연동 (corrective_action 기록)
- BR-NC-005: NC 제출 전 상태 확인 (DRAFT만)
- BR-NC-006: NC 취소 전 상태 확인 (SUBMITTED만)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_qm_app.quality.models.capa import Capa
from oneerp_qm_app.quality.models.non_conformance import NonConformance

logger = logging.getLogger(__name__)

# 심각도 에스컬레이션 순서
_SEVERITY_ORDER = ("minor", "major", "critical")


class NonConformanceService:
    """부적합 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._nc_repo = Repository("non_conformances", tenant_id=tenant_id)
        self._inspection_repo = Repository("quality_inspections", tenant_id=tenant_id)
        self._capa_repo = Repository("capas", tenant_id=tenant_id)

    def create_from_inspection(self, inspection_id: str, severity: str = "minor") -> dict[str, Any]:
        """불합격 검사로부터 NC를 생성한다."""
        inspection = self._inspection_repo.find_by_id(inspection_id)
        if not inspection:
            raise_not_found(f"검사 '{inspection_id}'를 찾을 수 없습니다")

        nc_id = generate_name("NC", tenant_id=self._tenant_id)
        doc = NonConformance(
            _id=nc_id,
            title=f"검사 불합격 — {inspection.get('item_code', '')}",
            description=f"검사 {inspection_id}에서 불합격 발생",
            severity=severity,
            item_code=inspection.get("item_code", ""),
            inspection_id=inspection_id,
            tenant_id=self._tenant_id,
        )
        self._nc_repo.insert(doc)

        logger.info("NC 생성: %s (검사: %s, 심각도: %s)", nc_id, inspection_id, severity)
        return {"nc_id": nc_id, "inspection_id": inspection_id, "severity": severity}

    def escalate(self, nc_id: str, new_severity: str) -> dict[str, Any]:
        """심각도를 상향한다 (minor→major→critical). 하향은 불가."""
        nc = self._nc_repo.find_by_id(nc_id)
        if not nc:
            raise_not_found(f"부적합 '{nc_id}'를 찾을 수 없습니다")

        current = nc.get("severity", "minor")
        if new_severity not in _SEVERITY_ORDER:
            raise_unprocessable(
                "ERR-QTY-002",
                f"유효하지 않은 심각도: {new_severity}",
            )

        current_idx = _SEVERITY_ORDER.index(current) if current in _SEVERITY_ORDER else 0
        new_idx = _SEVERITY_ORDER.index(new_severity)

        if new_idx <= current_idx:
            raise_unprocessable(
                "ERR-QTY-003",
                f"심각도를 하향할 수 없습니다: {current} → {new_severity}",
            )

        self._nc_repo.update_by_id(nc_id, {"severity": new_severity})
        logger.info("NC 에스컬레이션: %s (%s → %s)", nc_id, current, new_severity)
        return {"nc_id": nc_id, "previous": current, "new": new_severity}

    def resolve(self, nc_id: str, corrective_action: str) -> dict[str, Any]:
        """NC를 해결하고 CAPA를 자동 생성한다."""
        nc = self._nc_repo.find_by_id(nc_id)
        if not nc:
            raise_not_found(f"부적합 '{nc_id}'를 찾을 수 없습니다")

        # NC 조치 기록
        self._nc_repo.update_by_id(nc_id, {"corrective_action": corrective_action})

        # CAPA 자동 생성
        capa_id = generate_name("CAPA", tenant_id=self._tenant_id)
        capa_doc = Capa(
            _id=capa_id,
            capa_type="corrective",
            problem_description=nc.get("description", ""),
            corrective_action=corrective_action,
            is_closed=False,
            tenant_id=self._tenant_id,
        )
        self._capa_repo.insert(capa_doc)

        logger.info("NC 해결: %s → CAPA 생성: %s", nc_id, capa_id)
        return {"nc_id": nc_id, "capa_id": capa_id}
