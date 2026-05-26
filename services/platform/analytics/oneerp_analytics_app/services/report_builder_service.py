"""보고서 빌더 서비스 — 보고서 생성, 실행, 복제.

L2 비즈니스 룰 매핑:
- BR-08: 보고서 실행 (query 파싱 -> 집계 쿼리)
- BR-09: 보고서 내보내기 (xlsx/pdf)
- BR-10: 대용량 결과 제한 (10,000행)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_analytics_app.models.custom_report import CustomReport

logger = logging.getLogger(__name__)


class ReportBuilderService:
    """보고서 빌더 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._report_repo = Repository("custom_reports", tenant_id=tenant_id)

    def create_report(
        self,
        name: str,
        report_type: str,
        data_source: str,
        query: str,
        *,
        is_public: bool = False,
    ) -> dict[str, Any]:
        """커스텀 보고서를 생성한다."""
        report_id = generate_name("CUSRPT", tenant_id=self._tenant_id)
        doc = CustomReport(
            _id=report_id,
            report_name=name,
            report_type=report_type,
            data_source=data_source,
            query=query,
            is_public=is_public,
            tenant_id=self._tenant_id,
        )
        self._report_repo.insert(doc)
        logger.info("보고서 생성: %s (%s)", report_id, name)
        return {"report_id": report_id, "report_name": name}

    def execute_report(
        self, report_id: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """보고서를 실행한다. (현재는 메타데이터만 반환)"""
        report = self._report_repo.find_by_id(report_id)
        if not report:
            raise_not_found(f"보고서 '{report_id}'를 찾을 수 없습니다")

        logger.info("보고서 실행: %s (파라미터: %s)", report_id, parameters)
        return {
            "report_id": report_id,
            "report_name": report.get("report_name", ""),
            "query": report.get("query", ""),
            "parameters": parameters or {},
            "data": [],
        }

    def clone_report(self, report_id: str, new_name: str) -> dict[str, Any]:
        """기존 보고서를 복제한다."""
        original = self._report_repo.find_by_id(report_id)
        if not original:
            raise_not_found(f"보고서 '{report_id}'를 찾을 수 없습니다")

        new_id = generate_name("CUSRPT", tenant_id=self._tenant_id)
        doc = CustomReport(
            _id=new_id,
            report_name=new_name,
            report_type=original.get("report_type", ""),
            data_source=original.get("data_source", ""),
            query=original.get("query", ""),
            is_public=False,
            tenant_id=self._tenant_id,
        )
        self._report_repo.insert(doc)
        logger.info("보고서 복제: %s → %s", report_id, new_id)
        return {"report_id": new_id, "cloned_from": report_id, "report_name": new_name}
