"""포털 레이아웃 서비스 단위 테스트.

SC-PTL-001~005: 레이아웃 상속 해석, 위젯 제한, 잠금, 겹침 재배치 테스트.
EX-PTL-001~005: 에러 케이스 테스트.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_core_app.portal.services.portal_layout_service import PortalLayoutService


class TestPortalLayoutService:
    """PortalLayoutService 테스트."""

    def test_글로벌_레이아웃_반환(self, mock_collection: MagicMock) -> None:
        """SC-PTL-001: 글로벌 레이아웃만 있을 때 해당 레이아웃을 반환한다."""
        global_layout = {
            "_id": "PTLL-2026-00001",
            "scope": "global",
            "layout_name": "기본 레이아웃",
            "grid_columns": 12,
            "grid_row_height": 80,
            "widgets": [
                {"widget_id": "w1", "grid_x": 0, "grid_y": 0, "grid_w": 4, "grid_h": 4},
            ],
            "theme": {"primary_color": "#1976D2"},
            "mobile_config": {"columns": 1},
            "tenant_id": "T1",
        }
        # 글로벌 레이아웃 조회
        cursor_global = MagicMock()
        cursor_global.skip.return_value.limit.return_value.sort.return_value = [global_layout]
        # 부서/역할/개인 레이아웃 없음
        cursor_empty = MagicMock()
        cursor_empty.skip.return_value.limit.return_value.sort.return_value = []
        cursor_empty.skip.return_value.limit.return_value = []

        mock_collection.find.side_effect = [
            cursor_empty,  # personal_dashboards
            cursor_global,  # global layouts
        ]

        svc = PortalLayoutService("T1")
        result = svc.resolve_user_layout("user1")

        assert result["layout_name"] == "기본 레이아웃"
        assert result["grid_columns"] == 12
        assert len(result["widgets"]) == 1

    def test_부서_레이아웃_오버라이드(self, mock_collection: MagicMock) -> None:
        """SC-PTL-002: 부서 레이아웃이 글로벌을 오버라이드한다."""
        global_layout = {
            "_id": "PTLL-2026-00001",
            "scope": "global",
            "layout_name": "기본",
            "grid_columns": 12,
            "grid_row_height": 80,
            "widgets": [{"widget_id": "w1", "grid_x": 0, "grid_y": 0, "grid_w": 4, "grid_h": 4}],
            "theme": {"primary_color": "#1976D2"},
            "mobile_config": {},
        }
        dept_layout = {
            "_id": "PTLL-2026-00002",
            "scope": "department",
            "layout_name": "개발팀",
            "grid_columns": 16,
            "grid_row_height": 80,
            "widgets": [{"widget_id": "w2", "grid_x": 0, "grid_y": 0, "grid_w": 6, "grid_h": 4}],
            "theme": {"primary_color": "#FF5722"},
            "mobile_config": {},
        }

        cursor_personal = MagicMock()
        cursor_personal.skip.return_value.limit.return_value = []
        cursor_global = MagicMock()
        cursor_global.skip.return_value.limit.return_value.sort.return_value = [global_layout]
        cursor_dept = MagicMock()
        cursor_dept.skip.return_value.limit.return_value = [dept_layout]

        mock_collection.find.side_effect = [
            cursor_personal,
            cursor_global,
            cursor_dept,
        ]

        svc = PortalLayoutService("T1")
        result = svc.resolve_user_layout("user1", department="dev")

        assert result["layout_name"] == "개발팀"
        assert result["grid_columns"] == 16
        # w1과 w2 모두 존재 (병합)
        widget_ids = [w.get("widget_id") for w in result["widgets"]]
        assert "w1" in widget_ids
        assert "w2" in widget_ids

    def test_개인_대시보드_최종_오버라이드(self, mock_collection: MagicMock) -> None:
        """SC-PTL-003: 개인 대시보드가 최종 오버라이드된다."""
        global_layout = {
            "_id": "PTLL-2026-00001",
            "scope": "global",
            "layout_name": "기본",
            "grid_columns": 12,
            "grid_row_height": 80,
            "widgets": [{"widget_id": "w1", "grid_x": 0, "grid_y": 0, "grid_w": 4, "grid_h": 4}],
            "theme": {},
            "mobile_config": {},
        }
        personal = {
            "_id": "PDASH-2026-00001",
            "user_id": "user1",
            "widgets": [{"widget_id": "wp1", "grid_x": 0, "grid_y": 0, "grid_w": 6, "grid_h": 3}],
            "preferences": {"dark_mode": True},
        }

        cursor_personal = MagicMock()
        cursor_personal.skip.return_value.limit.return_value = [personal]
        cursor_global = MagicMock()
        cursor_global.skip.return_value.limit.return_value.sort.return_value = [global_layout]

        mock_collection.find.side_effect = [cursor_personal, cursor_global]

        svc = PortalLayoutService("T1")
        result = svc.resolve_user_layout("user1")

        # 개인 위젯이 우선
        assert len(result["widgets"]) == 1
        assert result["widgets"][0]["widget_id"] == "wp1"
        assert result.get("preferences", {}).get("dark_mode") is True

    def test_빈_레이아웃_기본값(self, mock_collection: MagicMock) -> None:
        """SC-PTL-004: 레이아웃이 없을 때 기본값을 반환한다."""
        # 개인 대시보드 없음
        cursor_personal = MagicMock()
        cursor_personal.skip.return_value.limit.return_value = []
        # 글로벌 레이아웃 없음
        cursor_global = MagicMock()
        cursor_global.skip.return_value.limit.return_value.sort.return_value = []

        mock_collection.find.side_effect = [cursor_personal, cursor_global]

        svc = PortalLayoutService("T1")
        result = svc.resolve_user_layout("user1")

        assert result["layout_name"] == "기본 레이아웃"
        assert result["grid_columns"] == 12
        assert result["widgets"] == []

    def test_위젯_50개_초과_에러(self, mock_collection: MagicMock) -> None:
        """EX-PTL-001: 위젯 50개 초과 시 에러 (BR-PTL-002, ERR-PTL-002)."""
        svc = PortalLayoutService("T1")
        widgets = [{"widget_id": f"w{i}"} for i in range(51)]
        with pytest.raises(OneERPError) as exc_info:
            svc.validate_widget_count(widgets)
        assert "ERR-PTL-002" in (exc_info.value.detail or "")

    def test_위젯_50개_이하_정상(self, mock_collection: MagicMock) -> None:
        """SC-PTL-005: 위젯 50개 이하는 정상 통과 (BR-PTL-002)."""
        svc = PortalLayoutService("T1")
        widgets = [{"widget_id": f"w{i}"} for i in range(50)]
        # 에러 없이 통과
        svc.validate_widget_count(widgets)

    def test_잠금_레이아웃_수정_불가(self, mock_collection: MagicMock) -> None:
        """EX-PTL-002: 잠금된 레이아웃 수정 시 에러 (BR-PTL-010, ERR-PTL-010)."""
        svc = PortalLayoutService("T1")
        layout = {"_id": "PTLL-2026-00001", "is_locked": True}
        with pytest.raises(OneERPError) as exc_info:
            svc.check_layout_lock(layout)
        assert "ERR-PTL-010" in (exc_info.value.detail or "")

    def test_잠금_해제_레이아웃_수정_가능(self, mock_collection: MagicMock) -> None:
        """EX-PTL-003: 잠금 해제된 레이아웃은 수정 가능."""
        svc = PortalLayoutService("T1")
        layout = {"_id": "PTLL-2026-00001", "is_locked": False}
        # 에러 없이 통과
        svc.check_layout_lock(layout)

    def test_겹치는_위젯_자동_재배치(self, mock_collection: MagicMock) -> None:
        """EX-PTL-004: 겹치는 위젯이 자동으로 아래로 이동한다 (BR-PTL-012)."""
        svc = PortalLayoutService("T1")
        widgets = [
            {"widget_id": "w1", "grid_x": 0, "grid_y": 0, "grid_w": 4, "grid_h": 4},
            {"widget_id": "w2", "grid_x": 0, "grid_y": 0, "grid_w": 4, "grid_h": 4},
        ]
        result = svc._reposition_overlapping_widgets(widgets, 12)
        # 두 번째 위젯이 아래로 이동해야 함
        assert result[0]["grid_y"] == 0
        assert result[1]["grid_y"] > 0

    def test_모바일_리플로우(self, mock_collection: MagicMock) -> None:
        """EX-PTL-005: 모바일 리플로우가 위젯을 단일 컬럼으로 쌓는다 (BR-PTL-013)."""
        svc = PortalLayoutService("T1")
        widgets = [
            {"widget_id": "w1", "grid_x": 0, "grid_y": 0, "grid_w": 6, "grid_h": 4},
            {"widget_id": "w2", "grid_x": 6, "grid_y": 0, "grid_w": 6, "grid_h": 4},
            {"widget_id": "w3", "grid_x": 0, "grid_y": 4, "grid_w": 12, "grid_h": 4},
        ]
        mobile_config = {"columns": 1, "hide_widgets": ["w3"], "stack_order": []}

        result = svc.generate_mobile_layout(widgets, mobile_config)

        # w3은 숨김 처리
        assert len(result) == 2
        # 모두 단일 컬럼
        for w in result:
            assert w["grid_w"] == 1
            assert w["grid_x"] == 0

    def test_레이아웃_404(self, mock_collection: MagicMock) -> None:
        """EX-PTL-005: 존재하지 않는 레이아웃 조회 시 404."""
        mock_collection.find_one.return_value = None
        svc = PortalLayoutService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.get_layout_or_404("NONEXISTENT")
        assert exc_info.value.status_code == 404
        assert "ERR-PTL-001" in (exc_info.value.detail or "")
