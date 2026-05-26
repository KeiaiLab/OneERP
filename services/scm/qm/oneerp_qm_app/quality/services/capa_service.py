"""시정예방조치(CAPA) 서비스 — NC->CAPA 생성, 마감, 초과 관리.

L2 비즈니스 룰 매핑:
- BR-CA-001: NC 존재 검증
- BR-CA-002: CAPA 존재 검증
- BR-CA-003: 조치 미기입 마감 금지
- BR-CA-004: 기한 초과 기준 (due_date < 기준일)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_qm_app.quality.models.capa import Capa

logger = logging.getLogger(__name__)


class CAPAService:
    """CAPA 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._capa_repo = Repository("capas", tenant_id=tenant_id)
        self._nc_repo = Repository("non_conformances", tenant_id=tenant_id)

    def create_capa_from_nc(
        self,
        nc_id: str,
        capa_type: str,
        corrective_action: str,
        responsible: str,
        due_date: date,
    ) -> dict[str, Any]:
        """부적합(NC)으로부터 CAPA를 생성한다."""
        nc = self._nc_repo.find_by_id(nc_id)
        if not nc:
            raise_not_found(f"부적합 '{nc_id}'를 찾을 수 없습니다")

        capa_id = generate_name("CAPA", tenant_id=self._tenant_id)
        doc = Capa(
            _id=capa_id,
            capa_type=capa_type,
            problem_description=nc.get("description", ""),
            corrective_action=corrective_action,
            responsible=responsible,
            due_date=due_date,
            is_closed=False,
            tenant_id=self._tenant_id,
        )
        self._capa_repo.insert(doc)

        logger.info("CAPA 생성: %s (NC: %s)", capa_id, nc_id)
        return {"capa_id": capa_id, "nc_id": nc_id, "capa_type": capa_type}

    def close_capa(self, capa_id: str, *, effectiveness_verified: bool = False) -> dict[str, Any]:
        """CAPA를 마감한다. 조치 미기입 시 에러."""
        capa = self._capa_repo.find_by_id(capa_id)
        if not capa:
            raise_not_found(f"CAPA '{capa_id}'를 찾을 수 없습니다")

        if not capa.get("corrective_action"):
            raise_unprocessable(
                "ERR-QTY-001",
                "조치(corrective_action)가 기입되지 않은 CAPA는 마감할 수 없습니다",
            )

        self._capa_repo.update_by_id(
            capa_id,
            {"is_closed": True, "effectiveness_verified": effectiveness_verified},
        )
        logger.info("CAPA 마감: %s (효과성 검증: %s)", capa_id, effectiveness_verified)
        return {"capa_id": capa_id, "is_closed": True}

    def get_overdue_capas(self, as_of_date: date | None = None) -> list[dict[str, Any]]:
        """기한 초과 CAPA 목록을 반환한다."""
        ref_date = as_of_date or datetime.now(tz=UTC).date()
        return self._capa_repo.find_many(
            {"is_closed": False, "due_date": {"$lt": ref_date}},
            limit=100,
        )

    def get_capa_statistics(self) -> dict[str, int]:
        """CAPA 통계를 반환한다 — 총/열린/마감/초과 건수."""
        total = self._capa_repo.count()
        open_count = self._capa_repo.count({"is_closed": False})
        closed_count = self._capa_repo.count({"is_closed": True})
        overdue_count = self._capa_repo.count(
            {"is_closed": False, "due_date": {"$lt": datetime.now(tz=UTC).date()}}
        )
        return {
            "total": total,
            "open": open_count,
            "closed": closed_count,
            "overdue": overdue_count,
        }
