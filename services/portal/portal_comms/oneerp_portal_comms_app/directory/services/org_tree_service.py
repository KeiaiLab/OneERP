"""조직 트리 서비스 — 조직 구조 구성/조회/스냅샷 비즈니스 로직.

BR-DIR-003: 조직 단위는 반드시 상위 조직에 소속되어야 한다.
BR-DIR-005: 조직 단위는 계층 구조를 가질 수 있다.
BR-DIR-011: 조직도 스냅샷은 특정 시점의 조직 구조를 보존한다.
BR-DIR-012: 스냅샷 생성 시 모든 활성 조직 단위와 인명부를 포함한다.
BR-DIR-013: 순환 참조(부모→자식→부모)를 방지한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class OrgTreeService:
    """조직 트리 비즈니스 로직.

    조직 단위의 계층 구조를 관리하고 조직도 스냅샷을 생성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._org_repo = Repository("organizations", tenant_id=tenant_id)
        self._unit_repo = Repository("org_units", tenant_id=tenant_id)
        self._dir_repo = Repository("employee_directories", tenant_id=tenant_id)
        self._snap_repo = Repository("org_chart_snapshots", tenant_id=tenant_id)

    def get_org_tree(self, org_id: str) -> dict[str, Any]:
        """조직의 전체 트리 구조를 조회한다.

        BR-DIR-005: 계층 구조를 재귀적으로 구성하여 반환한다.

        Args:
            org_id: 조직 ID

        Returns:
            트리 구조 (root + children)
        """
        org = self._org_repo.find_by_id(org_id)
        if not org:
            msg = f"ERR-DIR-001: 조직 '{org_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        units = self._unit_repo.find_many(
            {"org_id": org_id, "status": "active"},
            limit=10000,
        )

        tree = self._build_tree(units)

        logger.info("조직 트리 조회: %s (%d개 단위)", org_id, len(units))
        return {
            "org_id": org_id,
            "org_name": org.get("org_name", ""),
            "units": tree,
            "total_units": len(units),
        }

    def _build_tree(
        self,
        units: list[dict[str, Any]],
        parent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """BR-DIR-005: 조직 단위 목록을 계층형 트리로 구성한다."""
        children = []
        for unit in units:
            if unit.get("parent_unit_id") == parent_id:
                node: dict[str, Any] = {
                    "unit_id": unit.get("_id", ""),
                    "unit_code": unit.get("unit_code", ""),
                    "unit_name": unit.get("unit_name", ""),
                    "unit_type": unit.get("unit_type", ""),
                    "head_employee_id": unit.get("head_employee_id"),
                    "sort_order": unit.get("sort_order", 0),
                    "children": self._build_tree(units, unit.get("_id")),
                }
                children.append(node)
        children.sort(key=lambda x: x.get("sort_order", 0))
        return children

    def validate_no_circular_reference(
        self,
        unit_id: str,
        new_parent_id: str | None,
    ) -> bool:
        """BR-DIR-013: 순환 참조를 방지한다.

        Args:
            unit_id: 이동할 조직 단위 ID
            new_parent_id: 새로운 상위 조직 단위 ID

        Returns:
            True면 순환 참조 없음 (안전)

        Raises:
            ValueError: 순환 참조 감지 시
        """
        if new_parent_id is None:
            return True

        if unit_id == new_parent_id:
            msg = "ERR-DIR-013: 자기 자신을 상위 조직으로 설정할 수 없습니다"
            raise ValueError(msg)

        # 상위 체인을 따라가며 순환 여부 확인
        visited: set[str] = {unit_id}
        current_id: str | None = new_parent_id

        while current_id is not None:
            if current_id in visited:
                msg = "ERR-DIR-013: 순환 참조가 감지되었습니다"
                raise ValueError(msg)
            visited.add(current_id)
            parent_unit = self._unit_repo.find_by_id(current_id)
            if not parent_unit:
                break
            current_id = parent_unit.get("parent_unit_id")

        return True

    def move_unit(
        self,
        unit_id: str,
        new_parent_id: str | None,
    ) -> dict[str, Any]:
        """조직 단위를 다른 상위 단위로 이동한다.

        BR-DIR-005: 계층 구조를 변경한다.
        BR-DIR-013: 순환 참조를 방지한다.

        Args:
            unit_id: 이동할 조직 단위 ID
            new_parent_id: 새로운 상위 조직 단위 ID

        Returns:
            이동 결과
        """
        unit = self._unit_repo.find_by_id(unit_id)
        if not unit:
            msg = f"ERR-DIR-005: 조직 단위 '{unit_id}'를 찾을 수 없습니다"
            raise ValueError(msg)

        old_parent = unit.get("parent_unit_id")
        self.validate_no_circular_reference(unit_id, new_parent_id)

        self._unit_repo.update_by_id(unit_id, {"parent_unit_id": new_parent_id})

        logger.info(
            "조직 단위 이동: %s (%s → %s)",
            unit_id,
            old_parent,
            new_parent_id,
        )
        return {
            "unit_id": unit_id,
            "old_parent_id": old_parent,
            "new_parent_id": new_parent_id,
        }

    def create_snapshot(
        self,
        org_id: str,
        snapshot_date: date | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """조직도 스냅샷을 생성한다.

        BR-DIR-011: 특정 시점의 조직 구조를 보존한다.
        BR-DIR-012: 모든 활성 조직 단위와 인명부를 포함한다.

        Args:
            org_id: 조직 ID
            snapshot_date: 스냅샷 기준일 (기본: 오늘)
            description: 설명

        Returns:
            생성된 스냅샷 정보
        """
        org = self._org_repo.find_by_id(org_id)
        if not org:
            msg = f"ERR-DIR-001: 조직 '{org_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if snapshot_date is None:
            snapshot_date = datetime.now(UTC).date()

        # 활성 조직 단위 수집
        units = self._unit_repo.find_many(
            {"org_id": org_id, "status": "active"},
            limit=10000,
        )

        # 활성 인명부 엔트리 수집
        employees = self._dir_repo.find_many(
            {"org_id": org_id, "status": "active"},
            limit=100000,
        )

        tree_data = self._build_tree(units)

        snap_id = generate_name("SNAP", tenant_id=self._tenant_id)
        snap_doc = {
            "_id": snap_id,
            "org_id": org_id,
            "snapshot_date": snapshot_date.isoformat(),
            "description": description,
            "tree_data": tree_data,
            "total_units": len(units),
            "total_employees": len(employees),
            "tenant_id": self._tenant_id,
        }
        self._snap_repo.insert(snap_doc)

        logger.info(
            "조직도 스냅샷 생성: %s (조직: %s, 단위: %d, 인원: %d)",
            snap_id,
            org_id,
            len(units),
            len(employees),
        )
        return {
            "snapshot_id": snap_id,
            "org_id": org_id,
            "snapshot_date": snapshot_date.isoformat(),
            "total_units": len(units),
            "total_employees": len(employees),
        }
