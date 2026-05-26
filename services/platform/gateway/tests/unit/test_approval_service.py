"""결재 서비스 레이어(ApprovalService) 단위 테스트.

커버 시나리오:
- 결재 요청 생성 (단일/다단계/합의)
- 승인 (단일/다단계/합의)
- 거절 (단일/합의 — 1명 거절 시 전체 거절)
- 위임 (대결)
- 전결
- 결재 이력 기록
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError

# -- 헬퍼: ApprovalService 인스턴스를 Repository 모킹과 함께 생성 --


def _make_service() -> tuple:
    """ApprovalService와 모킹된 Repository 인스턴스들을 반환한다.

    Returns:
        (service, request_repo, template_repo, action_repo, delegation_repo)
    """
    with (
        patch("oneerp_gateway_app.services.approval_service.Repository") as mock_repo_cls,
        patch(
            "oneerp_gateway_app.services.approval_service.ApprovalNotificationService"
        ) as mock_notif_cls,
    ):
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        mock_notif = MagicMock()
        mock_notif_cls.return_value = mock_notif

        from oneerp_gateway_app.services.approval_service import ApprovalService

        service = ApprovalService(tenant_id="test-tenant")

    return (
        service,
        repos["approval_requests"],
        repos["approval_templates"],
        repos["approval_actions"],
        repos["delegation_rules"],
        mock_notif,
    )


# -- 템플릿 조회 결과 헬퍼 --


def _template_with_steps(steps: list[dict]) -> dict:
    """템플릿 조회 결과를 생성한다."""
    return {
        "_id": "AT-001",
        "template_name": "구매 결재",
        "document_type": "PurchaseOrder",
        "steps": steps,
    }


def _single_step_template() -> dict:
    return _template_with_steps(
        [
            {"step": 1, "approver_role": "team_lead", "approver": "user-lead"},
        ]
    )


def _two_step_template() -> dict:
    return _template_with_steps(
        [
            {"step": 1, "approver_role": "team_lead", "approver": "user-lead"},
            {"step": 2, "approver_role": "cfo", "approver": "user-cfo"},
        ]
    )


def _consensus_template() -> dict:
    """합의 결재 템플릿 — 1단계에 3명의 결재자."""
    return _template_with_steps(
        [
            {
                "step": 1,
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "approvers": ["user-a", "user-b", "user-c"],
            },
        ]
    )


def _consensus_two_step_template() -> dict:
    """합의 결재 1단계 + 단일 결재 2단계."""
    return _template_with_steps(
        [
            {
                "step": 1,
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "approvers": ["user-a", "user-b"],
            },
            {
                "step": 2,
                "approver_role": "cfo",
                "approver": "user-cfo",
            },
        ]
    )


def _pre_approval_template() -> dict:
    """전결 가능 템플릿 — 3단계, 1단계에서 ceo 역할이 전결 가능."""
    return _template_with_steps(
        [
            {
                "step": 1,
                "approver_role": "team_lead",
                "approver": "user-lead",
                "pre_approval_roles": ["ceo", "coo"],
            },
            {
                "step": 2,
                "approver_role": "director",
                "approver": "user-director",
            },
            {
                "step": 3,
                "approver_role": "cfo",
                "approver": "user-cfo",
            },
        ]
    )


def _pending_request_doc(
    request_id: str = "AR-001",
    current_step: int = 1,
    approval_lines: list[dict] | None = None,
) -> dict:
    """대기 중인 결재 요청 문서를 생성한다."""
    if approval_lines is None:
        approval_lines = [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
    return {
        "_id": request_id,
        "document_type": "PurchaseOrder",
        "document_id": "PO-001",
        "requester": "홍길동",
        "status": "pending",
        "current_step": current_step,
        "approval_lines": approval_lines,
        "tenant_id": "test-tenant",
    }


# ========== 결재 요청 생성 ==========


class Test결재요청생성:
    """create_request 메서드 테스트."""

    def test_결재요청_생성_성공(self) -> None:
        """템플릿이 존재할 때 결재 요청이 정상 생성된다."""
        service, req_repo, tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_many.return_value = []  # 중복 없음
        tmpl_repo.find_many.return_value = [_single_step_template()]
        req_repo.insert.return_value = "AR-001"

        result = service.create_request(
            document_type="PurchaseOrder",
            document_id="PO-001",
            requester="홍길동",
        )

        assert result["request_id"] == "AR-001"
        assert result["status"] == "pending"
        assert result["current_step"] == 1
        assert result["total_steps"] == 1
        req_repo.insert.assert_called_once()

    def test_템플릿_미존재시_에러(self) -> None:
        """document_type에 해당하는 템플릿이 없으면 OneERPError 발생."""
        service, _req_repo, tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        _req_repo.find_many.return_value = []  # 중복 없음
        tmpl_repo.find_many.return_value = []

        with pytest.raises(OneERPError, match="not_found"):
            service.create_request(
                document_type="UnknownType",
                document_id="XX-001",
                requester="홍길동",
            )

    def test_비활성_템플릿은_결재요청_생성에_사용되지_않음(self) -> None:
        """비활성 템플릿만 있으면 결재 요청 생성이 거부된다."""
        service, req_repo, tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_many.return_value = []

        inactive_template = _single_step_template() | {"is_active": False}

        def _template_lookup(query: dict, **_: object) -> list[dict]:
            if query.get("is_active") is True:
                return []
            return [inactive_template]

        tmpl_repo.find_many.side_effect = _template_lookup

        with pytest.raises(OneERPError, match="ERR-APR-009"):
            service.create_request(
                document_type="PurchaseOrder",
                document_id="PO-002",
                requester="홍길동",
            )

    def test_다단계_템플릿_결재라인_생성(self) -> None:
        """2단계 템플릿으로 생성 시 total_steps가 2이다."""
        service, req_repo, tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_many.return_value = []  # 중복 없음
        tmpl_repo.find_many.return_value = [_two_step_template()]
        req_repo.insert.return_value = "AR-002"

        result = service.create_request(
            document_type="PurchaseOrder",
            document_id="PO-002",
            requester="홍길동",
        )

        assert result["total_steps"] == 2
        inserted_doc = req_repo.insert.call_args[0][0]
        assert len(inserted_doc.approval_lines) == 2
        assert inserted_doc.approval_lines[0].step == 1
        assert inserted_doc.approval_lines[1].step == 2

    def test_합의_결재_템플릿_라인_생성(self) -> None:
        """합의 결재 템플릿은 approvers 수만큼 라인을 생성한다."""
        service, req_repo, tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_many.return_value = []  # 중복 없음
        tmpl_repo.find_many.return_value = [_consensus_template()]
        req_repo.insert.return_value = "AR-003"

        result = service.create_request(
            document_type="PurchaseOrder",
            document_id="PO-003",
            requester="홍길동",
        )

        # 합의 결재: 3명이 같은 단계이므로 total_steps=1
        assert result["total_steps"] == 1
        inserted_doc = req_repo.insert.call_args[0][0]
        # 라인은 3개 (approvers 3명)
        assert len(inserted_doc.approval_lines) == 3
        assert all(line.step == 1 for line in inserted_doc.approval_lines)
        assert all(line.approval_type == "consensus" for line in inserted_doc.approval_lines)
        approvers = [line.approver for line in inserted_doc.approval_lines]
        assert approvers == ["user-a", "user-b", "user-c"]


# ========== 승인 ==========


class Test결재승인:
    """approve 메서드 테스트."""

    def test_단일단계_승인_최종승인(self) -> None:
        """단일 단계 결재에서 승인하면 최종 승인이 된다."""
        service, req_repo, _tmpl_repo, action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()

        result = service.approve(
            request_id="AR-001",
            approver="user-lead",
            comment="승인합니다",
        )

        assert result["final_approved"] is True
        assert result["approved_step"] == 1
        assert result["step_complete"] is True
        update_call = req_repo.update_by_id.call_args
        assert update_call[0][0] == "AR-001"
        assert update_call[0][1]["status"] == "approved"
        action_repo.insert.assert_called_once()

    def test_다단계_1단계_승인_진행(self) -> None:
        """2단계 중 1단계 승인 시 다음 단계로 진행한다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        two_step_lines = [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 2,
                "approver": "user-cfo",
                "approver_role": "cfo",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=two_step_lines,
        )

        result = service.approve(request_id="AR-001", approver="user-lead")

        assert result["final_approved"] is False
        assert result["step_complete"] is True
        assert result["approved_step"] == 1
        update_data = req_repo.update_by_id.call_args[0][1]
        assert update_data["current_step"] == 2
        assert "status" not in update_data

    def test_다단계_2단계_승인_최종승인(self) -> None:
        """2단계 중 2단계 승인 시 최종 승인이 된다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        two_step_lines = [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "approved",
                "comment": "OK",
                "acted_at": datetime.now(tz=UTC),
            },
            {
                "step": 2,
                "approver": "user-cfo",
                "approver_role": "cfo",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            current_step=2,
            approval_lines=two_step_lines,
        )

        result = service.approve(
            request_id="AR-001",
            approver="user-cfo",
            comment="최종 승인",
        )

        assert result["final_approved"] is True
        update_data = req_repo.update_by_id.call_args[0][1]
        assert update_data["status"] == "approved"

    def test_권한없는_사용자_승인시_에러(self) -> None:
        """현재 단계 결재자가 아닌 사용자가 승인 시도하면 에러."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()

        with pytest.raises(OneERPError, match="ERR-APR-002"):
            service.approve(request_id="AR-001", approver="unauthorized-user")

    def test_이미처리된_요청_승인시_에러(self) -> None:
        """이미 승인/거절된 요청에 대해 승인 시도하면 에러."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        doc = _pending_request_doc()
        doc["status"] = "approved"
        req_repo.find_by_id.return_value = doc

        with pytest.raises(OneERPError, match="ERR-APR-001"):
            service.approve(request_id="AR-001", approver="user-lead")

    def test_미존재_요청_승인시_에러(self) -> None:
        """존재하지 않는 요청 ID로 승인 시도하면 에러."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.approve(request_id="AR-999", approver="user-lead")


