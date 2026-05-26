"""BOM 서비스 — BOM 버전 관리, 릴리즈, 비교, 전환 비즈니스 로직."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_plm_app.models.bom_version import BOMItem, BOMType, BOMVersion, BOMVersionStatus

logger = logging.getLogger(__name__)


class BOMService:
    """BOM 버전 관리 비즈니스 로직.

    BOM 릴리즈, 원가 산출, 트리 전개, 비교(Diff), E-BOM→M-BOM 전환을 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._bom_repo = Repository("bom_versions", tenant_id=tenant_id)
        self._product_repo = Repository("products", tenant_id=tenant_id)

    def release_bom(
        self,
        bom_version_id: str,
        approved_by: str,
    ) -> dict[str, Any]:
        """BOM을 릴리즈한다.

        Args:
            bom_version_id: BOM 버전 ID
            approved_by: 승인자 ID

        Returns:
            릴리즈 결과
        """
        bom = self._bom_repo.find_by_id(bom_version_id)
        if not bom:
            raise_not_found(f"BOM 버전을 찾을 수 없습니다: {bom_version_id}")

        status = bom.get("status", "")
        if status not in ("draft", "in_review"):
            raise_bad_request(
                f"draft 또는 in_review 상태에서만 릴리즈 가능합니다. 현재 상태: {status}"
            )

        items = bom.get("items", [])
        if not items:
            raise_bad_request("BOM 릴리즈 조건 미충족: 구성 품목이 비어있습니다")

        # 총 원가 산출
        total_cost = Decimal(0)
        for item in items:
            qty = Decimal(str(item.get("quantity", 0)))
            unit_cost = Decimal(str(item.get("unit_cost", 0)))
            total_cost += qty * unit_cost

        now = datetime.now(tz=UTC)
        update_data: dict[str, Any] = {
            "status": BOMVersionStatus.RELEASED.value,
            "total_cost": float(total_cost),
            "released_by": approved_by,
            "released_at": now.isoformat(),
        }
        self._bom_repo.update_by_id(bom_version_id, update_data)

        # 제품의 active_ebom_id 또는 active_mbom_id 갱신
        product_id = bom.get("product_id", "")
        bom_type = bom.get("bom_type", "")
        if product_id:
            field = "active_ebom_id" if bom_type == BOMType.EBOM.value else "active_mbom_id"
            self._product_repo.update_by_id(product_id, {field: bom_version_id})

        logger.info("BOM 릴리즈 완료: bom=%s, total_cost=%s", bom_version_id, total_cost)

        return {
            "bom_version_id": bom_version_id,
            "status": "released",
            "total_cost": float(total_cost),
            "released_by": approved_by,
        }

    def compare_bom(
        self,
        bom_id_1: str,
        bom_id_2: str,
    ) -> dict[str, Any]:
        """두 BOM 버전을 비교(Diff)한다.

        Args:
            bom_id_1: 비교 기준 BOM 버전 ID
            bom_id_2: 비교 대상 BOM 버전 ID

        Returns:
            비교 결과 (added, removed, modified, unchanged)
        """
        if bom_id_1 == bom_id_2:
            raise_bad_request("동일한 BOM을 비교할 수 없습니다")

        bom1 = self._bom_repo.find_by_id(bom_id_1)
        if not bom1:
            raise_not_found(f"BOM 버전을 찾을 수 없습니다: {bom_id_1}")

        bom2 = self._bom_repo.find_by_id(bom_id_2)
        if not bom2:
            raise_not_found(f"BOM 버전을 찾을 수 없습니다: {bom_id_2}")

        # 아이템 맵 생성 (item_code 기준)
        items1 = {item.get("item_code", ""): item for item in bom1.get("items", [])}
        items2 = {item.get("item_code", ""): item for item in bom2.get("items", [])}

        added: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []
        modified: list[dict[str, Any]] = []
        unchanged: list[dict[str, Any]] = []

        all_codes = set(items1.keys()) | set(items2.keys())
        for code in sorted(all_codes):
            in1 = code in items1
            in2 = code in items2
            if in1 and not in2:
                removed.append({"item_code": code, "detail": items1[code]})
            elif not in1 and in2:
                added.append({"item_code": code, "detail": items2[code]})
            elif in1 and in2:
                i1 = items1[code]
                i2 = items2[code]
                if i1.get("quantity") != i2.get("quantity") or i1.get("unit_cost") != i2.get(
                    "unit_cost"
                ):
                    modified.append(
                        {
                            "item_code": code,
                            "before": i1,
                            "after": i2,
                        }
                    )
                else:
                    unchanged.append({"item_code": code, "detail": i1})

        return {
            "bom_id_1": bom_id_1,
            "bom_id_2": bom_id_2,
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged": unchanged,
        }

    def convert_ebom_to_mbom(
        self,
        ebom_id: str,
        notes: str = "",
        user_id: str = "",
    ) -> dict[str, Any]:
        """E-BOM을 M-BOM으로 전환한다.

        Args:
            ebom_id: E-BOM 버전 ID
            notes: 전환 메모
            user_id: 요청자 ID

        Returns:
            전환 결과 (새 M-BOM ID 포함)
        """
        ebom = self._bom_repo.find_by_id(ebom_id)
        if not ebom:
            raise_not_found(f"BOM 버전을 찾을 수 없습니다: {ebom_id}")

        if ebom.get("bom_type") != BOMType.EBOM.value:
            raise_bad_request("E-BOM만 M-BOM으로 전환할 수 있습니다")

        if ebom.get("status") != BOMVersionStatus.RELEASED.value:
            raise_bad_request("릴리즈된 E-BOM만 M-BOM으로 전환할 수 있습니다")

        # 새 M-BOM 생성
        mbom_id = generate_name("BV", tenant_id=self._tenant_id)
        mbom_items = []
        for idx, item in enumerate(ebom.get("items", []), start=1):
            mbom_items.append(
                {
                    "line_no": idx,
                    "item_code": item.get("item_code", ""),
                    "item_name": item.get("item_name", ""),
                    "quantity": item.get("quantity", 0),
                    "uom": item.get("uom", "EA"),
                    "unit_cost": item.get("unit_cost", 0),
                    "reference_designator": item.get("reference_designator"),
                    "is_phantom": item.get("is_phantom", False),
                    "child_bom_id": item.get("child_bom_id"),
                    "notes": "",
                }
            )

        mbom = BOMVersion(
            _id=mbom_id,
            tenant_id=self._tenant_id,
            product_id=ebom.get("product_id", ""),
            bom_type=BOMType.MBOM,
            version_major=1,
            version_minor=0,
            version_label="1.0",
            status=BOMVersionStatus.DRAFT,
            base_quantity=ebom.get("base_quantity", 1.0),
            items=[BOMItem(**i) for i in mbom_items],
            source_ebom_id=ebom_id,
            notes=notes,
            created_by=user_id,
            updated_by=user_id,
        )

        self._bom_repo.insert(mbom)
        logger.info("E-BOM → M-BOM 전환 완료: ebom=%s → mbom=%s", ebom_id, mbom_id)

        return {
            "mbom_id": mbom_id,
            "source_ebom_id": ebom_id,
            "product_id": ebom.get("product_id", ""),
            "status": "draft",
        }

    def get_where_used(self, item_code: str) -> list[dict[str, Any]]:
        """Where-Used 분석 — 특정 부품이 사용된 BOM/제품을 역추적한다.

        Args:
            item_code: 부품 코드

        Returns:
            사용 BOM 목록
        """
        # 모든 BOM에서 해당 item_code를 포함하는 BOM 검색
        all_boms = self._bom_repo.find({"items.item_code": item_code})
        results: list[dict[str, Any]] = []
        for bom in all_boms:
            # 해당 아이템의 수량 찾기
            qty = 0.0
            for item in bom.get("items", []):
                if item.get("item_code") == item_code:
                    qty = float(item.get("quantity", 0))
                    break
            results.append(
                {
                    "bom_version_id": bom.get("_id", ""),
                    "product_id": bom.get("product_id", ""),
                    "bom_type": bom.get("bom_type", ""),
                    "version_label": bom.get("version_label", ""),
                    "quantity": qty,
                    "status": bom.get("status", ""),
                }
            )
        return results
