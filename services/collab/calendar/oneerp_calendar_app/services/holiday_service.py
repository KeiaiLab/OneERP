"""공휴일 서비스 — 공휴일 관리, 근무일 계산, 연간 반복 처리.

BR-CAL-060: 공휴일은 날짜와 이름이 필수이다.
BR-CAL-061: 동일 날짜에 중복 공휴일 등록 불가.
BR-CAL-062: 공휴일은 연간 반복 설정이 가능하다.
BR-CAL-063: 공휴일 기반 근무일 수 계산.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class HolidayService:
    """공휴일 관리 비즈니스 로직.

    공휴일 등록, 중복 검사, 근무일 계산을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._holiday_repo = Repository("holidays", tenant_id=tenant_id)

    def check_duplicate_holiday(
        self,
        holiday_date: date,
        *,
        exclude_id: str = "",
    ) -> bool:
        """BR-CAL-061: 동일 날짜 중복 공휴일을 검사한다.

        Args:
            holiday_date: 확인할 날짜
            exclude_id: 제외할 공휴일 ID (수정 시)

        Returns:
            중복 여부 (True면 중복)
        """
        holidays = self._holiday_repo.find_many(
            {"holiday_date": holiday_date.isoformat()},
            limit=10,
        )
        for h in holidays:
            if exclude_id and h.get("_id") == exclude_id:
                continue
            return True
        return False

    def register_holiday(
        self,
        name: str,
        holiday_date: date,
        description: str = "",
        *,
        is_annual: bool = True,
        country: str = "KR",
    ) -> dict[str, Any]:
        """BR-CAL-060: 공휴일을 등록한다.

        Args:
            name: 공휴일 이름
            holiday_date: 날짜
            description: 설명
            is_annual: 매년 반복 여부
            country: 국가 코드

        Returns:
            등록 결과

        Raises:
            ValueError: ERR-CAL-061 — 중복 날짜
        """
        if self.check_duplicate_holiday(holiday_date):
            msg = f"날짜 '{holiday_date}'에 이미 공휴일이 등록되어 있습니다 (ERR-CAL-061)"
            raise ValueError(msg)

        holiday_data = {
            "name": name,
            "holiday_date": holiday_date.isoformat(),
            "description": description,
            "is_annual": is_annual,
            "country": country,
            "tenant_id": self._tenant_id,
        }
        holiday_id = self._holiday_repo.insert(holiday_data)

        logger.info("공휴일 등록: %s (%s)", name, holiday_date)
        return {
            "holiday_id": holiday_id,
            "name": name,
            "holiday_date": holiday_date.isoformat(),
        }

    def is_holiday(self, check_date: date) -> bool:
        """특정 날짜가 공휴일인지 확인한다.

        연간 반복 공휴일은 월/일만 비교한다.

        Args:
            check_date: 확인할 날짜

        Returns:
            공휴일 여부
        """
        # 정확한 날짜 매칭
        exact = self._holiday_repo.find_many(
            {"holiday_date": check_date.isoformat()},
            limit=1,
        )
        if exact:
            return True

        # 연간 반복: 같은 월/일인 공휴일이 있는지 확인
        all_holidays = self._holiday_repo.find_many(
            {"is_annual": True},
            limit=10000,
        )
        for h in all_holidays:
            h_date_str = h.get("holiday_date", "")
            if not h_date_str:
                continue
            h_date = date.fromisoformat(h_date_str)
            if h_date.month == check_date.month and h_date.day == check_date.day:
                return True

        return False

    def calculate_business_days(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """BR-CAL-063: 두 날짜 사이의 근무일 수를 계산한다.

        주말(토/일)과 공휴일을 제외한다.

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            근무일 수와 상세 정보
        """
        if start_date > end_date:
            msg = "시작일이 종료일보다 늦습니다 (ERR-CAL-063)"
            raise ValueError(msg)

        total_days = 0
        holidays_count = 0
        weekends_count = 0
        current = start_date

        while current <= end_date:
            is_weekend = current.weekday() >= 5  # 토(5), 일(6)
            is_hol = self.is_holiday(current)

            if is_weekend:
                weekends_count += 1
            elif is_hol:
                holidays_count += 1
            else:
                total_days += 1

            current += timedelta(days=1)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "business_days": total_days,
            "holidays": holidays_count,
            "weekends": weekends_count,
            "total_calendar_days": (end_date - start_date).days + 1,
        }

    def get_holidays_in_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """기간 내 공휴일 목록을 반환한다.

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            공휴일 목록
        """
        all_holidays = self._holiday_repo.find_many({}, limit=10000)
        result: list[dict[str, Any]] = []

        for h in all_holidays:
            h_date_str = h.get("holiday_date", "")
            if not h_date_str:
                continue
            h_date = date.fromisoformat(h_date_str)

            # 정확한 범위 내
            if start_date <= h_date <= end_date:
                result.append(h)
                continue

            # 연간 반복: 올해 날짜로 변환하여 확인
            if h.get("is_annual"):
                for year in range(start_date.year, end_date.year + 1):
                    try:
                        annual_date = h_date.replace(year=year)
                    except ValueError:
                        continue  # 2/29 등 유효하지 않은 날짜
                    if start_date <= annual_date <= end_date:
                        result.append({**h, "holiday_date": annual_date.isoformat()})

        return result
