"""결재선 동적 결정 서비스 단위 테스트.

BR-APR-021: 결재선 동적 결정 (문서 유형 + 금액 + 조직도 기반)
BR-APR-022: 부재중 자동 위임 적용
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    """ApprovalChainResolverService와 모킹된 Repository들을 반환한다."""
    with patch(
        "oneerp_gateway_app.services.approval_chain_resolver_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_gateway_app.services.approval_chain_resolver_service import (
            ApprovalChainResolverService,
        )

        service = ApprovalChainResolverService(tenant_id="test-tenant")

    return (
        service,
        repos["approval_templates"],
        repos["users"],
        repos["delegation_rules"],
    )


def _single_step_template() -> dict:
    """단일 단계 템플릿 (역할 기반)."""
    return {
        "_id": "AT-001",
        "template_name": "구매 결재",
        "document_type": "PurchaseOrder",
        "steps": [
            {"step": 1, "approver_role": "team_lead", "approver_type": "single"},
        ],
    }


def _two_step_template() -> dict:
    """2단계 템플릿 (팀장 -> 부서장)."""
    return {
        "_id": "AT-002",
        "template_name": "경비 결재",
        "document_type": "ExpenseClaim",
        "steps": [
            {"step": 1, "approver_role": "team_lead"},
            {"step": 2, "approver_role": "department_head"},
        ],
    }


def _fixed_approver_template() -> dict:
    """고정 결재자 지정 템플릿."""
    return {
        "_id": "AT-003",
        "template_name": "긴급 결재",
        "document_type": "UrgentRequest",
        "steps": [
            {"step": 1, "approver": "USR-FIXED-001", "approver_role": ""},
        ],
    }


class Test결재선동적결정:
    """BR-APR-021: 결재선 동적 결정."""

    def test_템플릿_미존재_시_not_found(self) -> None:
        """문서 유형에 해당하는 템플릿이 없으면 OneERPError가 발생한다."""
        service, template_repo, _, _ = _make_service()
        template_repo.find_many.return_value = []

        from oneerp_core.errors import OneERPError

        with pytest.raises(OneERPError) as exc_info:
            service.resolve_chain(
                document_type="Unknown",
                requester="USR-001",
            )
        assert exc_info.value.status_code == 404

    def test_역할_기반_결재자_자동_매핑(self) -> None:
        """approver_role이 지정되면 조직도에서 결재자를 자동 매핑한다."""
        service, template_repo, user_repo, delegation_repo = _make_service()
        template_repo.find_many.return_value = [_single_step_template()]
        # 역할 기반 사용자 조회 결과
        user_repo.find_many.return_value = [
            {"_id": "USR-LEAD-001", "roles": ["team_lead"], "is_active": True},
        ]
        user_repo.find_by_id.return_value = None  # out_of_office 체크용
        delegation_repo.find_many.return_value = []

        result = service.resolve_chain(
            document_type="PurchaseOrder",
            requester="USR-001",
            amount=Decimal(500000),
            requester_department="DEPT-01",
        )

        assert result["total_steps"] == 1
        assert result["chain"][0]["approver"] == "USR-LEAD-001"
        assert result["chain"][0]["approver_role"] == "team_lead"

    def test_고정_결재자_사용(self) -> None:
        """템플릿에 고정 결재자가 지정되면 역할 조회 없이 사용한다."""
        service, template_repo, user_repo, delegation_repo = _make_service()
        template_repo.find_many.return_value = [_fixed_approver_template()]
        user_repo.find_by_id.return_value = None
        delegation_repo.find_many.return_value = []

        result = service.resolve_chain(
            document_type="UrgentRequest",
            requester="USR-001",
            amount=Decimal(0),
        )

        assert result["chain"][0]["approver"] == "USR-FIXED-001"
        # 역할 기반 조회는 호출되지 않아야 함
        user_repo.find_many.assert_not_called()

    def test_금액_기반_필수_결재_단계_추가(self) -> None:
        """금액이 큰 경우 필수 역할이 없으면 자동으로 추가된다.

        500만원 초과는 department_head 필수 -> 2단계 템플릿에 이미 있으므로 추가 안 됨.
        5000만원 초과는 executive 필수 -> 없으면 자동 추가.
        """
        service, template_repo, user_repo, delegation_repo = _make_service()
        template_repo.find_many.return_value = [_two_step_template()]

        # 역할별 사용자 조회 응답
        def _find_many_users(query: dict, limit: int) -> list[dict]:
            role_list = query.get("roles", {}).get("$in", [])
            if "team_lead" in role_list:
                return [{"_id": "USR-LEAD", "roles": ["team_lead"], "is_active": True}]
            if "department_head" in role_list:
                return [{"_id": "USR-DEPT", "roles": ["department_head"], "is_active": True}]
            if "executive" in role_list:
                return [{"_id": "USR-EXEC", "roles": ["executive"], "is_active": True}]
            return []

        user_repo.find_many.side_effect = _find_many_users
        user_repo.find_by_id.return_value = None
        delegation_repo.find_many.return_value = []

        result = service.resolve_chain(
            document_type="ExpenseClaim",
            requester="USR-001",
            amount=Decimal(30000000),  # 3천만원 -> executive 필수 (5000만원 이하 구간)
            requester_department="DEPT-01",
        )

        # 기본 2단계 + executive 자동 추가 = 3단계
        assert result["total_steps"] == 3
        assert result["amount_tier"] == "executive"
        # 마지막 단계가 executive여야 함
        last_line = result["chain"][-1]
        assert last_line["approver_role"] == "executive"
        assert last_line.get("auto_added_for_amount") is True

    def test_소액_결재_단계_추가_없음(self) -> None:
        """소액(100만원 이하)이면 team_lead만 필요하므로 추가 없음."""
        service, template_repo, user_repo, delegation_repo = _make_service()
        template_repo.find_many.return_value = [_single_step_template()]
        user_repo.find_many.return_value = [
            {"_id": "USR-LEAD", "roles": ["team_lead"], "is_active": True},
        ]
        user_repo.find_by_id.return_value = None
        delegation_repo.find_many.return_value = []

        result = service.resolve_chain(
            document_type="PurchaseOrder",
            requester="USR-001",
            amount=Decimal(500000),
        )

        assert result["total_steps"] == 1
        assert result["amount_tier"] == "team_lead"


class Test부재중자동위임:
    """BR-APR-022: 부재중 자동 위임 적용."""

    def test_out_of_office_플래그로_대리자_치환(self) -> None:
        """user.out_of_office=true면 out_of_office_delegate로 치환된다."""
        service, template_repo, user_repo, delegation_repo = _make_service()
        template_repo.find_many.return_value = [_fixed_approver_template()]
        # 고정 결재자가 부재 중
        user_repo.find_by_id.return_value = {
            "_id": "USR-FIXED-001",
            "out_of_office": True,
            "out_of_office_delegate": "USR-BACKUP-001",
        }
        delegation_repo.find_many.return_value = []

        result = service.resolve_chain(
            document_type="UrgentRequest",
            requester="USR-001",
        )

        assert result["chain"][0]["approver"] == "USR-BACKUP-001"
        assert result["chain"][0]["delegated_from"] == "USR-FIXED-001"
        assert len(result["delegations_applied"]) == 1
        assert result["delegations_applied"][0]["reason"] == "out_of_office"

    def test_delegation_rule_유효범위_내_치환(self) -> None:
        """유효한 DelegationRule이 있으면 대리자로 치환된다."""
        service, template_repo, user_repo, delegation_repo = _make_service()
        template_repo.find_many.return_value = [_fixed_approver_template()]

        # 부재중 아님
        user_repo.find_by_id.return_value = {
            "_id": "USR-FIXED-001",
            "out_of_office": False,
        }
        # 오늘이 위임 범위 내
        today = datetime.now(tz=UTC).date()
        delegation_repo.find_many.return_value = [
            {
                "delegator": "USR-FIXED-001",
                "delegate": "USR-DEL-001",
                "is_active": True,
                "from_date": today - timedelta(days=5),
                "to_date": today + timedelta(days=5),
            }
        ]

        result = service.resolve_chain(
            document_type="UrgentRequest",
            requester="USR-001",
        )

        assert result["chain"][0]["approver"] == "USR-DEL-001"
        assert result["delegations_applied"][0]["reason"] == "delegation_rule"

    def test_만료된_delegation_rule_무시(self) -> None:
        """to_date가 지난 위임 규칙은 무시된다."""
        service, template_repo, user_repo, delegation_repo = _make_service()
        template_repo.find_many.return_value = [_fixed_approver_template()]
        user_repo.find_by_id.return_value = {"_id": "USR-FIXED-001", "out_of_office": False}

        today = datetime.now(tz=UTC).date()
        delegation_repo.find_many.return_value = [
            {
                "delegator": "USR-FIXED-001",
                "delegate": "USR-DEL-001",
                "is_active": True,
                "from_date": today - timedelta(days=30),
                "to_date": today - timedelta(days=1),  # 어제 만료
            }
        ]

        result = service.resolve_chain(
            document_type="UrgentRequest",
            requester="USR-001",
        )

        # 치환 없음 -> 원래 결재자 유지
        assert result["chain"][0]["approver"] == "USR-FIXED-001"
        assert len(result["delegations_applied"]) == 0


class Test연속결재자중복제거:
    """연속 동일 결재자 병합 규칙."""

    def test_동일_결재자_연속_병합(self) -> None:
        """동일 결재자가 연속 단계에 있으면 한 단계로 병합되고 step 재정렬된다."""
        service, template_repo, user_repo, delegation_repo = _make_service()

        # 팀장과 부서장이 같은 사용자인 케이스
        template_repo.find_many.return_value = [
            {
                "_id": "AT-X",
                "document_type": "TestDoc",
                "steps": [
                    {"step": 1, "approver_role": "team_lead"},
                    {"step": 2, "approver_role": "department_head"},
                ],
            }
        ]

        def _find_many_users(query: dict, limit: int) -> list[dict]:
            # 두 역할 모두 같은 사용자로 매핑
            return [{"_id": "USR-SAME", "roles": ["team_lead"], "is_active": True}]

        user_repo.find_many.side_effect = _find_many_users
        user_repo.find_by_id.return_value = None
        delegation_repo.find_many.return_value = []

        result = service.resolve_chain(
            document_type="TestDoc",
            requester="USR-001",
            amount=Decimal(100000),
        )

        # 연속 동일 -> 1단계로 병합
        assert result["total_steps"] == 1
        assert result["chain"][0]["step"] == 1
        assert result["chain"][0]["approver"] == "USR-SAME"


class Test금액계층판정:
    """금액별 최소 필수 역할 결정 로직."""

    def test_100만원_이하_team_lead(self) -> None:
        service, _, _, _ = _make_service()
        assert service._determine_minimum_role(Decimal(500000)) == "team_lead"
        assert service._determine_minimum_role(Decimal(1000000)) == "team_lead"

    def test_500만원_이하_department_head(self) -> None:
        service, _, _, _ = _make_service()
        assert service._determine_minimum_role(Decimal(1000001)) == "department_head"
        assert service._determine_minimum_role(Decimal(5000000)) == "department_head"

    def test_5000만원_이하_executive(self) -> None:
        service, _, _, _ = _make_service()
        assert service._determine_minimum_role(Decimal(10000000)) == "executive"
        assert service._determine_minimum_role(Decimal(50000000)) == "executive"

    def test_5000만원_초과_ceo(self) -> None:
        service, _, _, _ = _make_service()
        assert service._determine_minimum_role(Decimal(50000001)) == "ceo"
        assert service._determine_minimum_role(Decimal(1000000000)) == "ceo"
