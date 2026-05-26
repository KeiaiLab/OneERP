"""위젯 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_core_app.portal.services.widget_service import WidgetService


class TestWidgetService:
    """WidgetService 테스트."""

    def test_모듈_의존성_필터링(self, mock_collection: MagicMock) -> None:
        """BR-PTL-007: 비활성 모듈의 위젯이 제외된다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "WGT-1",
                "is_active": True,
                "required_module": "accounting",
                "required_permission": "",
            },
            {
                "_id": "WGT-2",
                "is_active": True,
                "required_module": "hr",
                "required_permission": "",
            },
        ]
        mock_collection.find.return_value = cursor

        svc = WidgetService("T1")
        result = svc.get_available_widgets(
            active_modules=["accounting"],
            user_permissions=["*:*"],
        )

        assert len(result) == 1
        assert result[0]["_id"] == "WGT-1"

    def test_권한_필터링(self, mock_collection: MagicMock) -> None:
        """BR-PTL-008: 권한 없는 위젯이 제외된다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "WGT-1",
                "is_active": True,
                "required_module": "",
                "required_permission": "admin:read",
            },
            {
                "_id": "WGT-2",
                "is_active": True,
                "required_module": "",
                "required_permission": "user:read",
            },
        ]
        mock_collection.find.return_value = cursor

        svc = WidgetService("T1")
        result = svc.get_available_widgets(
            user_permissions=["user:read"],
        )

        assert len(result) == 1
        assert result[0]["_id"] == "WGT-2"

    def test_와일드카드_권한(self, mock_collection: MagicMock) -> None:
        """와일드카드 권한(*:*)이 있으면 모든 위젯을 반환한다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "WGT-1",
                "is_active": True,
                "required_module": "",
                "required_permission": "admin:read",
            },
            {
                "_id": "WGT-2",
                "is_active": True,
                "required_module": "",
                "required_permission": "user:read",
            },
        ]
        mock_collection.find.return_value = cursor

        svc = WidgetService("T1")
        result = svc.get_available_widgets(user_permissions=["*:*"])

        assert len(result) == 2

    def test_KPI_데이터_스코프_admin(self, mock_collection: MagicMock) -> None:
        """BR-PTL-014: admin 역할은 전사 범위."""
        mock_collection.find_one.return_value = {
            "_id": "WGT-1",
            "widget_type": "kpi",
            "data_source": {"endpoint": "/api/kpi"},
            "refresh_interval": 300,
            "tenant_id": "T1",
        }

        svc = WidgetService("T1")
        result = svc.get_widget_data("WGT-1", user_role="admin")

        assert result["scope"] == "company"

    def test_KPI_데이터_스코프_일반직원(self, mock_collection: MagicMock) -> None:
        """BR-PTL-014: 일반 직원은 개인 범위."""
        mock_collection.find_one.return_value = {
            "_id": "WGT-1",
            "widget_type": "kpi",
            "data_source": {},
            "refresh_interval": 300,
            "tenant_id": "T1",
        }

        svc = WidgetService("T1")
        result = svc.get_widget_data("WGT-1", user_role="employee")

        assert result["scope"] == "personal"

    def test_존재하지_않는_위젯_404(self, mock_collection: MagicMock) -> None:
        """존재하지 않는 위젯 조회 시 404 (ERR-PTL-012)."""
        mock_collection.find_one.return_value = None

        svc = WidgetService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.get_widget_data("NONEXISTENT")
        assert exc_info.value.status_code == 404
        assert "ERR-PTL-012" in (exc_info.value.detail or "")

    def test_모듈_의존성_검증(self, mock_collection: MagicMock) -> None:
        """BR-PTL-007: 모듈 의존성 검증 메서드."""
        svc = WidgetService("T1")

        widget_with_module = {"required_module": "accounting"}
        assert svc.validate_module_dependency(widget_with_module, ["accounting"]) is True
        assert svc.validate_module_dependency(widget_with_module, ["hr"]) is False

        widget_no_module = {"required_module": ""}
        assert svc.validate_module_dependency(widget_no_module, []) is True
