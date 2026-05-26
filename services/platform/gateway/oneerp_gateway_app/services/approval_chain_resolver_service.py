"""결재선 동적 결정 서비스 — 한국 전자결재 표준 기반.

L2 비즈니스 룰 매핑:
- BR-APR-021: 결재선 동적 결정 (문서 유형 + 금액 + 조직도 기반)
- BR-APR-022: 부재중 자동 위임 적용 (OutOfOffice/DelegationRule)

핵심 패턴:
1. 금액 기반 승급(escalation): amount_thresholds에 따라 추가 결재 단계 삽입
   - 예: 100만원 이하 팀장, 500만원 이하 부장, 5000만원 이하 임원, 초과 시 대표
2. 역할 기반 동적 결재자: approver_role 지정만 있으면 현재 기안자의 라인 매니저/부서장을 조회
3. 부재중 자동 위임: 결재자가 out_of_office=true이거나 유효 DelegationRule이 있으면 대리자로 치환
4. 중복 제거: 동일 결재자가 연속 단계에 있으면 상위 단계로 병합

참고 베스트 프랙티스:
- 한국 그룹웨어(다우오피스/한비로) 표준: 기안 -> 합의 -> 결재 -> 전결권자
- ERPNext Workflow: 조건부 transition rules (doc.grand_total > X)
- AWS SaaS 멀티테넌트: RBAC + 속성 기반 가산
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 기본 금액 임계값(원화) — 초과 시 추가 결재 단계 필요
_DEFAULT_AMOUNT_THRESHOLDS = [
    (Decimal(1000000), "team_lead"),  # 100만원 이하: 팀장까지
    (Decimal(5000000), "department_head"),  # 500만원 이하: 부서장까지
    (Decimal(50000000), "executive"),  # 5000만원 이하: 임원까지
    (Decimal(999999999999), "ceo"),  # 초과: 대표
]


class ApprovalChainResolverService:
    """결재선 동적 결정 서비스.

    ApprovalTemplate의 steps를 기반으로 하되, 문서 금액과 기안자의 조직
    위치, 부재중 위임 규칙을 반영하여 최종 결재 라인을 동적으로 구성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._template_repo = Repository("approval_templates", tenant_id=tenant_id)
        self._user_repo = Repository("users", tenant_id=tenant_id)
        self._delegation_repo = Repository("delegation_rules", tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # BR-APR-021: 결재선 동적 결정
    # ------------------------------------------------------------------

    def resolve_chain(
        self,
        document_type: str,
        requester: str,
        amount: Decimal | float | int = Decimal(0),
        requester_department: str = "",
    ) -> dict[str, Any]:
        """BR-APR-021: 결재선을 동적으로 결정한다.

        1. document_type으로 ApprovalTemplate 조회
        2. 템플릿의 steps를 baseline으로 사용
        3. 금액 기반 임계값을 초과하면 필요한 역할까지 단계 확장
        4. approver_role로 조직도에서 실제 결재자 매핑
        5. 위임/부재중 치환 적용
        6. 연속 동일 결재자 중복 제거

        Args:
            document_type: 문서 유형 (예: "PurchaseOrder", "ExpenseClaim")
            requester: 기안자 ID
            amount: 문서 금액 (0이면 금액 기반 승급 생략)
            requester_department: 기안자 부서 ID

        Returns:
            {
                "chain": [{"step": 1, "approver": "USR-001", "approver_role": "team_lead", ...}],
                "total_steps": 3,
                "amount_tier": "department_head",
                "delegations_applied": [{"from": "A", "to": "B"}],
            }

        Raises:
            OneERPError: 템플릿 미존재 또는 결재자 매핑 실패
        """
        amount_decimal = Decimal(str(amount))

        template = self._get_template(document_type)
        baseline_steps: list[dict[str, Any]] = list(template.get("steps", []))

        # 1단계: 금액 기반 최소 결재 단계 결정
        minimum_role = self._determine_minimum_role(amount_decimal)

        # 2단계: 역할 기반 조직도 매핑
        resolved_lines: list[dict[str, Any]] = []
        for step_cfg in baseline_steps:
            step_no = int(step_cfg.get("step", 0))
            role = str(step_cfg.get("approver_role", ""))
            fixed_approver = str(step_cfg.get("approver", ""))
            approval_type = str(step_cfg.get("approval_type", "single"))
            pre_approval_roles = list(step_cfg.get("pre_approval_roles", []))

            # 고정 결재자가 있으면 그대로 사용, 없으면 역할 기반 조회
            if fixed_approver:
                approver = fixed_approver
            elif role:
                approver = self._resolve_approver_by_role(role, requester_department, requester)
                if not approver:
                    logger.warning(
                        "역할 '%s'에 해당하는 결재자를 찾을 수 없음 (부서: %s)",
                        role,
                        requester_department,
                    )
                    continue
            else:
                raise_unprocessable(
                    "ERR-APR-021",
                    f"단계 {step_no}에 결재자/역할이 지정되지 않았습니다",
                )

            resolved_lines.append(
                {
                    "step": step_no,
                    "approver": approver,
                    "approver_role": role,
                    "approval_type": approval_type,
                    "pre_approval_roles": pre_approval_roles,
                    "status": "pending",
                    "comment": "",
                    "acted_at": None,
                }
            )

        # 3단계: 금액 기반 필수 역할이 체인에 없으면 마지막 단계에 추가
        # 금액이 0 이하이면 템플릿의 결재선을 그대로 사용 (강제 승급 생략)
        if amount_decimal > 0:
            resolved_lines = self._ensure_minimum_role_present(
                resolved_lines,
                minimum_role,
                requester_department,
                requester,
            )

        # 4단계: 부재중 자동 위임 적용
        delegations_applied: list[dict[str, str]] = []
        resolved_lines = self._apply_delegations(resolved_lines, delegations_applied)

        # 5단계: 연속 동일 결재자 중복 제거 (병합 — 상위 단계 유지)
        resolved_lines = self._deduplicate_consecutive(resolved_lines)

        total_steps = len({line["step"] for line in resolved_lines})

        logger.info(
            "결재선 동적 결정: doc=%s, amount=%s, tier=%s, steps=%d, delegations=%d",
            document_type,
            amount_decimal,
            minimum_role,
            total_steps,
            len(delegations_applied),
        )

        return {
            "chain": resolved_lines,
            "total_steps": total_steps,
            "amount_tier": minimum_role,
            "delegations_applied": delegations_applied,
        }

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _get_template(self, document_type: str) -> dict[str, Any]:
        """문서 유형에 해당하는 템플릿을 조회한다."""
        templates = self._template_repo.find_many(
            {"document_type": document_type},
            limit=1,
        )
        if not templates:
            raise_not_found(f"문서 유형 '{document_type}'에 해당하는 결재 템플릿이 없습니다")
        return templates[0]

    def _determine_minimum_role(self, amount: Decimal) -> str:
        """금액 기반 최소 필수 결재 역할을 결정한다.

        _DEFAULT_AMOUNT_THRESHOLDS의 첫 번째로 amount 이하인 임계값의 역할을 반환.
        예: 300만원 -> "department_head" (500만원 이하 구간)
        """
        if amount <= 0:
            return "team_lead"

        for threshold, role in _DEFAULT_AMOUNT_THRESHOLDS:
            if amount <= threshold:
                return role
        return "ceo"

    def _resolve_approver_by_role(
        self,
        role: str,
        department: str,
        requester: str,
    ) -> str:
        """역할명으로 실제 결재자 사용자 ID를 조회한다.

        조회 우선순위:
        1. 동일 부서의 해당 역할 사용자
        2. 전체 테넌트의 해당 역할 사용자 (첫 번째)
        """
        # 부서 스코프 우선 조회
        if department:
            users = self._user_repo.find_many(
                {
                    "roles": {"$in": [role]},
                    "department": department,
                    "is_active": True,
                },
                limit=1,
            )
            if users:
                candidate = str(users[0].get("_id", ""))
                if candidate and candidate != requester:
                    return candidate

        # 전체 스코프 폴백
        users = self._user_repo.find_many(
            {"roles": {"$in": [role]}, "is_active": True},
            limit=10,
        )
        for user in users:
            candidate = str(user.get("_id", ""))
            if candidate and candidate != requester:
                return candidate
        return ""

    def _ensure_minimum_role_present(
        self,
        lines: list[dict[str, Any]],
        minimum_role: str,
        department: str,
        requester: str,
    ) -> list[dict[str, Any]]:
        """금액 기반 필수 역할이 체인에 없으면 마지막에 추가한다."""
        role_priority = {
            "team_lead": 1,
            "department_head": 2,
            "executive": 3,
            "ceo": 4,
        }
        required_level = role_priority.get(minimum_role, 0)
        if required_level == 0:
            return lines

        # 이미 minimum_role 이상의 라인이 있으면 추가 불필요
        max_level_in_chain = 0
        for line in lines:
            line_role = str(line.get("approver_role", ""))
            max_level_in_chain = max(max_level_in_chain, role_priority.get(line_role, 0))

        if max_level_in_chain >= required_level:
            return lines

        # 필수 역할의 결재자 조회 후 마지막 단계로 추가
        approver = self._resolve_approver_by_role(minimum_role, department, requester)
        if not approver:
            logger.warning(
                "금액 기반 필수 역할 '%s'의 결재자를 찾을 수 없어 추가하지 못함",
                minimum_role,
            )
            return lines

        next_step = max((int(line.get("step", 0)) for line in lines), default=0) + 1
        lines.append(
            {
                "step": next_step,
                "approver": approver,
                "approver_role": minimum_role,
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
                "auto_added_for_amount": True,
            }
        )
        return lines

    def _apply_delegations(
        self,
        lines: list[dict[str, Any]],
        delegations_applied: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """BR-APR-022: 부재중/위임 규칙에 따라 결재자를 치환한다.

        - users.out_of_office=true이고 out_of_office_delegate가 있으면 대리자로 치환
        - delegation_rules에 유효(is_active, 현재 날짜 범위) 규칙이 있으면 대리자로 치환
        - 치환 내역은 delegations_applied에 기록
        """
        today = datetime.now(tz=UTC).date()

        for line in lines:
            original = str(line.get("approver", ""))
            if not original:
                continue

            # 1) 사용자 out_of_office 플래그 확인
            user_doc = self._user_repo.find_by_id(original)
            if user_doc and bool(user_doc.get("out_of_office", False)):
                backup = str(user_doc.get("out_of_office_delegate", ""))
                if backup and backup != original:
                    line["approver"] = backup
                    line["delegated_from"] = original
                    delegations_applied.append(
                        {"from": original, "to": backup, "reason": "out_of_office"}
                    )
                    continue

            # 2) delegation_rules 검사
            rules = self._delegation_repo.find_many(
                {"delegator": original, "is_active": True},
                limit=10,
            )
            for rule in rules:
                if not self._is_rule_valid(rule, today):
                    continue
                delegate = str(rule.get("delegate", ""))
                if delegate and delegate != original:
                    line["approver"] = delegate
                    line["delegated_from"] = original
                    delegations_applied.append(
                        {"from": original, "to": delegate, "reason": "delegation_rule"}
                    )
                    break

        return lines

    def _is_rule_valid(self, rule: dict[str, Any], today: date) -> bool:
        """위임 규칙의 날짜 범위가 오늘 날짜를 포함하는지 확인한다."""
        from_date = rule.get("from_date")
        to_date = rule.get("to_date")

        # datetime -> date 변환
        if isinstance(from_date, datetime):
            from_date = from_date.date()
        if isinstance(to_date, datetime):
            to_date = to_date.date()

        if from_date and from_date > today:
            return False
        return not (to_date and to_date < today)

    def _deduplicate_consecutive(
        self,
        lines: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """연속된 단계에 동일 결재자가 있으면 상위 단계만 유지한다.

        예: step1 A -> step2 B -> step3 B -> step4 C
            결과: step1 A -> step2 B(상위, 원래 step3) -> step3 C
        단계 번호는 1부터 재정렬된다.
        """
        if not lines:
            return lines

        # step 순으로 정렬
        sorted_lines = sorted(lines, key=lambda line_: int(line_.get("step", 0)))

        # 같은 approver가 연속으로 나오면 상위(뒤쪽) 단계 유지
        deduped: list[dict[str, Any]] = []
        for line in sorted_lines:
            approver = str(line.get("approver", ""))
            if deduped and str(deduped[-1].get("approver", "")) == approver:
                # 상위 단계로 갱신 (approver_role도 상위로)
                deduped[-1] = line
                continue
            deduped.append(line)

        # step 재정렬 (1, 2, 3, ...)
        for idx, line in enumerate(deduped, start=1):
            line["step"] = idx

        return deduped