# ========== 합의 결재 ==========


class Test합의결재:
    """합의(consensus) 결재 시나리오 테스트."""

    def _consensus_lines(self) -> list[dict]:
        """합의 결재 라인 3명 (모두 step=1)."""
        return [
            {
                "step": 1,
                "approver": "user-a",
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 1,
                "approver": "user-b",
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 1,
                "approver": "user-c",
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]

    def test_합의_1명승인_단계미완료(self) -> None:
        """3명 중 1명만 승인하면 단계가 완료되지 않는다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=self._consensus_lines(),
        )

        result = service.approve(request_id="AR-001", approver="user-a")

        assert result["step_complete"] is False
        assert result["final_approved"] is False

    def test_합의_전원승인_단계완료(self) -> None:
        """3명 모두 승인하면 단계가 완료되고 최종 승인된다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()

        lines = self._consensus_lines()
        # user-a, user-b 이미 승인 상태
        lines[0]["status"] = "approved"
        lines[0]["acted_at"] = datetime.now(tz=UTC)
        lines[1]["status"] = "approved"
        lines[1]["acted_at"] = datetime.now(tz=UTC)

        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=lines,
        )

        # 마지막 user-c 승인
        result = service.approve(request_id="AR-001", approver="user-c")

        assert result["step_complete"] is True
        assert result["final_approved"] is True

    def test_합의_2명승인_1명남음_미완료(self) -> None:
        """3명 중 2명 승인, 1명 남은 상태는 미완료."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()

        lines = self._consensus_lines()
        lines[0]["status"] = "approved"

        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=lines,
        )

        result = service.approve(request_id="AR-001", approver="user-b")

        assert result["step_complete"] is False
        assert result["final_approved"] is False

    def test_합의후_다음단계_진행(self) -> None:
        """합의 결재 완료 후 다음 단계로 진행한다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()

        lines = [
            {
                "step": 1,
                "approver": "user-a",
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "pre_approval_roles": [],
                "status": "approved",
                "comment": "",
                "acted_at": datetime.now(tz=UTC),
            },
            {
                "step": 1,
                "approver": "user-b",
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 2,
                "approver": "user-cfo",
                "approver_role": "cfo",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=lines,
        )

        result = service.approve(request_id="AR-001", approver="user-b")

        assert result["step_complete"] is True
        assert result["final_approved"] is False
        update_data = req_repo.update_by_id.call_args[0][1]
        assert update_data["current_step"] == 2

    def test_합의_1명거절_전체거절(self) -> None:
        """합의 결재에서 1명이 거절하면 전체 요청이 거절된다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=self._consensus_lines(),
        )

        result = service.reject(
            request_id="AR-001",
            approver="user-b",
            reason="동의 불가",
        )

        assert result["status"] == "rejected"
        update_data = req_repo.update_by_id.call_args[0][1]
        assert update_data["status"] == "rejected"


# ========== 거절 ==========


class Test결재거절:
    """reject 메서드 테스트."""

    def test_거절_성공(self) -> None:
        """정상 거절 시 status가 rejected로 변경된다."""
        service, req_repo, _tmpl_repo, action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()

        result = service.reject(
            request_id="AR-001",
            approver="user-lead",
            reason="예산 초과",
        )

        assert result["status"] == "rejected"
        assert result["rejected_step"] == 1
        update_data = req_repo.update_by_id.call_args[0][1]
        assert update_data["status"] == "rejected"
        action_doc = action_repo.insert.call_args[0][0]
        assert action_doc.action_type == "reject"
        assert action_doc.comment == "예산 초과"

    def test_권한없는_사용자_거절시_에러(self) -> None:
        """현재 단계 결재자가 아닌 사용자가 거절 시도하면 에러."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()

        with pytest.raises(OneERPError, match="ERR-APR-002"):
            service.reject(
                request_id="AR-001",
                approver="unauthorized-user",
                reason="거절",
            )


# ========== 위임 (대결) ==========


class Test결재위임:
    """delegate 메서드 테스트."""

    def test_위임_성공(self) -> None:
        """유효한 위임 규칙이 있을 때 결재자가 변경된다."""
        service, req_repo, _tmpl_repo, action_repo, del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()
        del_repo.find_many.return_value = [
            {
                "_id": "DR-001",
                "delegator": "user-lead",
                "delegate": "user-deputy",
                "from_date": date(2026, 1, 1),
                "to_date": date(2026, 12, 31),
                "is_active": True,
            },
        ]

        result = service.delegate(
            request_id="AR-001",
            delegator="user-lead",
            delegate_to="user-deputy",
        )

        assert result["from"] == "user-lead"
        assert result["to"] == "user-deputy"
        assert result["delegated_step"] == 1
        # DB 업데이트 1회만 호출 (버그 수정 검증)
        assert req_repo.update_by_id.call_count == 1
        # 결재 이력 기록 검증
        action_doc = action_repo.insert.call_args[0][0]
        assert action_doc.action_type == "delegate"

    def test_위임후_새라인_pending(self) -> None:
        """위임 시 기존 라인은 delegated, 새 라인이 pending으로 추가된다."""
        service, req_repo, _tmpl_repo, _action_repo, del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()
        del_repo.find_many.return_value = [
            {
                "_id": "DR-001",
                "delegator": "user-lead",
                "delegate": "user-deputy",
                "from_date": None,
                "to_date": None,
                "is_active": True,
            },
        ]

        service.delegate(
            request_id="AR-001",
            delegator="user-lead",
            delegate_to="user-deputy",
        )

        update_data = req_repo.update_by_id.call_args[0][1]
        lines = update_data["approval_lines"]
        # 기존 라인 delegated + 새 라인 pending = 2개
        assert len(lines) == 2
        assert lines[0]["status"] == "delegated"
        assert lines[1]["approver"] == "user-deputy"
        assert lines[1]["status"] == "pending"

    def test_위임규칙_없을때_에러(self) -> None:
        """유효한 위임 규칙이 없으면 에러."""
        service, req_repo, _tmpl_repo, _action_repo, del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()
        del_repo.find_many.return_value = []

        with pytest.raises(OneERPError, match="not_found"):
            service.delegate(
                request_id="AR-001",
                delegator="user-lead",
                delegate_to="user-deputy",
            )

    def test_위임자가_결재자가_아닐때_에러(self) -> None:
        """위임자가 현재 단계의 결재자가 아니면 에러."""
        service, req_repo, _tmpl_repo, _action_repo, del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()
        del_repo.find_many.return_value = [
            {
                "_id": "DR-002",
                "delegator": "other-user",
                "delegate": "user-deputy",
                "from_date": None,
                "to_date": None,
                "is_active": True,
            },
        ]

        with pytest.raises(OneERPError, match="ERR-APR-002"):
            service.delegate(
                request_id="AR-001",
                delegator="other-user",
                delegate_to="user-deputy",
            )


# ========== 전결 ==========


class Test전결:
    """pre_approve 메서드 테스트."""

    def _pre_approval_lines(self) -> list[dict]:
        """전결 가능 3단계 라인."""
        return [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": ["ceo", "coo"],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 2,
                "approver": "user-director",
                "approver_role": "director",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 3,
                "approver": "user-cfo",
                "approver_role": "cfo",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]

    def test_전결_성공(self) -> None:
        """전결 권한이 있는 사용자가 전결하면 최종 승인된다."""
        service, req_repo, _tmpl_repo, action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=self._pre_approval_lines(),
        )

        result = service.pre_approve(
            request_id="AR-001",
            approver="user-lead",
            approver_roles=("ceo",),
            comment="CEO 전결",
        )

        assert result["final_approved"] is True
        assert result["pre_approved_step"] == 1
        assert result["skipped_steps"] == [2, 3]  # 2단계, 3단계 생략 (배열)

        # DB 업데이트 검증
        update_data = req_repo.update_by_id.call_args[0][1]
        assert update_data["status"] == "approved"
        lines = update_data["approval_lines"]
        assert lines[0]["status"] == "approved"
        assert lines[1]["status"] == "skipped"
        assert lines[2]["status"] == "skipped"
        assert "전결로 인한 생략" in lines[1]["comment"]

        # 결재 이력 검증
        action_doc = action_repo.insert.call_args[0][0]
        assert action_doc.action_type == "pre_approve"

    def test_전결_권한없음_에러(self) -> None:
        """전결 권한이 없는 사용자가 전결 시도하면 에러."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=self._pre_approval_lines(),
        )

        with pytest.raises(OneERPError, match="ERR-APR-003"):
            service.pre_approve(
                request_id="AR-001",
                approver="user-lead",
                approver_roles=("team_lead",),  # ceo/coo 아님
            )

    def test_전결_역할없음_에러(self) -> None:
        """pre_approval_roles가 비어있으면 전결 불가."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        lines = [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": [],  # 전결 미허용
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=lines,
        )

        with pytest.raises(OneERPError, match="ERR-APR-003"):
            service.pre_approve(
                request_id="AR-001",
                approver="user-lead",
                approver_roles=("ceo",),
            )

    def test_전결시_합의_결재_다른결재자_skipped(self) -> None:
        """합의 결재 단계에서 전결 시 같은 단계 다른 결재자도 skipped."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        lines = [
            {
                "step": 1,
                "approver": "user-a",
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "pre_approval_roles": ["ceo"],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 1,
                "approver": "user-b",
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 2,
                "approver": "user-cfo",
                "approver_role": "cfo",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=lines,
        )

        result = service.pre_approve(
            request_id="AR-001",
            approver="user-a",
            approver_roles=("ceo",),
        )

        assert result["final_approved"] is True
        update_data = req_repo.update_by_id.call_args[0][1]
        updated_lines = update_data["approval_lines"]
        assert updated_lines[0]["status"] == "approved"  # user-a
        assert updated_lines[1]["status"] == "skipped"  # user-b (같은 단계)
        assert updated_lines[2]["status"] == "skipped"  # user-cfo (다음 단계)


# ========== 결재 이력 ==========


class Test결재이력검증:
    """결재 이력(ApprovalAction) 기록 검증 테스트."""

    def test_승인시_이력기록(self) -> None:
        """승인 시 ApprovalAction이 올바르게 기록된다."""
        service, req_repo, _tmpl_repo, action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()

        service.approve(request_id="AR-001", approver="user-lead", comment="OK")

        action_doc = action_repo.insert.call_args[0][0]
        assert action_doc.id.startswith("AA-")
        assert action_doc.approval_request == "AR-001"
        assert action_doc.action_type == "approve"
        assert action_doc.actor == "user-lead"
        assert action_doc.comment == "OK"
        assert action_doc.action_date is not None
        assert action_doc.acted_at is not None
        assert action_doc.step == 1
        assert action_doc.request_status == "approved"
        assert action_doc.document_type == "PurchaseOrder"
        assert action_doc.document_id == "PO-001"

    def test_거절시_이력기록(self) -> None:
        """거절 시 ApprovalAction이 올바르게 기록된다."""
        service, req_repo, _tmpl_repo, action_repo, _del_repo, _notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()

        service.reject(request_id="AR-001", approver="user-lead", reason="불가")

        action_doc = action_repo.insert.call_args[0][0]
        assert action_doc.approval_request == "AR-001"
        assert action_doc.action_type == "reject"
        assert action_doc.actor == "user-lead"
        assert action_doc.comment == "불가"
        assert action_doc.request_status == "rejected"

    def test_전결시_이력기록(self) -> None:
        """전결 시 ApprovalAction이 pre_approve로 기록된다."""
        service, req_repo, _tmpl_repo, action_repo, _del_repo, _notif = _make_service()
        lines = [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": ["ceo"],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=lines,
        )

        service.pre_approve(
            request_id="AR-001",
            approver="user-lead",
            approver_roles=("ceo",),
            comment="긴급 전결",
        )

        action_doc = action_repo.insert.call_args[0][0]
        assert action_doc.action_type == "pre_approve"
        assert action_doc.comment == "긴급 전결"
        assert action_doc.request_status == "approved"
        assert action_doc.approval_type == "single"

    def test_위임시_이력에_수임자와_현재단계가_기록된다(self) -> None:
        """위임 이력에는 수임자와 단계/문서 메타데이터가 남아야 한다."""
        service, req_repo, _tmpl_repo, action_repo, del_repo, _notif = _make_service()
        del_repo.find_many.return_value = [
            {
                "delegator": "user-lead",
                "delegate": "delegate-001",
                "is_active": True,
                "from_date": date(2026, 1, 1),
                "to_date": date(2026, 12, 31),
            }
        ]
        req_repo.find_by_id.return_value = _pending_request_doc()

        service.delegate(
            request_id="AR-001",
            delegator="user-lead",
            delegate_to="delegate-001",
        )

        action_doc = action_repo.insert.call_args[0][0]
        assert action_doc.action_type == "delegate"
        assert action_doc.step == 1
        assert action_doc.delegate_to == "delegate-001"
        assert action_doc.request_status == "pending"
        assert action_doc.document_type == "PurchaseOrder"


# ========== 버그 수정 검증 ==========


class Test_submitted_상태_결재처리:
    """버그1: submitted 상태에서도 결재 처리가 가능해야 한다 (BR-APPR-013)."""

    def test_submitted_상태_승인_성공(self) -> None:
        """submitted 상태의 결재 요청도 승인할 수 있다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        doc = _pending_request_doc()
        doc["status"] = "submitted"
        req_repo.find_by_id.return_value = doc

        result = service.approve(request_id="AR-001", approver="user-lead")

        assert result["final_approved"] is True

    def test_submitted_상태_거절_성공(self) -> None:
        """submitted 상태의 결재 요청도 거절할 수 있다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        doc = _pending_request_doc()
        doc["status"] = "submitted"
        req_repo.find_by_id.return_value = doc

        result = service.reject(request_id="AR-001", approver="user-lead", reason="불가")

        assert result["status"] == "rejected"

    def test_cancelled_상태_승인_불가(self) -> None:
        """cancelled 상태의 결재 요청은 처리할 수 없다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        doc = _pending_request_doc()
        doc["status"] = "cancelled"
        req_repo.find_by_id.return_value = doc

        with pytest.raises(OneERPError, match="ERR-APR-001"):
            service.approve(request_id="AR-001", approver="user-lead")


