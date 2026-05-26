"""결재 데이터바인딩 서비스 — ERP 도큐먼트 데이터를 결재 양식에 바인딩."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 서비스 URL 매핑 (환경변수 우선)
_SERVICE_URLS: dict[str, str] = {
    "selling": os.getenv("ONEERP_SELLING_URL", "http://selling-service/api/v1"),
    "buying": os.getenv("ONEERP_BUYING_URL", "http://buying-service/api/v1"),
    "expenses": os.getenv("ONEERP_EXPENSES_URL", "http://expenses-service/api/v1"),
    "hr": os.getenv("ONEERP_HR_URL", "http://hr-service/api/v1"),
    "manufacturing": os.getenv("ONEERP_MANUFACTURING_URL", "http://manufacturing-service/api/v1"),
}

# 서비스별 문서 엔드포인트
_DOC_ENDPOINTS: dict[str, str] = {
    "selling": "quotations",
    "buying": "purchase-orders",
    "expenses": "expense-claims",
    "hr": "leave-applications",
    "manufacturing": "work-orders",
}


class ApprovalDataBindingService:
    """결재 양식에 ERP 소스 데이터를 바인딩하는 서비스.

    approval_templates의 data_binding_fields를 기반으로
    소스 서비스 API를 호출하여 데이터를 매핑한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._template_repo = Repository("approval_templates", tenant_id=tenant_id)

    def bind_erp_data(
        self,
        template_id: str,
        source_service: str,
        source_doc_id: str,
    ) -> dict[str, Any]:
        """BR-APPR-012: 결재 양식에 ERP 데이터를 바인딩한다.

        Args:
            template_id: 결재 템플릿 ID
            source_service: 소스 서비스명 (예: "selling", "expenses")
            source_doc_id: 소스 문서 ID

        Returns:
            바인딩된 필드 딕셔너리

        Raises:
            OneERPError: 템플릿 없음 또는 지원하지 않는 서비스
        """
        # 템플릿 조회
        template = self._template_repo.find_by_id(template_id)
        if not template:
            msg = f"결재 템플릿 '{template_id}'를 찾을 수 없습니다"
            raise_not_found(msg)

        binding_fields: list[dict[str, Any]] = template.get("data_binding_fields", [])
        if not binding_fields:
            logger.debug("템플릿 '%s'에 바인딩 필드가 없습니다", template_id)
            return {}

        # 소스 서비스 URL 확인
        base_url = _SERVICE_URLS.get(source_service)
        if not base_url:
            msg = f"지원하지 않는 소스 서비스: '{source_service}'"
            raise_unprocessable("ERR-APR-004", msg)

        endpoint = _DOC_ENDPOINTS.get(source_service, source_service)
        url = f"{base_url}/{endpoint}/{source_doc_id}"

        # 소스 문서 조회
        try:
            response = httpx.get(
                url,
                headers={"X-Tenant-Id": self._tenant_id},
                timeout=5.0,
            )
            response.raise_for_status()
            source_doc: dict[str, Any] = response.json()
        except httpx.HTTPError as exc:
            msg = f"소스 서비스 호출 실패: {exc}"
            raise_unprocessable("ERR-APR-005", msg)

        # 바인딩 필드 매핑
        bound: dict[str, Any] = {}
        for field_def in binding_fields:
            target_field: str = field_def.get("target_field", "")
            source_field: str = field_def.get("source_field", "")
            if target_field and source_field:
                bound[target_field] = source_doc.get(source_field)

        logger.info(
            "데이터바인딩 완료: template=%s, source=%s/%s, 필드수=%d",
            template_id,
            source_service,
            source_doc_id,
            len(bound),
        )
        return bound
