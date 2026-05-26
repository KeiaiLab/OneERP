"""제품 수명주기 서비스 — 상태 전이 검증 및 BOM 연동 비즈니스 로직."""

from __future__ import annotations

import logging
from typing import Any, cast

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.repository import Repository

from oneerp_plm_app.models.product import LIFECYCLE_TRANSITIONS, LifecycleStatus

logger = logging.getLogger(__name__)


class ProductLifecycleService:
    """제품 수명주기 비즈니스 로직.

    수명주기 상태 전이 검증 및 조건 확인을 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._product_repo = Repository("products", tenant_id=tenant_id)
        self._bom_repo = Repository("bom_versions", tenant_id=tenant_id)

    def transition_lifecycle(
        self,
        product_id: str,
        new_status: str,
        reason: str = "",
        user_id: str = "",
    ) -> dict[str, Any]:
        """제품 수명주기 상태를 전이한다.

        Args:
            product_id: 제품 ID
            new_status: 전이할 새 상태
            reason: 전이 사유
            user_id: 요청자 ID

        Returns:
            전이 결과
        """
        product = self._product_repo.find_by_id(product_id)
        if not product:
            raise_not_found(f"제품을 찾을 수 없습니다: {product_id}")
        product = cast("dict[str, Any]", product)

        current_status = LifecycleStatus(product["lifecycle_status"])
        try:
            target_status = LifecycleStatus(new_status)
        except ValueError:
            raise_bad_request(f"유효하지 않은 상태입니다: {new_status}")

        # 전이 규칙 검증
        allowed = LIFECYCLE_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            allowed_names = [s.value for s in allowed]
            raise_bad_request(
                f"허용되지 않는 상태 전이입니다: {current_status.value} → {new_status}. "
                f"허용 전이: {allowed_names}"
            )

        # 전이 조건 검증
        self._validate_transition_conditions(product, current_status, target_status)

        # 상태 갱신
        update_data: dict[str, Any] = {
            "lifecycle_status": target_status.value,
            "updated_by": user_id,
        }
        self._product_repo.update_by_id(product_id, update_data)

        logger.info(
            "제품 수명주기 전이: product=%s, %s → %s, 사유=%s",
            product_id,
            current_status.value,
            target_status.value,
            reason,
        )

        return {
            "product_id": product_id,
            "previous_status": current_status.value,
            "new_status": target_status.value,
            "reason": reason,
        }

    def _validate_transition_conditions(
        self,
        product: dict[str, Any],
        current: LifecycleStatus,
        target: LifecycleStatus,
    ) -> None:
        """전이 조건을 검증한다."""
        product_id = product.get("_id", "")

        # design → prototype: E-BOM 릴리즈 필요
        if current == LifecycleStatus.DESIGN and target == LifecycleStatus.PROTOTYPE:
            ebom_id = product.get("active_ebom_id")
            if not ebom_id:
                raise_bad_request("prototype 전이 조건 미충족: 릴리즈된 E-BOM이 없습니다")
            ebom = self._bom_repo.find_by_id(str(ebom_id))
            if not ebom or ebom.get("status") != "released":
                raise_bad_request("prototype 전이 조건 미충족: E-BOM이 릴리즈 상태가 아닙니다")

        # prototype → pre_production: M-BOM 릴리즈 필요
        if current == LifecycleStatus.PROTOTYPE and target == LifecycleStatus.PRE_PRODUCTION:
            mbom_id = product.get("active_mbom_id")
            if not mbom_id:
                raise_bad_request("pre_production 전이 조건 미충족: 릴리즈된 M-BOM이 없습니다")

        logger.info("제품 전이 조건 검증 완료: product=%s, %s → %s", product_id, current, target)
