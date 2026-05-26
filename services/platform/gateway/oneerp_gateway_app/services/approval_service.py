"""결재 서비스 레이어 — 결재 요청/승인/거절/위임/합의/전결 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-APPR-001: 결재 요청 자동 생성 (ApprovalTemplate -> ApprovalLine)
- BR-APPR-002: 합의 결재 전원 승인 필요
- BR-APPR-003: 합의 결재 1명 거절 시 전체 거절
- BR-APPR-004: 전결 권한 검증 (pre_approval_roles)
- BR-APPR-005: 전결 시 이후 단계 일괄 생략
- BR-APPR-006: 위임 규칙 검증 (DelegationRule)
- BR-APPR-007: 위임 처리 (delegated + 새 pending 라인)
- BR-APPR-008: 단계 완료 판정 (_is_step_complete)
- BR-APPR-009: 최종 승인 판정 (APPROVAL_REQUEST_APPROVED 이벤트)
- BR-APPR-010: 결재 이력 자동 기록 (ApprovalAction)
- BR-APPR-011: 결재자 알림 서비스 호출
- BR-APPR-013: pending/submitted만 처리 가능
- BR-APPR-014: 현재 단계 결재자만 처리 가능
- BR-APPR-015: 결재 취소는 기안자만 가능
- BR-APPR-020: 동일 문서 중복 결재 요청 방지
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from oneerp_core.errors import OneERPError, raise_not_found, raise_unprocessable
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_gateway_app.models.approval_action import ApprovalAction
from oneerp_gateway_app.models.approval_request import ApprovalLineEmbed, ApprovalRequest
from oneerp_gateway_app.services.approval_notification import ApprovalNotificationService

logger = logging.getLogger(__name__)
_ACTION_PREFIX = "AA"


class ApprovalService:
    """전자결재 핵심 비즈니스 로직.

    결재 요청 생성, 승인, 거절, 위임, 합의, 전결 워크플로우를 처리한다.
    모든 메서드는 tenant_id 격리를 보장한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._request_repo = Repository("approval_requests", tenant_id=tenant_id)
        self._template_repo = Repository("approval_templates", tenant_id=tenant_id)
        self._action_repo = Repository("approval_actions", tenant_id=tenant_id)
        self._delegation_repo = Repository("delegation_rules", tenant_id=tenant_id)
        self._notification_service = ApprovalNotificationService(tenant_id=tenant_id)

    # -- 결재 요청 생성 --

    def create_request(
        self,
        document_type: str,
        document_id: str,
        requester: str,
    ) -> dict[str, Any]:
        """BR-APPR-001: 결재 요청을 자동 생성한다.

        1. document_type으로 템플릿 조회
        2. 템플릿의 steps에서 ApprovalLineEmbed 목록 생성
           - consensus 유형이면 approvers 수만큼 라인 생성
        3. ApprovalRequest 생성 및 저장

        Args:
            document_type: 문서 유형 (예: "PurchaseOrder")
            document_id: 대상 문서 ID
            requester: 요청자 ID

        Returns:
            생성된 결재 요청 정보

        Raises:
            OneERPError: 템플릿이 존재하지 않을 때
        """
        # BR-APPR-020: 동일 문서 중복 결재 요청 방지
        existing = self._request_repo.find_many(
            {
                "document_type": document_type,
                "document_id": document_id,
                "status": {"$in": ["pending", "submitted"]},
            },
            limit=1,
        )
        if existing:
            raise_unprocessable("ERR-APR-020", "이미 진행 중인 결재 요청이 있습니다")

        templates = self._template_repo.find_many(
            {"document_type": document_type, "is_active": True},
            limit=1,
        )
        if not templates:
            inactive_templates = self._template_repo.find_many(
                {"document_type": document_type},
                limit=1,
            )
            if inactive_templates:
                raise_unprocessable("ERR-APR-009", "비활성화된 결재 템플릿은 사용할 수 없습니다")
            msg = f"문서 유형 '{document_type}'에 해당하는 결재 템플릿이 없습니다"
            raise_not_found(msg)

        template = templates[0]
        steps = template.get("steps", [])

        # 결재 라인 생성 — consensus 유형은 approvers 각각에 대해 라인 생성
        approval_lines: list[ApprovalLineEmbed] = []
        for step_cfg in steps:
            approval_type = step_cfg.get("approval_type", "single")
            pre_approval_roles = step_cfg.get("pre_approval_roles", [])

            if approval_type == "consensus":
                # 합의 결재: 복수 결재자 각각에 대해 라인 생성
                approvers = step_cfg.get("approvers", [])
                if not approvers:
                    # approvers가 비어있으면 단일 결재자로 폴백
                    approvers = [step_cfg.get("approver", "")]
                approval_lines.extend(
                    ApprovalLineEmbed(
                        step=step_cfg["step"],
                        approver=approver_id,
                        approver_role=step_cfg.get("approver_role", ""),
                        approval_type="consensus",
                        pre_approval_roles=pre_approval_roles,
                    )
                    for approver_id in approvers
                )
            else:
                # 단일 결재
                approval_lines.append(
                    ApprovalLineEmbed(
                        step=step_cfg["step"],
                        approver=step_cfg.get("approver", ""),
                        approver_role=step_cfg.get("approver_role", ""),
                        approval_type="single",
                        pre_approval_roles=pre_approval_roles,
                    )
                )

        request_doc = ApprovalRequest(
            document_type=document_type,
            document_id=document_id,
            requester=requester,
            status="pending",
            current_step=1,
            approval_lines=approval_lines,
            tenant_id=self._tenant_id,
        )

        request_id = self._request_repo.insert(request_doc)
        # 고유 단계 수 계산 (합의 결재는 같은 step에 여러 라인)
        unique_steps = len({line.step for line in approval_lines})
        logger.info(
            "결재 요청 생성: %s (문서: %s/%s, 요청자: %s, 단계: %d)",
            request_id,
            document_type,
            document_id,
            requester,
            unique_steps,
        )
        result = {
            "request_id": request_id,
            "status": "pending",
            "current_step": 1,
            "total_steps": unique_steps,
        }

        # BR-APPR-011: 첫 번째 단계 결재자에게 알림
        first_step_approvers = {line.approver for line in approval_lines if line.step == 1}
        for approver_id in first_step_approvers:
            self._safe_notify(request_id, approver_id, "request")

        return result

    # -- 승인 (합의 결재 지원) --

    def approve(
        self,
        request_id: str,
        approver: str,
        comment: str = "",
    ) -> dict[str, Any]:
        """BR-APPR-002/008/009/013/014: 현재 단계를 승인한다.

        BR-APPR-002: 합의(consensus) 결재 시 전원 승인 필요.
        BR-APPR-008: 단계 완료 판정.
        BR-APPR-009: 최종 단계 완료 시 approved + 이벤트.
        BR-APPR-013: pending/submitted만 처리 가능.
        BR-APPR-014: 현재 단계 결재자만 처리 가능.

        Args:
            request_id: 결재 요청 ID
            approver: 승인자 ID
            comment: 승인 코멘트

        Returns:
            승인 결과 (final_approved 포함)

        Raises:
            OneERPError: 요청 미존재, 이미 완료, 권한 없음 등
        """
        request_doc = self._get_pending_request(request_id)
        current_step = request_doc["current_step"]
        approval_lines = request_doc.get("approval_lines", [])

        # 현재 단계에서 이 결재자의 라인 찾기
        current_line_idx = self._find_approver_line(approval_lines, current_step, approver)

        # 현재 라인 승인 처리
        now = datetime.now(tz=UTC)
        approval_lines[current_line_idx]["status"] = "approved"
        approval_lines[current_line_idx]["comment"] = comment
        approval_lines[current_line_idx]["acted_at"] = now

        # 합의 결재: 동일 단계의 모든 라인이 승인되었는지 확인
        step_complete = self._is_step_complete(approval_lines, current_step)

        update_data: dict[str, Any] = {"approval_lines": approval_lines}
        final_approved = False

        if step_complete:
            # 다음 단계 확인
            next_step_exists = any(line["step"] > current_step for line in approval_lines)
            if next_step_exists:
                update_data["current_step"] = current_step + 1
            else:
                update_data["status"] = "approved"
                final_approved = True

        self._request_repo.update_by_id(request_id, update_data)

        current_line = approval_lines[current_line_idx]
        self._record_action(
            request_id,
            "approve",
            approver,
            comment,
            step=current_step,
            request_status=str(update_data.get("status", request_doc["status"])),
            document_type=request_doc.get("document_type", ""),
            document_id=request_doc.get("document_id", ""),
            approval_type=current_line.get("approval_type", "single"),
        )

        logger.info(
            "결재 승인: %s (단계: %d, 승인자: %s, 단계완료: %s, 최종: %s)",
            request_id,
            current_step,
            approver,
            step_complete,
            final_approved,
        )

        result: dict[str, Any] = {
            "request_id": request_id,
            "approved_step": current_step,
            "step_complete": step_complete,
            "final_approved": final_approved,
        }

        if final_approved:
            result["event_type"] = EventType.APPROVAL_REQUEST_APPROVED

        # BR-APPR-011: 다음 단계 결재자에게 알림
        if step_complete and not final_approved:
            next_step = current_step + 1
            next_approvers = {
                line["approver"]
                for line in approval_lines
                if line["step"] == next_step and line["status"] == "pending"
            }
            for approver_id in next_approvers:
                self._safe_notify(request_id, approver_id, "approve")

        return result

    # -- 거절 --

    def reject(
        self,
        request_id: str,
        approver: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """BR-APPR-003/013/014: 결재를 거절한다.

        BR-APPR-003: 합의 결재 1명 거절 시 전체 거절.

        Args:
            request_id: 결재 요청 ID
            approver: 거절자 ID
            reason: 거절 사유

        Returns:
            거절 결과

        Raises:
            OneERPError: 요청 미존재, 이미 완료, 권한 없음 등
        """
        request_doc = self._get_pending_request(request_id)
        current_step = request_doc["current_step"]
        approval_lines = request_doc.get("approval_lines", [])

        current_line_idx = self._find_approver_line(approval_lines, current_step, approver)

        # 거절 처리
        now = datetime.now(tz=UTC)
        approval_lines[current_line_idx]["status"] = "rejected"
        approval_lines[current_line_idx]["comment"] = reason
        approval_lines[current_line_idx]["acted_at"] = now

        self._request_repo.update_by_id(
            request_id,
            {
                "approval_lines": approval_lines,
                "status": "rejected",
            },
        )

        current_line = approval_lines[current_line_idx]
        self._record_action(
            request_id,
            "reject",
            approver,
            reason,
            step=current_step,
            request_status="rejected",
            document_type=request_doc.get("document_type", ""),
            document_id=request_doc.get("document_id", ""),
            approval_type=current_line.get("approval_type", "single"),
        )

        logger.info(
            "결재 거절: %s (단계: %d, 거절자: %s)",
            request_id,
            current_step,
            approver,
        )

        # BR-APPR-011: 기안자에게 거절 알림
        requester = request_doc.get("requester", "")
        if requester:
            self._safe_notify(request_id, requester, "reject")

        return {
            "request_id": request_id,
            "rejected_step": current_step,
            "status": "rejected",
            "event_type": EventType.APPROVAL_REQUEST_REJECTED,
        }

    # -- 위임 (대결) --

    def delegate(
        self,
        request_id: str,
        delegator: str,
        delegate_to: str,
    ) -> dict[str, Any]:
        """BR-APPR-006/007: 결재를 위임한다.

        BR-APPR-006: 위임 규칙 검증 (DelegationRule).
        BR-APPR-007: 기존 라인 delegated + 새 pending 라인 추가.

        Args:
            request_id: 결재 요청 ID
            delegator: 위임자 ID
            delegate_to: 위임 대상자 ID

        Returns:
            위임 결과

        Raises:
            OneERPError: 요청 미존재, 위임 규칙 없음, 권한 없음 등
        """
        request_doc = self._get_pending_request(request_id)
        self._validate_delegation_rule(delegator, delegate_to)

        current_step = request_doc["current_step"]
        approval_lines = request_doc.get("approval_lines", [])

        # 현재 단계에서 위임자의 라인 찾기
        current_line_idx = self._find_approver_line(approval_lines, current_step, delegator)

        # 기존 라인 delegated 처리 + 새 라인 추가 (단일 DB 업데이트)
        approval_lines[current_line_idx]["status"] = "delegated"
        approval_lines.append(
            {
                "step": current_step,
                "approver": delegate_to,
                "approver_role": approval_lines[current_line_idx].get("approver_role", ""),
                "approval_type": approval_lines[current_line_idx].get("approval_type", "single"),
                "pre_approval_roles": approval_lines[current_line_idx].get(
                    "pre_approval_roles", []
                ),
                "status": "pending",
                "comment": "",
                "acted_at": None,
            }
        )

        self._request_repo.update_by_id(
            request_id,
            {"approval_lines": approval_lines},
        )

        current_line = approval_lines[current_line_idx]
        self._record_action(
            request_id,
            "delegate",
            delegator,
            f"{delegator} → {delegate_to} 위임",
            step=current_step,
            request_status=request_doc.get("status", "pending"),
            document_type=request_doc.get("document_type", ""),
            document_id=request_doc.get("document_id", ""),
            approval_type=current_line.get("approval_type", "single"),
            delegate_to=delegate_to,
        )

        logger.info(
            "결재 위임: %s (단계: %d, %s → %s)",
            request_id,
            current_step,
            delegator,
            delegate_to,
        )

        # BR-APPR-011: 위임 대상자에게 알림
        self._safe_notify(request_id, delegate_to, "delegate")

        return {
            "request_id": request_id,
            "delegated_step": current_step,
            "from": delegator,
            "to": delegate_to,
        }

    # -- 전결 (pre-approval) --

    def pre_approve(
        self,
        request_id: str,
        approver: str,
        approver_roles: tuple[str, ...],
        comment: str = "",
    ) -> dict[str, Any]:
        """BR-APPR-004/005: 전결 — 상위 결재권자가 현재 단계 이후를 건너뛰고 최종 승인한다.

        현재 단계의 pre_approval_roles에 사용자 역할이 포함되어 있어야 한다.
        전결 시 현재 단계 라인은 approved, 이후 단계 라인은 skipped 처리된다.

        Args:
            request_id: 결재 요청 ID
            approver: 전결자 ID
            approver_roles: 전결자의 역할 목록
            comment: 전결 코멘트

        Returns:
            전결 결과

        Raises:
            OneERPError: 요청 미존재, 전결 권한 없음 등
        """
        request_doc = self._get_pending_request(request_id)
        current_step = request_doc["current_step"]
        approval_lines = request_doc.get("approval_lines", [])

        # 현재 단계에서 전결자의 라인 찾기
        current_line_idx = self._find_approver_line(approval_lines, current_step, approver)

        # 전결 권한 확인
        current_line = approval_lines[current_line_idx]
        pre_approval_roles = current_line.get("pre_approval_roles", [])
        if not pre_approval_roles or not (set(approver_roles) & set(pre_approval_roles)):
            msg = (
                f"전결 권한이 없습니다. "
                f"필요 역할: {pre_approval_roles}, 사용자 역할: {list(approver_roles)}"
            )
            raise_unprocessable("ERR-APR-003", msg)

        # 현재 단계 승인 + 이후 단계 skipped 처리
        now = datetime.now(tz=UTC)
        for idx, line in enumerate(approval_lines):
            if line["step"] == current_step and line["approver"] == approver:
                approval_lines[idx]["status"] = "approved"
                approval_lines[idx]["comment"] = comment or "전결"
                approval_lines[idx]["acted_at"] = now
            elif line["step"] == current_step and line["status"] == "pending":
                # 합의 결재의 다른 결재자도 skipped 처리
                approval_lines[idx]["status"] = "skipped"
                approval_lines[idx]["comment"] = "전결로 인한 생략"
                approval_lines[idx]["acted_at"] = now
            elif line["step"] > current_step:
                # 이후 단계 모두 skipped
                approval_lines[idx]["status"] = "skipped"
                approval_lines[idx]["comment"] = "전결로 인한 생략"
                approval_lines[idx]["acted_at"] = now

        self._request_repo.update_by_id(
            request_id,
            {
                "approval_lines": approval_lines,
                "status": "approved",
            },
        )

        self._record_action(
            request_id,
            "pre_approve",
            approver,
            comment or "전결",
            step=current_step,
            request_status="approved",
            document_type=request_doc.get("document_type", ""),
            document_id=request_doc.get("document_id", ""),
            approval_type=current_line.get("approval_type", "single"),
        )

        skipped_steps = sorted(
            {line["step"] for line in approval_lines if line["step"] > current_step}
        )
        logger.info(
            "전결: %s (단계: %d, 전결자: %s, 생략 단계: %s)",
            request_id,
            current_step,
            approver,
            skipped_steps,
        )

        return {
            "request_id": request_id,
            "pre_approved_step": current_step,
            "skipped_steps": skipped_steps,
            "final_approved": True,
            "event_type": EventType.APPROVAL_REQUEST_APPROVED,
        }

    # ========== 내부 헬퍼 ==========

    def _get_pending_request(self, request_id: str) -> dict[str, Any]:
        """대기 중인 결재 요청을 조회한다. 없거나 이미 처리됐으면 에러."""
        request_doc = self._request_repo.find_by_id(request_id)
        if not request_doc:
            msg = f"결재 요청 '{request_id}'을 찾을 수 없습니다"
            raise_not_found(msg)
        request_doc = cast("dict[str, Any]", request_doc)

        if request_doc["status"] not in ("pending", "submitted"):
            msg = f"이미 처리된 결재 요청입니다 (상태: {request_doc['status']})"
            raise_unprocessable("ERR-APR-001", msg)

        return request_doc

    def _find_approver_line(
        self,
        approval_lines: list[dict[str, Any]],
        step: int,
        approver: str,
    ) -> int:
        """현재 단계에서 해당 결재자의 pending 라인 인덱스를 찾는다."""
        for idx, line in enumerate(approval_lines):
            if (
                line["step"] == step
                and line["approver"] == approver
                and line["status"] == "pending"
            ):
                return idx

        # pending 라인이 없으면 결재자 자체가 맞는지 확인하여 에러 메시지 세분화
        has_approver = any(
            line["step"] == step and line["approver"] == approver for line in approval_lines
        )
        if has_approver:
            msg = f"이미 처리된 결재 단계입니다 (단계: {step}, 결재자: {approver})"
        else:
            msg = f"결재 권한이 없습니다 (단계: {step}, 결재자: {approver})"
        raise OneERPError(status_code=422, error="ERR-APR-002", detail=msg)

    def _is_step_complete(
        self,
        approval_lines: list[dict[str, Any]],
        step: int,
    ) -> bool:
        """해당 단계의 모든 라인이 승인(또는 skipped/delegated)인지 확인한다.

        합의 결재: 같은 step의 모든 pending 라인이 없어야 완료.
        delegated 라인은 새 pending 라인이 생기므로 완료에서 제외.
        """
        step_lines = [line for line in approval_lines if line["step"] == step]
        # pending 라인이 하나도 없으면 단계 완료
        return not any(line["status"] == "pending" for line in step_lines)

    def _validate_delegation_rule(
        self,
        delegator: str,
        delegate_to: str,
    ) -> None:
        """BR-APPR-016: 유효한 위임 규칙이 존재하는지 확인한다."""
        today = datetime.now(tz=UTC).date()
        delegation_rules = self._delegation_repo.find_many(
            {
                "delegator": delegator,
                "delegate": delegate_to,
                "is_active": True,
            },
            limit=100,
        )

        for rule in delegation_rules:
            from_date = rule.get("from_date")
            to_date = rule.get("to_date")
            # 날짜 범위 검증 (None이면 제한 없음)
            if (
                from_date
                and (from_date.date() if isinstance(from_date, datetime) else from_date) > today
            ):
                continue
            if to_date and (to_date.date() if isinstance(to_date, datetime) else to_date) < today:
                continue
            return  # 유효한 규칙 발견

        msg = f"'{delegator}'에서 '{delegate_to}'로의 유효한 위임 규칙이 없습니다"
        raise_not_found(msg)

    def _safe_notify(
        self,
        request_id: str,
        recipient: str,
        action_type: str,
    ) -> None:
        """알림을 전송한다. 실패해도 결재 흐름을 방해하지 않는다."""
        try:
            self._notification_service.notify_approver(request_id, recipient, action_type)
        except Exception:
            logger.warning(
                "결재 알림 전송 실패 (무시): request=%s, 수신=%s, 유형=%s",
                request_id,
                recipient,
                action_type,
                exc_info=True,
            )

    def _record_action(
        self,
        request_id: str,
        action_type: str,
        actor: str,
        comment: str,
        *,
        step: int,
        request_status: str,
        document_type: str,
        document_id: str,
        approval_type: str = "single",
        delegate_to: str = "",
    ) -> None:
        """결재 이력을 기록한다."""
        now = datetime.now(tz=UTC)
        action = ApprovalAction(
            _id=generate_name(_ACTION_PREFIX, tenant_id=self._tenant_id),
            approval_request=request_id,
            action_type=action_type,
            actor=actor,
            comment=comment,
            action_date=now.date(),
            acted_at=now,
            step=step,
            request_status=request_status,
            document_type=document_type,
            document_id=document_id,
            approval_type=approval_type,
            delegate_to=delegate_to,
            tenant_id=self._tenant_id,
        )
        self._action_repo.insert(action)