class Test전결_skipped_steps_배열반환:
    """버그3: pre_approve의 skipped_steps가 정수가 아닌 배열을 반환해야 한다."""

    def test_skipped_steps_배열_타입(self) -> None:
        """skipped_steps가 list 타입이어야 한다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        lines = [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": ["ceo"],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 2,
                "approver": "user-director",
                "approver_role": "director",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 3,
                "approver": "user-cfo",
                "approver_role": "cfo",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=lines,
        )

        result = service.pre_approve(
            request_id="AR-001",
            approver="user-lead",
            approver_roles=("ceo",),
        )

        assert isinstance(result["skipped_steps"], list)
        assert result["skipped_steps"] == [2, 3]

    def test_skipped_steps_단일단계_빈배열(self) -> None:
        """이후 단계가 없으면 빈 배열을 반환한다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        lines = [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": ["ceo"],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=lines,
        )

        result = service.pre_approve(
            request_id="AR-001",
            approver="user-lead",
            approver_roles=("ceo",),
        )

        assert result["skipped_steps"] == []


# ========== BR-APPR-020: 동일 문서 중복 결재 요청 방지 ==========


class Test중복결재요청방지:
    """BR-APPR-020: 동일 문서에 대해 진행 중인 결재 요청이 있으면 중복 생성 불가."""

    def test_중복_결재요청_거부(self) -> None:
        """pending 상태의 동일 문서 결재 요청이 있으면 에러."""
        service, req_repo, tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_many.return_value = [{"_id": "AR-EXISTING", "status": "pending"}]

        with pytest.raises(OneERPError, match="ERR-APR-020"):
            service.create_request(
                document_type="PurchaseOrder",
                document_id="PO-001",
                requester="홍길동",
            )

        # 템플릿 조회·insert가 호출되지 않아야 한다
        tmpl_repo.find_many.assert_not_called()
        req_repo.insert.assert_not_called()

    def test_완료된_요청은_중복아님(self) -> None:
        """approved/rejected 상태의 동일 문서는 중복이 아니므로 생성 가능."""
        service, req_repo, tmpl_repo, _action_repo, _del_repo, _notif = _make_service()
        req_repo.find_many.return_value = []  # 진행 중인 요청 없음
        tmpl_repo.find_many.return_value = [_single_step_template()]
        req_repo.insert.return_value = "AR-NEW"

        result = service.create_request(
            document_type="PurchaseOrder",
            document_id="PO-001",
            requester="홍길동",
        )

        assert result["request_id"] == "AR-NEW"


