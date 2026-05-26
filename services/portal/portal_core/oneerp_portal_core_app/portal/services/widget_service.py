"""위젯 서비스 — 위젯 권한 필터링, 모듈 의존성 검증.

BR-PTL-007: 위젯 모듈 의존성 검증.
BR-PTL-008: 위젯 권한 필터링.
BR-PTL-014: KPI 데이터 범위를 역할별로 제한.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class WidgetService:
    """위젯 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._widget_repo = Repository("widgets", tenant_id=tenant_id)
        self._config_repo = Repository("widget_configs", tenant_id=tenant_id)

    def get_available_widgets(
        self,
        *,
        user_permissions: list[str] | None = None,
        active_modules: list[str] | None = None,
        user_role: str = "",
    ) -> list[dict[str, Any]]:
        """사용자에게 사용 가능한 위젯 목록을 반환한다.

        BR-PTL-007: 비활성 모듈의 위젯은 제외.
        BR-PTL-008: 권한 없는 위젯은 제외.
        """
        all_widgets = self._widget_repo.find_many({"is_active": True}, limit=200)

        result: list[dict[str, Any]] = []
        for widget in all_widgets:
            # BR-PTL-007: 모듈 의존성 확인
            required_module = widget.get("required_module", "")
            if (
                required_module
                and active_modules is not None
                and required_module not in active_modules
            ):
                continue

            # BR-PTL-008: 권한 확인
            required_perm = widget.get("required_permission", "")
            if (
                required_perm
                and user_permissions is not None
                and required_perm not in user_permissions
                and "*:*" not in user_permissions
            ):
                continue

            result.append(widget)

        logger.info(
            "사용 가능 위젯: %d/%d (역할: %s)",
            len(result),
            len(all_widgets),
            user_role,
        )
        return result

    def get_widget_data(
        self,
        widget_id: str,
        *,
        user_role: str = "",
    ) -> dict[str, Any]:
        """위젯 데이터를 조회한다.

        BR-PTL-014: KPI 위젯의 데이터 범위를 역할별로 제한한다.
        """
        widget = self._widget_repo.find_by_id(widget_id)
        if widget is None:
            raise_not_found("위젯을 찾을 수 없습니다 [ERR-PTL-012]")

        data_source = widget.get("data_source", {})
        widget_type = widget.get("widget_type", "")

        # BR-PTL-014: KPI 위젯 데이터 스코프 제한
        scope = self._resolve_data_scope(widget_type, user_role)

        return {
            "widget_id": widget_id,
            "widget_type": widget_type,
            "data_source": data_source,
            "scope": scope,
            "refresh_interval": widget.get("refresh_interval", 300),
        }

    def validate_module_dependency(
        self,
        widget: dict[str, Any],
        active_modules: list[str],
    ) -> bool:
        """BR-PTL-007: 위젯의 모듈 의존성을 검증한다.

        Returns:
            True이면 의존 모듈이 활성 상태, False이면 비활성.
        """
        required_module = widget.get("required_module", "")
        if not required_module:
            return True
        return required_module in active_modules

    @staticmethod
    def _resolve_data_scope(widget_type: str, user_role: str) -> str:
        """BR-PTL-014: 역할에 따라 KPI 데이터 범위를 결정한다.

        - admin/manager: 전사 범위
        - team_lead: 팀 범위
        - 기타: 개인 범위
        """
        if widget_type != "kpi":
            return "full"

        if user_role in ("admin", "manager", "super_admin"):
            return "company"
        if user_role in ("team_lead", "department_head"):
            return "team"
        return "personal"
