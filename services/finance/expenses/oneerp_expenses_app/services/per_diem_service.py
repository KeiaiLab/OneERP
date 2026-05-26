"""출장비 일일 정액 계산 서비스.

BR-EXP-NEW-017: 국내/해외 출장 일일 정액(per diem) 자동 산정.

참조: 공무원 여비규정(기획재정부) 별표 1·2, 한국 일반 기업 출장비 관행.

정액 구조:
- 일비(daily_allowance): 매일 지급 (출장 일수 x 정액)
- 식비(meal_allowance): 매일 지급 (출장 일수 x 정액)
- 숙박비(lodging_allowance): 숙박일 지급 (출장 일수 - 1) x 정액

지역 구분:
- domestic: 국내
- overseas_tier1: 해외 1등급(미국/EU/일본 등 선진국)
- overseas_tier2: 해외 2등급(동남아/남미/기타)

직급 등급:
- regular: 일반 직원
- manager: 관리직(차장/부장)
- executive: 임원
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from oneerp_core.errors import OneERPError, raise_bad_request, raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 정액표: (region, grade) -> {daily, meal, lodging, currency}
# 공무원 여비규정 별표 + 일반 기업 관행 참조.
_PER_DIEM_TABLE: dict[tuple[str, str], dict[str, Any]] = {
    # 국내
    ("domestic", "regular"): {
        "daily": Decimal(20000),
        "meal": Decimal(20000),
        "lodging": Decimal(70000),
        "currency": "KRW",
    },
    ("domestic", "manager"): {
        "daily": Decimal(22000),
        "meal": Decimal(22000),
        "lodging": Decimal(80000),
        "currency": "KRW",
    },
    ("domestic", "executive"): {
        "daily": Decimal(25000),
        "meal": Decimal(25000),
        "lodging": Decimal(100000),
        "currency": "KRW",
    },
    # 해외 1등급 (미국/EU/일본 등 선진국)
    ("overseas_tier1", "regular"): {
        "daily": Decimal(50),
        "meal": Decimal(80),
        "lodging": Decimal(180),
        "currency": "USD",
    },
    ("overseas_tier1", "manager"): {
        "daily": Decimal(65),
        "meal": Decimal(100),
        "lodging": Decimal(220),
        "currency": "USD",
    },
    ("overseas_tier1", "executive"): {
        "daily": Decimal(80),
        "meal": Decimal(120),
        "lodging": Decimal(250),
        "currency": "USD",
    },
    # 해외 2등급 (동남아/남미 등)
    ("overseas_tier2", "regular"): {
        "daily": Decimal(40),
        "meal": Decimal(60),
        "lodging": Decimal(120),
        "currency": "USD",
    },
    ("overseas_tier2", "manager"): {
        "daily": Decimal(50),
        "meal": Decimal(75),
        "lodging": Decimal(150),
        "currency": "USD",
    },
    ("overseas_tier2", "executive"): {
        "daily": Decimal(60),
        "meal": Decimal(90),
        "lodging": Decimal(180),
        "currency": "USD",
    },
}

_SUPPORTED_REGIONS: frozenset[str] = frozenset({"domestic", "overseas_tier1", "overseas_tier2"})
_SUPPORTED_GRADES: frozenset[str] = frozenset({"regular", "manager", "executive"})


class PerDiemService:
    """출장 일일 정액(per diem) 계산 비즈니스 로직.

    출장 기간 x 지역/등급별 정액을 산정한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._travel_repo = Repository("travel_requests", tenant_id=tenant_id)

    def calculate(
        self,
        *,
        region: str,
        grade: str,
        departure_date: date,
        return_date: date,
    ) -> dict[str, Any]:
        """출장 기간과 지역/등급에 따른 정액을 계산한다.

        Args:
            region: 지역 코드 (domestic/overseas_tier1/overseas_tier2)
            grade: 직급 등급 (regular/manager/executive)
            departure_date: 출발일
            return_date: 귀환일

        Returns:
            {days, daily_allowance, meal_allowance, lodging_allowance,
             total, currency, region, grade}

        Raises:
            OneERPError: 지역/등급 미지원(400), 기간 역전(422)
        """
        if region not in _SUPPORTED_REGIONS:
            raise_bad_request(
                f"지원하지 않는 지역입니다: '{region}' (지원: {sorted(_SUPPORTED_REGIONS)})"
            )
        if grade not in _SUPPORTED_GRADES:
            raise_bad_request(
                f"지원하지 않는 등급입니다: '{grade}' (지원: {sorted(_SUPPORTED_GRADES)})"
            )
        if departure_date > return_date:
            raise OneERPError(
                status_code=422,
                error="ERR-EXP-032",
                detail=(f"출발일({departure_date})이 귀환일({return_date})보다 클 수 없습니다"),
            )

        rates = _PER_DIEM_TABLE[(region, grade)]

        # 출장 일수 = (return - departure) + 1 (당일=1일)
        days = Decimal(str((return_date - departure_date).days + 1))
        # 숙박일 = 일수 - 1 (당일=0박)
        lodging_days = max(days - Decimal(1), Decimal(0))

        daily_allowance = rates["daily"] * days
        meal_allowance = rates["meal"] * days
        lodging_allowance = rates["lodging"] * lodging_days
        total = daily_allowance + meal_allowance + lodging_allowance

        logger.info(
            "출장 정액 계산: 지역=%s, 등급=%s, 일수=%s, 총액=%s %s",
            region,
            grade,
            days,
            total,
            rates["currency"],
        )

        return {
            "region": region,
            "grade": grade,
            "departure_date": departure_date,
            "return_date": return_date,
            "days": days,
            "lodging_days": lodging_days,
            "daily_allowance": daily_allowance,
            "meal_allowance": meal_allowance,
            "lodging_allowance": lodging_allowance,
            "total": total,
            "currency": rates["currency"],
        }

    def calculate_from_request(
        self,
        *,
        travel_request_id: str,
        region: str,
        grade: str,
    ) -> dict[str, Any]:
        """출장 신청서 ID 기반으로 정액을 계산한다.

        출장 신청서에서 출발일/귀환일을 자동으로 읽어온다.

        Args:
            travel_request_id: 출장 신청서 ID
            region: 지역 코드
            grade: 직급 등급

        Returns:
            calculate()의 결과 + travel_request_id

        Raises:
            OneERPError: 출장 신청서 미존재(404)
        """
        travel = self._travel_repo.find_by_id(travel_request_id)
        if not travel:
            raise_not_found(f"출장 신청서 '{travel_request_id}'을 찾을 수 없습니다")

        departure_raw = travel.get("departure_date")
        return_raw = travel.get("return_date")

        departure_date = _parse_date(departure_raw)
        return_date = _parse_date(return_raw)

        result = self.calculate(
            region=region,
            grade=grade,
            departure_date=departure_date,
            return_date=return_date,
        )

        return {
            "travel_request_id": travel_request_id,
            **result,
        }


def _parse_date(value: Any) -> date:
    """문자열 또는 date 값을 date로 정규화한다."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise_bad_request(f"날짜 값이 올바르지 않습니다: {value!r}")
    # raise_bad_request는 Never를 반환하지만 타입 분석기 힌트를 위해 명시
    return date.min  # pragma: no cover
