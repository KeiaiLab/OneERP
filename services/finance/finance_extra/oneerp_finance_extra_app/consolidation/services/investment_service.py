"""투자 관계 서비스 — 연결 방법 자동 판단, 영업권 산출, 유효 지분율 계산.

L2 비즈니스 룰 매핑:
- BR-CSL-001: 의결권 비율에 따�� 연결 방법 자동 결정
- BR-CSL-005: 영업권 산출 (부분/전부영업권법)
- ERR-CSL-025: 순환 투자 관계 감지
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, cast

from oneerp_core.errors import OneERPError, raise_conflict, raise_not_found
from oneerp_core.repository import Repository

from oneerp_finance_extra_app.consolidation.models.consolidation_entity import ConsolidationMethod

logger = logging.getLogger(__name__)

# 의결권 비율 경계값
_CONTROL_THRESHOLD = Decimal(50)
_SIGNIFICANT_INFLUENCE_LOW = Decimal(20)


def _raise_unprocessable(error_code: str, detail: str) -> None:
    """422 Unprocessable Entity 에러를 발생시킨다."""
    raise OneERPError(status_code=422, error=error_code, detail=detail)


class InvestmentService:
    """투자 관계 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._entity_repo = Repository("consolidation_entities", tenant_id=tenant_id)
        self._relation_repo = Repository("investment_relations", tenant_id=tenant_id)

    def determine_consolidation_method(
        self,
        voting_rights_percentage: Decimal,
        *,
        is_joint_control: bool = False,
    ) -> dict[str, Any]:
        """BR-CSL-001: 의결권 비율에 따른 연결 방법 자동 판단.

        Args:
            voting_rights_percentage: 의결권 비율
            is_joint_control: 공동지배력 여부 (향후 확장용)

        Returns:
            consolidation_method, is_control, is_significant_influence 딕셔너리
        """
        _ = is_joint_control  # 향��� K-IFRS 제1111호 공동기업 분기에 사용
        if voting_rights_percentage > _CONTROL_THRESHOLD:
            return {
                "consolidation_method": ConsolidationMethod.FULL,
                "is_control": True,
                "is_significant_influence": False,
            }

        if voting_rights_percentage >= _SIGNIFICANT_INFLUENCE_LOW:
            return {
                "consolidation_method": ConsolidationMethod.EQUITY,
                "is_control": False,
                "is_significant_influence": True,
            }

        # 의결권 20% 미만
        return {
            "consolidation_method": ConsolidationMethod.NONE,
            "is_control": False,
            "is_significant_influence": False,
        }

    def calculate_goodwill(
        self,
        acquisition_cost: Decimal,
        fair_value_net_assets: Decimal,
        ownership_percentage: Decimal,
        nci_fair_value: Decimal | None = None,
    ) -> dict[str, Decimal]:
        """BR-CSL-005: 영업권 산출.

        부분영업권법(기본)과 전부영업권법을 모두 계산한다.

        Returns:
            partial_goodwill, full_goodwill 딕셔너리
        """
        # 부분영업권법: 취득대가 - (순자산��정가치 x 지분율 / 100)
        partial = acquisition_cost - (fair_value_net_assets * ownership_percentage / Decimal(100))

        # 전부영업권법  # noqa: ERA001
        nci = nci_fair_value if nci_fair_value is not None else Decimal(0)
        full = (acquisition_cost + nci) - fair_value_net_assets

        return {
            "partial_goodwill": partial,
            "full_goodwill": full,
        }

    def check_circular_investment(
        self,
        investor_entity_id: str,
        investee_entity_id: str,
    ) -> bool:
        """ERR-CSL-025: 순환 투자 관계 검출.

        investee가 이미 investor에 투자하고 있는지 확인한다.

        Returns:
            순환 관계가 존재하�� True
        """
        reverse = self._relation_repo.find_many(
            {
                "investor_entity_id": investee_entity_id,
                "investee_entity_id": investor_entity_id,
                "status": "active",
            },
            limit=1,
        )
        return len(reverse) > 0

    def create_investment_relation(self, data: dict[str, Any]) -> dict[str, Any]:
        """투자 관계 생성 — 연결 방법 자동 판단 및 영업권 산출 포함.

        Args:
            data: 투자 관계 생성 요청 데이터

        Returns:
            생성된 투자 관계 문서
        """
        investor_id = data["investor_entity_id"]
        investee_id = data["investee_entity_id"]

        # 순환 투자 검증
        if self.check_circular_investment(investor_id, investee_id):
            _raise_unprocessable(
                "ERR-CSL-025",
                "순환 투자 관계가 감지되었습니다. 상호출자는 현재 지원되지 않습니다.",
            )

        # 중복 투자 관계 검증
        existing = self._relation_repo.find_many(
            {
                "investor_entity_id": investor_id,
                "investee_entity_id": investee_id,
            },
            limit=1,
        )
        if existing:
            raise_conflict("동일한 투자 관계가 이미 존재합니다")

        # 연결 방법 자동 판단
        voting = Decimal(str(data.get("voting_rights_percentage", 0)))
        is_joint = data.get("is_joint_control", False)
        method_result = self.determine_consolidation_method(voting, is_joint_control=is_joint)

        data["consolidation_method"] = method_result["consolidation_method"]
        data["is_control"] = method_result["is_control"]
        data["is_significant_influence"] = method_result["is_significant_influence"]

        # 영업권 산출
        fair_value = data.get("fair_value_net_assets")
        acq_cost = Decimal(str(data.get("acquisition_cost", 0)))
        ownership = Decimal(str(data.get("ownership_percentage", 0)))

        if fair_value is not None:
            nci_fv = data.get("nci_fair_value")
            goodwill_result = self.calculate_goodwill(
                acq_cost,
                Decimal(str(fair_value)),
                ownership,
                Decimal(str(nci_fv)) if nci_fv is not None else None,
            )
            # 부분영업권법 기본 적용
            data["goodwill"] = goodwill_result["partial_goodwill"]

        return data

    def get_ownership_tree(self) -> list[dict[str, Any]]:
        """지분 구조 트리를 조회한다.

        Returns:
            법인별 지분 관계 트리 목록
        """
        entities = self._entity_repo.find_many({}, limit=1000)
        relations = self._relation_repo.find_many({"status": "active"}, limit=1000)

        # 지배기업 찾기
        parent = None
        for entity in entities:
            if entity.get("is_parent"):
                parent = entity
                break

        if parent is None:
            raise_not_found("지배기업을 찾을 수 없습니다")
        parent = cast("dict[str, Any]", parent)

        # 트리 구성
        tree: list[dict[str, Any]] = []
        parent_node: dict[str, Any] = {
            "entity_id": parent["_id"],
            "entity_code": parent.get("entity_code", ""),
            "entity_name": parent.get("entity_name", ""),
            "entity_type": parent.get("entity_type", "parent"),
            "children": [],
        }

        for relation in relations:
            if relation.get("investor_entity_id") == parent["_id"]:
                investee = next(
                    (e for e in entities if e.get("_id") == relation.get("investee_entity_id")),
                    None,
                )
                if investee:
                    child = {
                        "entity_id": investee["_id"],
                        "entity_code": investee.get("entity_code", ""),
                        "entity_name": investee.get("entity_name", ""),
                        "ownership_percentage": relation.get("ownership_percentage", 0),
                        "consolidation_method": relation.get("consolidation_method", ""),
                    }
                    parent_node["children"].append(child)

        tree.append(parent_node)
        return tree
