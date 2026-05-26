"""포털 레이아웃 서비스 — 레이아웃 상속 해석, 위젯 배치 관리.

BR-PTL-001: 4단계 레이아웃 상속 (글로벌→부서→역할→개인).
BR-PTL-002: 위젯 최대 50개 제한.
BR-PTL-010: 레이아웃 잠금 시 수정 불가.
BR-PTL-012: 겹치는 위젯 자동 재배치.
BR-PTL-013: 모바일 자동 리플로우.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_MAX_WIDGETS = 50
_SCOPE_PRIORITY = ["global", "department", "role", "personal"]


class PortalLayoutService:
    """포털 레이아웃 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._layout_repo = Repository("portal_layouts", tenant_id=tenant_id)
        self._dashboard_repo = Repository("personal_dashboards", tenant_id=tenant_id)

    def resolve_user_layout(
        self,
        user_id: str,
        *,
        department: str = "",
        role: str = "",
    ) -> dict[str, Any]:
        """BR-PTL-001: 사용자의 최종 레이아웃을 4단계 상속으로 해석한다.

        상속 순서: 글로벌 → 부서 → 역할 → 개인.
        하위 범위가 상위 범위의 설정을 오버라이드한다.

        Returns:
            병합된 최종 레이아웃 dict.
        """
        # 1. 개인 대시보드 조회
        personal = self._dashboard_repo.find_many(
            {"user_id": user_id},
            limit=1,
        )

        # 2. 레이아웃 체인 수집 (글로벌 → 부서 → 역할)
        layouts: list[dict[str, Any]] = []

        # 글로벌 레이아웃
        global_layouts = self._layout_repo.find_many(
            {"scope": "global"},
            limit=1,
            sort=[("created_at", 1)],
        )
        if global_layouts:
            layouts.append(global_layouts[0])

        # 부서 레이아웃
        if department:
            dept_layouts = self._layout_repo.find_many(
                {"scope": "department", "scope_value": department},
                limit=1,
            )
            if dept_layouts:
                layouts.append(dept_layouts[0])

        # 역할 레이아웃
        if role:
            role_layouts = self._layout_repo.find_many(
                {"scope": "role", "scope_value": role},
                limit=1,
            )
            if role_layouts:
                layouts.append(role_layouts[0])

        # 3. 병합 — 하위 범위가 상위를 오버라이드
        merged = self._merge_layouts(layouts)

        # 4. 개인 대시보드 오버라이드
        if personal:
            merged = self._apply_personal_dashboard(merged, personal[0])

        # 5. 겹침 감지 및 자동 재배치
        merged["widgets"] = self._reposition_overlapping_widgets(
            merged.get("widgets", []),
            merged.get("grid_columns", 12),
        )

        logger.info(
            "레이아웃 해석 완료: user=%s, 병합 레이어=%d",
            user_id,
            len(layouts) + (1 if personal else 0),
        )
        return merged

    def _merge_layouts(self, layouts: list[dict[str, Any]]) -> dict[str, Any]:
        """레이아웃 체인을 병합한다 — 하위 범위 우선.

        BR-PTL-001: 위젯 배치는 하위 범위가 우선, 테마/그리드 설정도 오버라이드.
        """
        if not layouts:
            return {
                "layout_name": "기본 레이아웃",
                "grid_columns": 12,
                "grid_row_height": 80,
                "widgets": [],
                "theme": {},
                "mobile_config": {},
            }

        merged: dict[str, Any] = {}
        for layout in layouts:
            if not merged:
                merged = {**layout}
                continue

            # 스칼라 값은 하위 범위가 오버라이드
            for key in ("layout_name", "grid_columns", "grid_row_height"):
                if layout.get(key):
                    merged[key] = layout[key]

            # 테마 병합
            if layout.get("theme"):
                merged_theme = merged.get("theme", {})
                if isinstance(merged_theme, dict) and isinstance(layout["theme"], dict):
                    merged["theme"] = {**merged_theme, **layout["theme"]}
                else:
                    merged["theme"] = layout["theme"]

            # 모바일 설정 병합
            if layout.get("mobile_config"):
                merged_mobile = merged.get("mobile_config", {})
                if isinstance(merged_mobile, dict) and isinstance(
                    layout["mobile_config"],
                    dict,
                ):
                    merged["mobile_config"] = {**merged_mobile, **layout["mobile_config"]}
                else:
                    merged["mobile_config"] = layout["mobile_config"]

            # 위젯 병합 — 동일 widget_id는 하위가 오버라이드
            existing_widgets = {
                w.get("widget_id", ""): w for w in merged.get("widgets", []) if isinstance(w, dict)
            }
            for widget in layout.get("widgets", []):
                if isinstance(widget, dict):
                    existing_widgets[widget.get("widget_id", "")] = widget
            merged["widgets"] = list(existing_widgets.values())

        return merged

    def _apply_personal_dashboard(
        self,
        base: dict[str, Any],
        personal: dict[str, Any],
    ) -> dict[str, Any]:
        """개인 대시보드 설정을 기본 레이아웃 위에 적용한다."""
        result = {**base}
        if personal.get("widgets"):
            result["widgets"] = personal["widgets"]
        if personal.get("preferences"):
            result["preferences"] = personal["preferences"]
        return result

    def validate_widget_count(self, widgets: list[Any]) -> None:
        """BR-PTL-002: 위젯 최대 50개 제한 검증.

        Raises:
            OneERPError: 위젯 수가 50개를 초과할 때 (ERR-PTL-002).
        """
        if len(widgets) > _MAX_WIDGETS:
            raise_bad_request(
                f"위젯은 최대 {_MAX_WIDGETS}개까지 배치할 수 있습니다 "
                f"(현재: {len(widgets)}개) [ERR-PTL-002]"
            )

    def check_layout_lock(self, layout: dict[str, Any]) -> None:
        """BR-PTL-010: 잠금된 레이아웃은 수정할 수 없다.

        Raises:
            OneERPError: 레이아웃이 잠금 상태일 때 (ERR-PTL-010).
        """
        if layout.get("is_locked"):
            raise_bad_request("잠금된 레이아웃은 수정할 수 없습니다 [ERR-PTL-010]")

    def _reposition_overlapping_widgets(
        self,
        widgets: list[dict[str, Any]],
        grid_columns: int,
    ) -> list[dict[str, Any]]:
        """BR-PTL-012: 겹치는 위젯을 자동으로 재배치한다.

        간단한 그리디 알고리즘: 순서대로 배치하며 겹침 감지 시 아래로 이동.
        """
        if not widgets:
            return widgets

        occupied: set[tuple[int, int]] = set()
        result: list[dict[str, Any]] = []

        for widget in widgets:
            if not isinstance(widget, dict):
                continue
            x = widget.get("grid_x", 0)
            y = widget.get("grid_y", 0)
            w = widget.get("grid_w", 4)
            h = widget.get("grid_h", 4)

            # 겹침 감지
            while self._has_overlap(x, y, w, h, occupied, grid_columns):
                y += 1

            # 그리드 범위 내로 클램핑
            if x + w > grid_columns:
                x = max(0, grid_columns - w)

            # 점유 기록
            for dx in range(w):
                for dy in range(h):
                    occupied.add((x + dx, y + dy))

            result.append({**widget, "grid_x": x, "grid_y": y})

        return result

    @staticmethod
    def _has_overlap(
        x: int,
        y: int,
        w: int,
        h: int,
        occupied: set[tuple[int, int]],
        grid_columns: int,
    ) -> bool:
        """주어진 영역이 이미 점유된 셀과 겹치는지 확인한다."""
        for dx in range(w):
            for dy in range(h):
                if x + dx >= grid_columns:
                    return True
                if (x + dx, y + dy) in occupied:
                    return True
        return False

    def generate_mobile_layout(
        self,
        widgets: list[dict[str, Any]],
        mobile_config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """BR-PTL-013: 모바일 자동 리플로우.

        위젯을 지정된 컬럼 수에 맞게 재배치하고,
        숨김 목록에 있는 위젯은 제외한다.
        """
        columns = mobile_config.get("columns", 1)
        hide_widgets = set(mobile_config.get("hide_widgets", []))
        stack_order = mobile_config.get("stack_order", [])

        # 숨김 위젯 제거
        visible = [
            w for w in widgets if isinstance(w, dict) and w.get("widget_id", "") not in hide_widgets
        ]

        # 스택 순서 적용
        if stack_order:
            order_map = {wid: i for i, wid in enumerate(stack_order)}
            visible.sort(
                key=lambda w: order_map.get(w.get("widget_id", ""), len(stack_order)),
            )

        # 단일 컬럼 리플로우
        result: list[dict[str, Any]] = []
        current_y = 0
        for widget in visible:
            result.append(
                {
                    **widget,
                    "grid_x": 0,
                    "grid_y": current_y,
                    "grid_w": columns,
                }
            )
            current_y += widget.get("grid_h", 4)

        return result

    def get_layout_or_404(self, layout_id: str) -> dict[str, Any]:
        """레이아웃을 조회하고 없으면 404를 발생시킨다."""
        layout = self._layout_repo.find_by_id(layout_id)
        if layout is None:
            raise_not_found("포털 레이아웃을 찾을 수 없습니다 [ERR-PTL-001]")
        return cast("dict[str, Any]", layout)
