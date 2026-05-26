"""아이템 변형 서비스 — 속성 기반 변형 자동 생성 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-STK-009: 품목 변형 코드 생성 (variant_code = template-attr1-attr2...)
"""

from __future__ import annotations

import itertools
import logging
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ItemVariantService:
    """아이템 변형(Variant) 자동 생성 비즈니스 로직.

    템플릿 아이템의 속성 조합으로 변형 아이템을 일괄 생성한다.
    예: 티셔츠(색상: 빨강/파랑, 사이즈: S/M/L) → 6개 변형
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._variant_repo = Repository("item_variants", tenant_id=tenant_id)
        self._item_repo = Repository("items", tenant_id=tenant_id)

    def generate_variants(
        self,
        template_item_code: str,
        attributes: dict[str, list[str]],
    ) -> dict[str, Any]:
        """속성 조합으로 변형 아이템을 일괄 생성한다.

        Args:
            template_item_code: 템플릿 아이템 코드
            attributes: 속성 이름 → 값 목록 매핑
                예: {"색상": ["빨강", "파랑"], "사이즈": ["S", "M", "L"]}

        Returns:
            생성 결과 (variant_count, variants)
        """
        template = self._item_repo.find_by_id(template_item_code)
        if not template:
            msg = f"템플릿 아이템 '{template_item_code}'을 찾을 수 없습니다"
            raise_not_found(msg)

        if not attributes:
            msg = "속성을 1개 이상 지정해야 합니다"
            raise_unprocessable("ERR-STK-005", msg)

        # 속성 조합 생성
        attr_names = list(attributes.keys())
        attr_values = list(attributes.values())
        combinations = list(itertools.product(*attr_values))

        created_variants: list[dict[str, Any]] = []
        for combo in combinations:
            attr_dict = dict(zip(attr_names, combo, strict=True))
            # 변형 코드: 템플릿코드-속성값들
            suffix = "-".join(combo)
            variant_code = f"{template_item_code}-{suffix}"

            ivr_id = generate_name("IVR", tenant_id=self._tenant_id)
            doc = {
                "_id": ivr_id,
                "item_code": variant_code,
                "variant_of": template_item_code,
                "attributes": attr_dict,
                "tenant_id": self._tenant_id,
            }
            self._variant_repo.insert(doc)

            created_variants.append(
                {
                    "variant_id": ivr_id,
                    "item_code": variant_code,
                    "attributes": attr_dict,
                }
            )

        logger.info(
            "아이템 변형 생성: %s (%d개 변형)",
            template_item_code,
            len(created_variants),
        )

        return {
            "template_item": template_item_code,
            "variant_count": len(created_variants),
            "variants": created_variants,
        }
