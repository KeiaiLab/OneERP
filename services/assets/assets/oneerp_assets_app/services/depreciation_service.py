"""감가상각 서비스 — 정액법/정률법 상각 계산 및 월별 일괄 상각.

L2 비즈니스 룰 매핑:
- BR-004: 잔존가치 보호 (상각 후 장부가 >= 잔존가치)
- BR-005: 상각 대상 제한 (status=submitted만)
- BR-006: 상각 중단 조건 (장부가 <= 잔존가치)
- BR-007: 내용연수 유효성 (0 이하 불가)
- BR-008: 정률법 자동 상각률 계산
- BR-013: 누적상각액 정합성
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class DepreciationService:
    """감가상각 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._asset_repo = Repository("assets", tenant_id=tenant_id)
        self._dep_repo = Repository("depreciation_entries", tenant_id=tenant_id)

    def calculate_straight_line(self, asset_id: str) -> float:
        """정액법 월별 상각액을 계산한다.

        공식: (취득원가 - 잔존가치) / (내용연수 * 12)
        """
        asset = self._asset_repo.find_by_id(asset_id)
        if not asset:
            raise_not_found(f"자산 '{asset_id}'을 찾을 수 없습니다")

        gross = float(asset.get("gross_amount", 0))
        salvage = float(asset.get("salvage_value", 0))
        useful_years = int(asset.get("useful_life_years", 0))

        if useful_years <= 0:
            raise_unprocessable(
                "ERR-AST-001",
                f"자산 '{asset_id}'의 내용연수가 유효하지 않습니다",
            )

        monthly = (gross - salvage) / (useful_years * 12)
        return round(monthly, 2)

    def calculate_declining_balance(
        self,
        asset_id: str,
        rate: float | None = None,
    ) -> float:
        """정률법 월별 상각액을 계산한다.

        rate 미지정 시 자동 계산: 1 - (salvage / gross) ^ (1 / useful_life_years)
        월별 상각액: 장부가 * rate / 12
        """
        asset = self._asset_repo.find_by_id(asset_id)
        if not asset:
            raise_not_found(f"자산 '{asset_id}'을 찾을 수 없습니다")

        gross = float(asset.get("gross_amount", 0))
        salvage = float(asset.get("salvage_value", 0))
        current = float(asset.get("current_value", 0))
        useful_years = int(asset.get("useful_life_years", 0))

        if useful_years <= 0:
            raise_unprocessable(
                "ERR-AST-001",
                f"자산 '{asset_id}'의 내용연수가 유효하지 않습니다",
            )

        if rate is None:
            if gross <= 0 or salvage <= 0:
                raise_unprocessable(
                    "ERR-AST-002",
                    "정률법 자동 계산에는 취득원가와 잔존가치가 0보다 커야 합니다",
                )
            rate = 1 - (salvage / gross) ** (1 / useful_years)

        monthly = current * rate / 12
        return round(monthly, 2)

    def run_monthly_depreciation(self, year_month: str) -> list[dict[str, Any]]:
        """전체 active 자산에 대해 월별 일괄 상각을 실행한다.

        DepreciationEntry를 생성하고 current_value를 차감한다.

        Args:
            year_month: 상각 기간 (예: "2026-03")

        Returns:
            생성된 상각 항목 목록
        """
        # active 자산 조회 (status=submitted)
        assets = self._asset_repo.find_many(
            {"status": "submitted"},
            limit=10000,
        )

        results: list[dict[str, Any]] = []
        for asset in assets:
            asset_id = asset["_id"]
            method = asset.get("depreciation_method", "straight_line")
            current_value = float(asset.get("current_value", 0))
            salvage_value = float(asset.get("salvage_value", 0))

            # 잔존가치 이하이면 상각 불필요
            if current_value <= salvage_value:
                continue

            # 상각액 계산
            if method == "declining_balance":
                dep_amount = self.calculate_declining_balance(asset_id)
            else:
                dep_amount = self.calculate_straight_line(asset_id)

            # 상각 후 잔존가치 미만이 되지 않도록 조정
            if current_value - dep_amount < salvage_value:
                dep_amount = round(current_value - salvage_value, 2)

            new_value = round(current_value - dep_amount, 2)
            gross = float(asset.get("gross_amount", 0))
            accumulated = round(gross - new_value, 2)

            # 상각 항목 생성
            year, month = year_month.split("-")
            posting_date = date(int(year), int(month), 1)
            entry_id = generate_name("DEP", tenant_id=self._tenant_id)

            self._dep_repo.insert(
                {
                    "_id": entry_id,
                    "asset_ref": asset_id,
                    "posting_date": posting_date,
                    "depreciation_amount": dep_amount,
                    "accumulated_depreciation": accumulated,
                    "remaining_value": new_value,
                    "tenant_id": self._tenant_id,
                },
            )

            # 자산 장부가 업데이트
            self._asset_repo.update_by_id(asset_id, {"current_value": new_value})

            results.append(
                {
                    "entry_id": entry_id,
                    "asset_id": asset_id,
                    "depreciation_amount": dep_amount,
                    "remaining_value": new_value,
                },
            )

        logger.info("월별 상각 완료: %s — %d건", year_month, len(results))
        return results

    def get_depreciation_schedule(self, asset_id: str) -> list[dict[str, Any]]:
        """전체 기간 감가상각 스케줄 미리보기를 반환한다."""
        asset = self._asset_repo.find_by_id(asset_id)
        if not asset:
            raise_not_found(f"자산 '{asset_id}'을 찾을 수 없습니다")

        gross = float(asset.get("gross_amount", 0))
        salvage = float(asset.get("salvage_value", 0))
        useful_years = int(asset.get("useful_life_years", 0))
        method = asset.get("depreciation_method", "straight_line")
        current = float(asset.get("current_value", 0))

        if useful_years <= 0:
            return []

        total_months = useful_years * 12
        schedule: list[dict[str, Any]] = []
        remaining = current

        for month_idx in range(1, total_months + 1):
            if remaining <= salvage:
                break

            if method == "declining_balance":
                # 정률법: 자동 rate 계산
                if gross > 0 and salvage > 0:
                    rate = 1 - (salvage / gross) ** (1 / useful_years)
                else:
                    break
                dep_amount = round(remaining * rate / 12, 2)
            else:
                dep_amount = round((gross - salvage) / total_months, 2)

            # 잔존가치 보호
            if remaining - dep_amount < salvage:
                dep_amount = round(remaining - salvage, 2)

            remaining = round(remaining - dep_amount, 2)
            accumulated = round(gross - remaining, 2)

            schedule.append(
                {
                    "month": month_idx,
                    "depreciation_amount": dep_amount,
                    "accumulated_depreciation": accumulated,
                    "remaining_value": remaining,
                },
            )

        return schedule
