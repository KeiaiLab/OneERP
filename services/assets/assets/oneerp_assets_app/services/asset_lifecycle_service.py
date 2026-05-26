"""자산 생애주기 서비스 — 이동, 처분, 재평가, 이력 조회.

L2 비즈니스 룰 매핑:
- BR-009: 처분손익 자동 계산 (gain_loss = sale_amount - book_value)
- BR-010: 처분 시 상태 변경 (scrapped)
- BR-011: 재평가 차액 기록 (old_value/new_value/difference)
- BR-012: 자산 이동 시 출발지/도착지 필수
- BR-017: 자산 존재 확인
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class AssetLifecycleService:
    """자산 생애주기 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._asset_repo = Repository("assets", tenant_id=tenant_id)
        self._movement_repo = Repository("asset_movements", tenant_id=tenant_id)
        self._disposal_repo = Repository("asset_disposals", tenant_id=tenant_id)
        self._revaluation_repo = Repository("asset_revaluations", tenant_id=tenant_id)
        self._dep_repo = Repository("depreciation_entries", tenant_id=tenant_id)

    def move_asset(
        self,
        asset_id: str,
        from_location: str,
        to_location: str,
        movement_date: date | None = None,
    ) -> dict[str, Any]:
        """자산을 다른 위치로 이동한다. AssetMovement를 생성한다."""
        asset = self._asset_repo.find_by_id(asset_id)
        if not asset:
            raise_not_found(f"자산 '{asset_id}'을 찾을 수 없습니다")

        if movement_date is None:
            movement_date = datetime.now(tz=UTC).date()

        movement_id = generate_name("AMOV", tenant_id=self._tenant_id)
        self._movement_repo.insert(
            {
                "_id": movement_id,
                "asset": asset_id,
                "asset_name": asset.get("asset_name", ""),
                "from_location": from_location,
                "to_location": to_location,
                "movement_date": movement_date,
                "purpose": "transfer",
                "tenant_id": self._tenant_id,
            },
        )

        logger.info("자산 이동: %s (%s → %s)", asset_id, from_location, to_location)
        return {
            "movement_id": movement_id,
            "asset_id": asset_id,
            "from_location": from_location,
            "to_location": to_location,
        }

    def dispose_asset(
        self,
        asset_id: str,
        disposal_method: str,
        sale_amount: float = 0.0,
        disposal_date: date | None = None,
    ) -> dict[str, Any]:
        """자산을 처분한다.

        gain_loss = 매각금액 - 장부가
        자산 상태를 scrapped로 변경한다.
        """
        asset = self._asset_repo.find_by_id(asset_id)
        if not asset:
            raise_not_found(f"자산 '{asset_id}'을 찾을 수 없습니다")

        if disposal_date is None:
            disposal_date = datetime.now(tz=UTC).date()

        book_value = float(asset.get("current_value", 0))
        gain_loss = round(sale_amount - book_value, 2)

        disposal_id = generate_name("ADSP", tenant_id=self._tenant_id)
        self._disposal_repo.insert(
            {
                "_id": disposal_id,
                "asset": asset_id,
                "asset_name": asset.get("asset_name", ""),
                "disposal_date": disposal_date,
                "disposal_method": disposal_method,
                "sale_amount": sale_amount,
                "book_value": book_value,
                "gain_loss": gain_loss,
                "tenant_id": self._tenant_id,
            },
        )

        # 자산 상태를 scrapped로 변경
        self._asset_repo.update_by_id(asset_id, {"status": "scrapped"})

        logger.info("자산 처분: %s (방법: %s, 손익: %.2f)", asset_id, disposal_method, gain_loss)
        return {
            "disposal_id": disposal_id,
            "asset_id": asset_id,
            "disposal_method": disposal_method,
            "book_value": book_value,
            "sale_amount": sale_amount,
            "gain_loss": gain_loss,
        }

    def revalue_asset(
        self,
        asset_id: str,
        new_value: float,
        revaluation_date: date | None = None,
    ) -> dict[str, Any]:
        """자산을 재평가한다. 차액을 기록하고 current_value를 업데이트한다."""
        asset = self._asset_repo.find_by_id(asset_id)
        if not asset:
            raise_not_found(f"자산 '{asset_id}'을 찾을 수 없습니다")

        if revaluation_date is None:
            revaluation_date = datetime.now(tz=UTC).date()

        old_value = float(asset.get("current_value", 0))
        difference = round(new_value - old_value, 2)

        reval_id = generate_name("ARVAL", tenant_id=self._tenant_id)
        self._revaluation_repo.insert(
            {
                "_id": reval_id,
                "asset_id": asset_id,
                "revaluation_date": revaluation_date,
                "current_value": old_value,
                "revalued_amount": new_value,
                "revaluation_method": "manual",
                "tenant_id": self._tenant_id,
            },
        )

        # 자산 장부가 업데이트
        self._asset_repo.update_by_id(asset_id, {"current_value": new_value})

        logger.info("자산 재평가: %s (%.2f → %.2f)", asset_id, old_value, new_value)
        return {
            "revaluation_id": reval_id,
            "asset_id": asset_id,
            "old_value": old_value,
            "new_value": new_value,
            "difference": difference,
        }

    def get_asset_history(self, asset_id: str) -> dict[str, Any]:
        """자산의 이동/처분/재평가/상각 통합 이력을 조회한다."""
        asset = self._asset_repo.find_by_id(asset_id)
        if not asset:
            raise_not_found(f"자산 '{asset_id}'을 찾을 수 없습니다")

        movements = self._movement_repo.find_many({"asset": asset_id}, limit=10000)
        disposals = self._disposal_repo.find_many({"asset": asset_id}, limit=10000)
        revaluations = self._revaluation_repo.find_many({"asset_id": asset_id}, limit=10000)
        depreciations = self._dep_repo.find_many({"asset_ref": asset_id}, limit=10000)

        return {
            "asset_id": asset_id,
            "asset_name": asset.get("asset_name", ""),
            "current_value": float(asset.get("current_value", 0)),
            "movements": movements,
            "disposals": disposals,
            "revaluations": revaluations,
            "depreciations": depreciations,
        }
