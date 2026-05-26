"""권한 매트릭스 평가 서비스 — RBAC + ABAC 하이브리드.

L2 비즈니스 룰 매핑:
- BR-APR-030: 권한 매트릭스 평가 (사용자x역할x자원x액션)
- BR-APR-031: 멀티테넌트 격리 강제
- BR-APR-032: 명시적 거부(deny) 우선 평가

핵심 패턴:
1. RBAC: users.roles → role_permissions(role, doctype, action)
2. ABAC: tenant_id, user_tier, ownership 속성 기반 가산 조건
3. Super Admin: super_admin 등급은 모든 권한 허용 (tenant 경계만 유지)
4. Deny 우선: 동일 자원에 allow+deny가 혼재하면 deny 승리
5. 와일드카드: permissions="*:*", doctype="*" 지원

참고 베스트 프랙티스:
- AWS SaaS 멀티테넌트 RBAC/ABAC: gateway 레이어 거친 검사 + 서비스 레이어 세밀 검사
- WorkOS 멀티테넌트 RBAC: tenant-scoped roles + delegated administration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 권한 액션 — RolePermission 모델과 1:1 매핑
_PERMISSION_ACTIONS = {
    "read",
    "write",
    "create",
    "delete",
    "submit",
    "cancel",
    "export",
    "report",
}

# 와일드카드 상수
_WILDCARD = "*"


@dataclass
class PermissionDecision:
    """권한 평가 결과."""

    allowed: bool
    reason: str = ""
    matched_role: str = ""
    denied_by: str = ""
    tenant_scope: str = ""
    applied_rules: list[dict[str, Any]] = field(default_factory=list)


class PermissionMatrixService:
    """권한 매트릭스 평가 서비스.

    사용자의 역할 집합과 자원(doctype)/액션 조합을 받아 허용/거부를 판정한다.
    Super Admin은 자동 허용(테넌트 경계는 유지)하며, 명시적 deny는 최우선으로 적용된다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._role_perm_repo = Repository("role_permissions", tenant_id=tenant_id)
        self._user_repo = Repository("users", tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # BR-APR-030: 권한 매트릭스 평가
    # ------------------------------------------------------------------

    def evaluate(
        self,
        user_id: str,
        doctype: str,
        action: str,
        target_tenant_id: str | None = None,
        resource_owner: str | None = None,
    ) -> PermissionDecision:
        """BR-APR-030: 사용자x역할x자원x액션 조합의 허용 여부를 평가한다.

        평가 순서:
        1. 액션 유효성 검사 (read/write/create/delete/submit/cancel/export/report)
        2. 테넌트 경계 검사 (BR-APR-031) — target_tenant != 사용자 테넌트이면 거부 (super_admin 예외)
        3. 사용자 조회 + 비활성 체크
        4. Super Admin 즉시 허용
        5. 사용자 역할 집합 수집
        6. 역할별 RolePermission 조회 → 명시적 deny 스캔
        7. 와일드카드/정확 매치로 allow 결정

        Args:
            user_id: 평가 대상 사용자 ID
            doctype: 자원 유형 (예: "PurchaseOrder", "Lead")
            action: 액션 (read/write/create/delete/...)
            target_tenant_id: 접근하려는 테넌트 ID (None이면 현재 테넌트)
            resource_owner: 자원 소유자 ID (ownership 기반 평가 시 사용)

        Returns:
            PermissionDecision — allowed, reason, matched_role, denied_by
        """
        # 1) 액션 검증
        if action not in _PERMISSION_ACTIONS:
            return PermissionDecision(
                allowed=False,
                reason=f"알 수 없는 액션: '{action}'",
                tenant_scope=self._tenant_id,
            )

        # 2) 테넌트 경계 검사
        effective_target = target_tenant_id or self._tenant_id
        if effective_target != self._tenant_id:
            # 사용자가 super_admin이면 교차 테넌트 허용
            user = self._user_repo.find_by_id(user_id)
            if not user or user.get("user_tier") != "super_admin":
                return PermissionDecision(
                    allowed=False,
                    reason=f"테넌트 경계 위반: 요청={effective_target}, 현재={self._tenant_id}",
                    tenant_scope=effective_target,
                )

        # 3) 사용자 조회
        user_doc = self._user_repo.find_by_id(user_id)
        if not user_doc:
            return PermissionDecision(
                allowed=False,
                reason=f"사용자 '{user_id}'를 찾을 수 없습니다",
                tenant_scope=self._tenant_id,
            )

        if not user_doc.get("is_active", True):
            return PermissionDecision(
                allowed=False,
                reason=f"비활성 사용자: '{user_id}'",
                tenant_scope=self._tenant_id,
            )

        # 4) Super Admin 즉시 허용
        if (
            bool(user_doc.get("is_super_admin", False))
            or user_doc.get("user_tier") == "super_admin"
        ):
            return PermissionDecision(
                allowed=True,
                reason="super_admin 권한",
                matched_role="super_admin",
                tenant_scope=effective_target,
            )

        # 5) 사용자 역할 집합 (기본 role + roles 목록)
        roles: set[str] = set()
        if user_doc.get("role"):
            roles.add(str(user_doc["role"]))
        for role in user_doc.get("roles", []) or []:
            roles.add(str(role))

        if not roles:
            return PermissionDecision(
                allowed=False,
                reason="사용자에게 역할이 할당되지 않았습니다",
                tenant_scope=effective_target,
            )

        # 6) 역할별 권한 매트릭스 조회 및 평가
        return self._evaluate_roles(
            roles=roles,
            doctype=doctype,
            action=action,
            user_id=user_id,
            resource_owner=resource_owner,
            tenant_scope=effective_target,
        )

    # ------------------------------------------------------------------
    # BR-APR-032: 역할 권한 평가 (deny 우선)
    # ------------------------------------------------------------------

    def _evaluate_roles(
        self,
        roles: set[str],
        doctype: str,
        action: str,
        user_id: str,
        resource_owner: str | None,
        tenant_scope: str,
    ) -> PermissionDecision:
        """사용자의 역할 집합에 대해 doctypexaction 권한을 평가한다.

        - 동일 (role, doctype) 쌍에 대해 명시적 deny가 있으면 최우선 거부
        - allow는 와일드카드도 허용 (doctype="*")
        - 소유자 기반: resource_owner == user_id이면 owner scope 가중치
        """
        applied_rules: list[dict[str, Any]] = []
        deny_found: dict[str, Any] | None = None
        allow_found: dict[str, Any] | None = None
        matched_role: str = ""

        for role in roles:
            rules = self._role_perm_repo.find_many(
                {
                    "$or": [
                        {"role": role, "doctype": doctype},
                        {"role": role, "doctype": _WILDCARD},
                    ]
                },
                limit=100,
            )

            for rule in rules:
                applied_rules.append(
                    {
                        "role": role,
                        "doctype": rule.get("doctype", ""),
                        "effect": "deny" if rule.get("deny", False) else "allow",
                    }
                )

                # 명시적 deny 체크
                if bool(rule.get("deny", False)) and self._rule_grants(rule, action):
                    deny_found = {"rule": rule, "role": role}
                    break

                # allow 체크 (첫 매치만 기록)
                if (
                    not bool(rule.get("deny", False))
                    and self._rule_grants(rule, action)
                    and allow_found is None
                ):
                    allow_found = rule
                    matched_role = role

            if deny_found:
                break

        if deny_found:
            return PermissionDecision(
                allowed=False,
                reason=f"명시적 거부 (role={deny_found['role']}, doctype={doctype}, action={action})",
                denied_by=str(deny_found["role"]),
                tenant_scope=tenant_scope,
                applied_rules=applied_rules,
            )

        if allow_found:
            # ownership 가산 기록 (정책 평가에는 영향 없지만 로깅용)
            ownership_note = ""
            if resource_owner and resource_owner == user_id:
                ownership_note = " (owner)"
            return PermissionDecision(
                allowed=True,
                reason=f"역할 '{matched_role}' 권한 매치{ownership_note}",
                matched_role=matched_role,
                tenant_scope=tenant_scope,
                applied_rules=applied_rules,
            )

        return PermissionDecision(
            allowed=False,
            reason=f"권한 규칙 미매치 (roles={sorted(roles)}, doctype={doctype}, action={action})",
            tenant_scope=tenant_scope,
            applied_rules=applied_rules,
        )

    def _rule_grants(self, rule: dict[str, Any], action: str) -> bool:
        """RolePermission 규칙이 특정 action을 허용하는지 확인한다."""
        return bool(rule.get(action, False))

    # ------------------------------------------------------------------
    # 벌크 평가 — 여러 자원/액션을 한 번에 평가
    # ------------------------------------------------------------------

    def evaluate_bulk(
        self,
        user_id: str,
        checks: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """복수 (doctype, action) 쌍을 한 번에 평가한다.

        Args:
            user_id: 대상 사용자 ID
            checks: [{"doctype": "Lead", "action": "read"}, ...]

        Returns:
            각 체크에 대한 {"doctype", "action", "allowed", "reason"} 목록
        """
        results: list[dict[str, Any]] = []
        for check in checks:
            doctype = str(check.get("doctype", ""))
            action = str(check.get("action", ""))
            decision = self.evaluate(user_id, doctype, action)
            results.append(
                {
                    "doctype": doctype,
                    "action": action,
                    "allowed": decision.allowed,
                    "reason": decision.reason,
                    "matched_role": decision.matched_role,
                }
            )
        return results
