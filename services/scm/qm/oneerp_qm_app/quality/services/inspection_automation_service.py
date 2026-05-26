"""검사 자동화 서비스 — 입고/공정 중 자동 검사 트리거, 불합격->NC 자동 생성.

L2 비즈니스 룰 매핑:
- BR-QI-003: 입고 시 자동 검사 (purchase_receipt 이벤트 -> incoming 검사)
- BR-QI-004: 공정 중 자동 검사 (stock_entry 이벤트 -> in_process 검사)
- BR-NC-001: 불합격 시 NC 자동 생성 (result=rejected -> NC)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_qm_app.quality.models.non_conformance import NonConformance
from oneerp_qm_app.quality.models.quality_inspection import (
    InspectionReferenceType,
    InspectionType,
    QualityInspection,
)

logger = logging.getLogger(__name__)


class InspectionAutomationService:
    """검사 자동화 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._inspection_repo = Repository("quality_inspections", tenant_id=tenant_id)
        self._nc_repo = Repository("non_conformances", tenant_id=tenant_id)

    def trigger_incoming_inspection(self, reference_no: str, item_code: str) -> dict[str, Any]:
        """입고 시 자동 검사를 생성한다."""
        inspection_id = generate_name("QI", tenant_id=self._tenant_id)
        doc = QualityInspection(
            _id=inspection_id,
            reference_type=InspectionReferenceType.PURCHASE_RECEIPT,
            reference_no=reference_no,
            inspection_type=InspectionType.INCOMING,
            item_code=item_code,
            tenant_id=self._tenant_id,
        )
        self._inspection_repo.insert(doc)
        logger.info(
            "입고 검사 생성: %s (참조: %s, 품목: %s)", inspection_id, reference_no, item_code
        )
        return {"inspection_id": inspection_id, "inspection_type": "incoming"}

    def trigger_in_process_inspection(self, reference_no: str, item_code: str) -> dict[str, Any]:
        """공정 중 검사를 생성한다."""
        inspection_id = generate_name("QI", tenant_id=self._tenant_id)
        doc = QualityInspection(
            _id=inspection_id,
            reference_type=InspectionReferenceType.STOCK_ENTRY,
            reference_no=reference_no,
            inspection_type=InspectionType.IN_PROCESS,
            item_code=item_code,
            tenant_id=self._tenant_id,
        )
        self._inspection_repo.insert(doc)
        logger.info(
            "공정 중 검사 생성: %s (참조: %s, 품목: %s)", inspection_id, reference_no, item_code
        )
        return {"inspection_id": inspection_id, "inspection_type": "in_process"}

    def auto_create_nc_on_failure(self, inspection_id: str) -> dict[str, Any] | None:
        """불합격 검사에 대해 NC를 자동 생성한다. 합격이면 None 반환."""
        inspection = self._inspection_repo.find_by_id(inspection_id)
        if not inspection:
            raise_not_found(f"검사 '{inspection_id}'를 찾을 수 없습니다")

        if inspection.get("result") == "accepted":
            logger.info("검사 합격 — NC 생성 불필요: %s", inspection_id)
            return None

        nc_id = generate_name("NC", tenant_id=self._tenant_id)
        nc_doc = NonConformance(
            _id=nc_id,
            title=f"자동 NC — {inspection.get('item_code', '')}",
            description=f"검사 {inspection_id} 불합격으로 자동 생성",
            severity="minor",
            item_code=inspection.get("item_code", ""),
            inspection_id=inspection_id,
            tenant_id=self._tenant_id,
        )
        self._nc_repo.insert(nc_doc)
        logger.info("불합격 NC 자동 생성: %s (검사: %s)", nc_id, inspection_id)
        return {"nc_id": nc_id, "inspection_id": inspection_id}
