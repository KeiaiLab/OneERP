"""수익 인식 서비스 — 완료기준/진행률기준 수익 인식.

L2 비즈니스 룰 매핑:
- BR-PROJ-009: 완료기준 수익 인식 (100% 완료 시에만)
- BR-PROJ-010: 이미 전액 인식된 프로젝트는 추가 인식 불가
- BR-PROJ-011: 진행률기준 수익 인식 공식
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class RevenueRecognitionService:
    """수익 인식 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._project_repo = Repository("projects", tenant_id=tenant_id)
        self._recognition_repo = Repository("project_revenue_recognitions", tenant_id=tenant_id)
        self._billing_repo = Repository("project_billings", tenant_id=tenant_id)

    def _get_contract_value(self, project_id: str) -> Decimal:
        """프로젝트의 계약 총액을 청구 합계로 산출한다."""
        billings = self._billing_repo.find_many(
            {"project": project_id},
            limit=10000,
        )
        return sum(
            (Decimal(str(b.get("total", 0))) for b in billings),
            Decimal(0),
        )

    def _get_previously_recognized(self, project_id: str) -> Decimal:
        """기인식 수익 합계를 조회한다."""
        records = self._recognition_repo.find_many(
            {"project_id": project_id},
            limit=10000,
        )
        return sum(
            (Decimal(str(r.get("recognized_amount", 0))) for r in records),
            Decimal(0),
        )

    def recognize_by_completion(
        self,
        project_id: str,
        recognition_date: date,
    ) -> dict[str, Any]:
        """완료기준 수익 인식 — 100% 완료 시 전액 인식.

        프로젝트 percent_complete가 100이어야 인식한다.
        """
        project = self._project_repo.find_by_id(project_id)
        if not project:
            raise_not_found(f"프로젝트 '{project_id}'을 찾을 수 없습니다")

        percent = Decimal(str(project.get("percent_complete", 0)))
        if percent < Decimal(100):
            raise_unprocessable(
                "ERR-PRJ-005",
                f"프로젝트 완료율이 {percent}%입니다. 100% 완료 시에만 인식 가능합니다",
            )

        contract_value = self._get_contract_value(project_id)
        previously_recognized = self._get_previously_recognized(project_id)
        amount_to_recognize = contract_value - previously_recognized

        if amount_to_recognize <= 0:
            return {
                "project_id": project_id,
                "recognized_amount": Decimal(0),
                "message": "이미 전액 인식되었습니다",
            }

        rec_id = generate_name("PRREC", tenant_id=self._tenant_id)
        self._recognition_repo.insert(
            {
                "_id": rec_id,
                "project_id": project_id,
                "recognition_date": recognition_date,
                "recognized_amount": amount_to_recognize,
                "total_contract_value": contract_value,
                "completion_percentage": Decimal(100),
                "tenant_id": self._tenant_id,
            },
        )

        logger.info("완료기준 수익인식: %s — %s원", project_id, amount_to_recognize)
        return {
            "recognition_id": rec_id,
            "project_id": project_id,
            "recognized_amount": amount_to_recognize,
            "total_contract_value": contract_value,
            "completion_percentage": Decimal(100),
        }

    def recognize_by_progress(
        self,
        project_id: str,
        recognition_date: date,
    ) -> dict[str, Any]:
        """진행률기준 수익 인식 — 진행률 * 계약금 - 기인식 = 추가인식.

        프로젝트의 percent_complete를 기반으로 비례 인식한다.
        """
        project = self._project_repo.find_by_id(project_id)
        if not project:
            raise_not_found(f"프로젝트 '{project_id}'을 찾을 수 없습니다")

        percent = Decimal(str(project.get("percent_complete", 0)))
        contract_value = self._get_contract_value(project_id)
        previously_recognized = self._get_previously_recognized(project_id)

        # 진행률 * 계약금 - 기인식
        target = contract_value * percent / Decimal(100)
        amount_to_recognize = target - previously_recognized

        if amount_to_recognize <= 0:
            return {
                "project_id": project_id,
                "recognized_amount": Decimal(0),
                "message": "추가 인식할 금액이 없습니다",
            }

        rec_id = generate_name("PRREC", tenant_id=self._tenant_id)
        self._recognition_repo.insert(
            {
                "_id": rec_id,
                "project_id": project_id,
                "recognition_date": recognition_date,
                "recognized_amount": amount_to_recognize,
                "total_contract_value": contract_value,
                "completion_percentage": percent,
                "tenant_id": self._tenant_id,
            },
        )

        logger.info(
            "진행률기준 수익인식: %s — %s원 (%s%%)",
            project_id,
            amount_to_recognize,
            percent,
        )
        return {
            "recognition_id": rec_id,
            "project_id": project_id,
            "recognized_amount": amount_to_recognize,
            "total_contract_value": contract_value,
            "completion_percentage": percent,
        }