# ========== BR-APPR-011: 결재자 알림 서비스 호출 ==========


class Test결재알림호출:
    """BR-APPR-011: 각 결재 액션 후 적절한 대상에게 알림이 전송된다."""

    def test_생성시_첫단계_결재자_알림(self) -> None:
        """결재 요청 생성 후 첫 번째 단계 결재자에게 알림."""
        service, req_repo, tmpl_repo, _action_repo, _del_repo, notif = _make_service()
        req_repo.find_many.return_value = []
        tmpl_repo.find_many.return_value = [_single_step_template()]
        req_repo.insert.return_value = "AR-001"

        service.create_request(
            document_type="PurchaseOrder",
            document_id="PO-001",
            requester="홍길동",
        )

        notif.notify_approver.assert_called_once_with("AR-001", "user-lead", "request")

    def test_생성시_합의결재_모든결재자_알림(self) -> None:
        """합의 결재 생성 후 첫 단계의 모든 결재자에게 알림."""
        service, req_repo, tmpl_repo, _action_repo, _del_repo, notif = _make_service()
        req_repo.find_many.return_value = []
        tmpl_repo.find_many.return_value = [_consensus_template()]
        req_repo.insert.return_value = "AR-002"

        service.create_request(
            document_type="PurchaseOrder",
            document_id="PO-002",
            requester="홍길동",
        )

        assert notif.notify_approver.call_count == 3
        called_approvers = {call.args[1] for call in notif.notify_approver.call_args_list}
        assert called_approvers == {"user-a", "user-b", "user-c"}

    def test_승인후_다음단계_결재자_알림(self) -> None:
        """단계 완료 후 다음 단계 결재자에게 알림."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, notif = _make_service()
        two_step_lines = [
            {
                "step": 1,
                "approver": "user-lead",
                "approver_role": "team_lead",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
            {
                "step": 2,
                "approver": "user-cfo",
                "approver_role": "cfo",
                "approval_type": "single",
                "pre_approval_roles": [],
                "status": "pending",
                "comment": "",
                "acted_at": None,
            },
        ]
        req_repo.find_by_id.return_value = _pending_request_doc(
            approval_lines=two_step_lines,
        )

        service.approve(request_id="AR-001", approver="user-lead")

        notif.notify_approver.assert_called_once_with("AR-001", "user-cfo", "approve")

    def test_최종승인시_알림_미호출(self) -> None:
        """최종 승인 시에는 다음 단계 알림이 호출되지 않는다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()

        service.approve(request_id="AR-001", approver="user-lead")

        notif.notify_approver.assert_not_called()

    def test_거절시_기안자_알림(self) -> None:
        """거절 시 기안자에게 알림."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()

        service.reject(request_id="AR-001", approver="user-lead", reason="불가")

        notif.notify_approver.assert_called_once_with("AR-001", "홍길동", "reject")

    def test_위임시_대상자_알림(self) -> None:
        """위임 시 위임 대상자에게 알림."""
        service, req_repo, _tmpl_repo, _action_repo, del_repo, notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()
        del_repo.find_many.return_value = [
            {
                "_id": "DR-001",
                "delegator": "user-lead",
                "delegate": "user-deputy",
                "from_date": None,
                "to_date": None,
                "is_active": True,
            },
        ]

        service.delegate(
            request_id="AR-001",
            delegator="user-lead",
            delegate_to="user-deputy",
        )

        notif.notify_approver.assert_called_once_with("AR-001", "user-deputy", "delegate")

    def test_알림실패시_결재흐름_정상(self) -> None:
        """알림 전송 실패해도 결재 처리는 정상 완료된다."""
        service, req_repo, _tmpl_repo, _action_repo, _del_repo, notif = _make_service()
        req_repo.find_by_id.return_value = _pending_request_doc()
        notif.notify_approver.side_effect = RuntimeError("알림 서비스 장애")

        # 거절 시 기안자 알림이 실패하더라도 결재 거절은 정상 처리
        result = service.reject(request_id="AR-001", approver="user-lead", reason="불가")

        assert result["status"] == "rejected"
