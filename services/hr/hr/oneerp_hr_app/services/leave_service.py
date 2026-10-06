"""휴가 관리 서비스 — 휴가 정책 적용, 보상휴가, 잔여 일수 계산, 연차 자동화 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-HR-001: 연차 자동 부여 (근로기준법 제60조)
- BR-HR-003: 휴가 신청 잔여 검증 (잔여 >= 신청일수)
- BR-HR-004: 연차 사용 촉진 (6개월/2개월 전 알림)
- BR-HR-010: 휴가 OPEN 상태만 승인/거절/삭제 가능
- BR-HR-014: 휴가 이월 한도 (max_carry_forward_days)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any, cast

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class LeaveService:
    """휴가 관리 비즈니스 로직.

    휴가 정책 배정, 잔여 일수 계산, 보상휴가 처리.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._policy_repo = Repository("leave_policies", tenant_id=tenant_id)
        self._assignment_repo = Repository("leave_policy_assignments", tenant_id=tenant_id)
        self._balance_repo = Repository("leave_balances", tenant_id=tenant_id)
        self._leave_repo = Repository("leaves", tenant_id=tenant_id)
        self._comp_repo = Repository("compensatory_leave_requests", tenant_id=tenant_id)

    def get_leave_balance(
        self,
        employee: str,
        leave_type: str = "",
    ) -> dict[str, Any]:
        """직원의 휴가 잔여 일수를 조회한다."""
        query: dict[str, Any] = {"employee": employee}
        if leave_type:
            query["leave_type"] = leave_type

        balances = self._balance_repo.find_many(query, limit=100)

        result: list[dict[str, Any]] = []
        total_remaining = 0.0
        for bal in balances:
            allocated = float(bal.get("allocated_days", 0))
            used = float(bal.get("used_days", 0))
            remaining = allocated - used
            total_remaining += remaining
            result.append(
                {
                    "leave_type": bal.get("leave_type", ""),
                    "allocated": allocated,
                    "used": used,
                    "remaining": remaining,
                }
            )

        return {
            "employee": employee,
            "balances": result,
            "total_remaining": total_remaining,
        }

    def process_compensatory_leave(
        self,
        employee: str,
        work_date: Any,
        reason: str = "",
        days: float = 1.0,
    ) -> dict[str, Any]:
        """보상휴가를 처리한다.

        초과근무/휴일근무에 대한 보상휴가를 잔여 일수에 추가.

        Args:
            employee: 직원 ID
            work_date: 근무일
            reason: 사유
            days: 보상 일수

        Returns:
            처리 결과
        """
        # 보상휴가 잔액 업데이트
        balances = self._balance_repo.find_many(
            {"employee": employee, "leave_type": "보상휴가"},
            limit=1,
        )

        if balances:
            current = float(balances[0].get("allocated_days", 0))
            self._balance_repo.update_by_id(
                balances[0]["_id"],
                {"allocated_days": current + days},
            )
        else:
            self._balance_repo.insert(
                {
                    "employee": employee,
                    "leave_type": "보상휴가",
                    "allocated_days": days,
                    "used_days": 0,
                    "tenant_id": self._tenant_id,
                }
            )

        logger.info(
            "보상휴가 처리: +%.1f일, 사유 %s",
            days,
            reason,
        )

        return {
            "employee": employee,
            "compensatory_days": days,
            "work_date": str(work_date),
            "reason": reason,
        }

    def grant_annual_leave(
        self,
        employee_id: str,
        fiscal_year: str,
    ) -> dict[str, Any]:
        """BR-HR-001: 직원에게 근속연수 기반 연차를 자동 부여한다.

        - 1년 미만: 근속 월수 x 1일
        - 1년 이상: 15일
        - 3년 이상: 15 + (근속연수 - 2)일 (최대 25일)

        Args:
            employee_id: 직원 ID
            fiscal_year: 회계연도 (예: "2026")

        Returns:
            부여된 연차 정보
        """
        employee_repo = Repository("employees", tenant_id=self._tenant_id)
        employee = employee_repo.find_by_id(employee_id)
        if not employee:
            raise_not_found(f"직원 '{employee_id}'를 찾을 수 없습니다")
        employee = cast("dict[str, Any]", employee)

        join_date = date.fromisoformat(employee["date_of_joining"])
        today = datetime.now(UTC).date()

        # 근속 개월수 계산
        months = (today.year - join_date.year) * 12 + (today.month - join_date.month)
        years = months // 12

        if years < 1:
            # 1년 미만: 월 1일 (최대 11일)
            allocated_days = min(months, 11)
        elif years < 3:
            # 1~2년: 15일
            allocated_days = 15
        else:
            # 3년 이상: 15 + (근속연수 - 2)일, 최대 25일
            allocated_days = min(15 + (years - 2), 25)

        # leave_balances에 upsert
        existing = self._balance_repo.find_many(
            {"employee": employee_id, "leave_type": "연차", "fiscal_year": fiscal_year},
            limit=1,
        )
        if existing:
            self._balance_repo.update_by_id(
                existing[0]["_id"],
                {"allocated_days": allocated_days},
            )
        else:
            self._balance_repo.insert(
                {
                    "employee": employee_id,
                    "leave_type": "연차",
                    "fiscal_year": fiscal_year,
                    "allocated_days": float(allocated_days),
                    "used_days": 0.0,
                    "tenant_id": self._tenant_id,
                }
            )

        logger.info("연차 부여: %d일 (회계연도: %s)", allocated_days, fiscal_year)
        return {
            "employee": employee_id,
            "fiscal_year": fiscal_year,
            "allocated_days": allocated_days,
        }

    def process_leave_application(
        self,
        leave_app_id: str,
        action: str,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """휴가 신청을 승인 또는 거절 처리한다.

        approve 시 leave_balances의 used_days를 차감하고
        LEAVE_APPLICATION_APPROVED 이벤트를 발행한다.

        Args:
            leave_app_id: 휴가 신청 ID
            action: "approve" 또는 "reject"

        Returns:
            처리 결과

        Raises:
            OneERPError: 잔여 연차 부족 시
        """
        app_repo = Repository("leave_applications", tenant_id=self._tenant_id)
        leave_app = app_repo.find_by_id(leave_app_id)
        if not leave_app:
            raise_not_found(f"휴가 신청 '{leave_app_id}'를 찾을 수 없습니다")

        # BR-HR-010: OPEN 상태의 휴가 신청만 승인/거절 가능 (이중 승인 방지)
        if leave_app.get("status") != "open":
            raise_unprocessable(
                "ERR-HR-032",
                "OPEN 상태의 휴가 신청만 승인/거절할 수 있습니다",
            )

        if action == "approve":
            employee = leave_app.get("employee_id") or leave_app.get("employee")
            if not employee:
                raise_not_found("휴가 신청의 직원 정보를 찾을 수 없습니다")
            leave_type = leave_app.get("leave_type", "연차")
            total_days = float(leave_app.get("total_days", 0))

            # 잔여 일수 확인
            balances = self._balance_repo.find_many(
                {"employee": employee, "leave_type": leave_type},
                limit=1,
            )
            if not balances:
                raise_not_found("휴가 잔액 정보가 없습니다")

            balance = balances[0]
            allocated_days = float(
                balance.get("allocated_days", balance.get("total_allocated", 0)),
            )
            used_days = float(balance.get("used_days", balance.get("total_used", 0)))
            remaining = float(balance.get("balance", allocated_days - used_days))
            if remaining < total_days:
                raise_unprocessable(
                    "ERR-HR-030",
                    f"잔여 연차가 부족합니다 (잔여: {remaining}일, 신청: {total_days}일)",
                )

            # used_days 증가
            new_used_days = used_days + total_days
            update = {
                "used_days": new_used_days,
                "total_used": new_used_days,
                "balance": allocated_days - new_used_days,
            }
            self._balance_repo.update_by_id(
                balance["_id"],
                update,
            )
            application_update = {"status": "approved"}
            if actor_id:
                application_update["updated_by"] = actor_id
            app_repo.update_by_id(leave_app_id, application_update)

            logger.info("휴가 승인: %s (%.1f일)", leave_app_id, total_days)
            return {"leave_app_id": leave_app_id, "status": "approved"}

        # reject
        application_update = {"status": "rejected"}
        if actor_id:
            application_update["updated_by"] = actor_id
        app_repo.update_by_id(leave_app_id, application_update)
        logger.info("휴가 거절: %s", leave_app_id)
        return {"leave_app_id": leave_app_id, "status": "rejected"}

    def run_leave_promotion(self, fiscal_year: str) -> list[dict[str, Any]]:
        """BR-HR-004: 연차 사용 촉진 대상자를 조회하고 통보 기록을 생성한다.

        - 1차: 사용기한 6개월 전 통보
        - 2차: 사용기한 2개월 전 통보

        Args:
            fiscal_year: 회계연도

        Returns:
            통보 대상 목록
        """
        today = datetime.now(UTC).date()
        notifications: list[dict[str, Any]] = []

        # LeaveBalance 모델에 remaining_days 필드는 없으므로 allocated_days > 0 조건으로 조회 후
        # Python 레벨에서 잔여 일수(allocated_days - used_days) 필터 적용
        balances = self._balance_repo.find_many(
            {"fiscal_year": fiscal_year, "allocated_days": {"$gt": 0}},
            limit=10000,
        )

        notification_repo = Repository("leave_promotion_notices", tenant_id=self._tenant_id)

        for bal in balances:
            # 잔여 일수가 0 이하인 경우 촉진 대상에서 제외
            allocated = float(bal.get("allocated_days", 0))
            used = float(bal.get("used_days", 0))
            if allocated - used <= 0:
                continue
            expiry_str = bal.get("expiry_date", "")
            if not expiry_str:
                continue

            expiry = date.fromisoformat(expiry_str)
            days_until_expiry = (expiry - today).days

            notice_stage: str | None = None
            if 150 <= days_until_expiry <= 180:
                # 6개월 전 (약 180일): 1차 통보
                notice_stage = "1차"
            elif 50 <= days_until_expiry <= 60:
                # 2개월 전 (약 60일): 2차 통보
                notice_stage = "2차"

            if notice_stage:
                notice = {
                    "employee": bal.get("employee", ""),
                    "leave_type": bal.get("leave_type", "연차"),
                    "fiscal_year": fiscal_year,
                    "remaining_days": allocated - used,
                    "expiry_date": expiry_str,
                    "notice_stage": notice_stage,
                    "noticed_at": datetime.now(UTC).isoformat(),
                    "tenant_id": self._tenant_id,
                }
                notification_repo.insert(notice)
                notifications.append(notice)

        logger.info("연차 촉진 처리: %d명 (회계연도: %s)", len(notifications), fiscal_year)
        return notifications

    def carry_forward_leave(
        self,
        employee_id: str,
        from_year: str,
        to_year: str,
    ) -> dict[str, Any]:
        """BR-HR-014: 잔여 연차를 다음 연도로 이월한다.

        leave_policies에서 carry_forward=true인 정책의 max_carry_forward_days를 조회하고,
        from_year 잔여일수와 비교하여 min(잔여, max_carry_forward_days)만 이월한다.
        초과분은 소멸 처리된다.

        Args:
            employee_id: 직원 ID
            from_year: 이월 원천 회계연도 (예: "2025")
            to_year: 이월 대상 회계연도 (예: "2026")

        Returns:
            이월 결과 (이월일수, 소멸일수 포함)
        """
        # carry_forward=true인 휴가 정책 조회
        policies = self._policy_repo.find_many(
            {"carry_forward": True},
            limit=100,
        )
        if not policies:
            return {
                "employee": employee_id,
                "from_year": from_year,
                "to_year": to_year,
                "carried_forward": 0.0,
                "expired": 0.0,
            }

        total_carried = 0.0
        total_expired = 0.0

        for policy in policies:
            max_carry = float(policy.get("max_carry_forward_days", 0))
            leave_type = policy.get("leave_type_id", "연차")

            # from_year 잔여 일수 조회
            balances = self._balance_repo.find_many(
                {
                    "employee": employee_id,
                    "leave_type": leave_type,
                    "fiscal_year": from_year,
                },
                limit=1,
            )
            if not balances:
                continue

            bal = balances[0]
            allocated = float(bal.get("allocated_days", 0))
            used = float(bal.get("used_days", 0))
            remaining = max(0.0, allocated - used)

            if remaining <= 0:
                continue

            carry_days = min(remaining, max_carry)
            expired_days = remaining - carry_days

            # to_year 잔액에 이월분 추가
            to_balances = self._balance_repo.find_many(
                {
                    "employee": employee_id,
                    "leave_type": leave_type,
                    "fiscal_year": to_year,
                },
                limit=1,
            )
            if to_balances:
                current_allocated = float(to_balances[0].get("allocated_days", 0))
                self._balance_repo.update_by_id(
                    to_balances[0]["_id"],
                    {"allocated_days": current_allocated + carry_days},
                )
            else:
                self._balance_repo.insert(
                    {
                        "employee": employee_id,
                        "leave_type": leave_type,
                        "fiscal_year": to_year,
                        "allocated_days": carry_days,
                        "used_days": 0.0,
                        "tenant_id": self._tenant_id,
                    }
                )

            total_carried += carry_days
            total_expired += expired_days

        logger.info(
            "연차 이월: %s→%s, 이월 %.1f일, 소멸 %.1f일",
            from_year,
            to_year,
            total_carried,
            total_expired,
        )

        return {
            "employee": employee_id,
            "from_year": from_year,
            "to_year": to_year,
            "carried_forward": total_carried,
            "expired": total_expired,
        }
