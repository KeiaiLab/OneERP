"""권한 매트릭스 평가 서비스 단위 테스트.

BR-APR-030: 권한 매트릭스 평가 (사용자x역할x자원x액션)
BR-APR-031: 멀티테넌트 격리 강제
BR-APR-032: 명시적 거부(deny) 우선 평가
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_service(tenant_id: str = "test-tenant") -> tuple:
    """PermissionMatrixService와 모킹된 Repository를 반환한다."""
    with patch("oneerp_gateway_app.services.permission_matrix_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_gateway_app.services.permission_matrix_service import PermissionMatrixService

        service = PermissionMatrixService(tenant_id=tenant_id)

    return service, repos["role_permissions"], repos["users"]


class Test기본권한평가:
    """BR-APR-030: 역할 기반 권한 매트릭스 평가."""

    def test_유효한_역할과_권한_매치_시_허용(self) -> None:
        service, role_perm_repo, user_repo = _make_service()

        user_repo.find_by_id.return_value = {
            "_id": "USR-001",
            "is_active": True,
            "roles": ["sales_rep"],
            "user_tier": "regular",
        }
        role_perm_repo.find_many.return_value = [
            {
                "role": "sales_rep",
                "doctype": "Lead",
                "read": True,
                "write": True,
                "create": True,
            }
        ]

        decision = service.evaluate(user_id="USR-001", doctype="Lead", action="read")

        assert decision.allowed is True
        assert decision.matched_role == "sales_rep"

    def test_알수없는_액션은_거부(self) -> None:
        service, _, _ = _make_service()

        decision = service.evaluate(user_id="USR-001", doctype="Lead", action="invalid_action")

        assert decision.allowed is False
        assert "알 수 없는 액션" in decision.reason

    def test_사용자_없으면_거부(self) -> None:
        service, _, user_repo = _make_service()
        user_repo.find_by_id.return_value = None

        decision = service.evaluate(user_id="USR-GHOST", doctype="Lead", action="read")

        assert decision.allowed is False
        assert "찾을 수 없습니다" in decision.reason

    def test_비활성_사용자_거부(self) -> None:
        service, _, user_repo = _make_service()
        user_repo.find_by_id.return_value = {
            "_id": "USR-002",
            "is_active": False,
            "roles": ["admin"],
        }

        decision = service.evaluate(user_id="USR-002", doctype="Lead", action="read")

        assert decision.allowed is False
        assert "비활성" in decision.reason

    def test_역할_없는_사용자_거부(self) -> None:
        service, _, user_repo = _make_service()
        user_repo.find_by_id.return_value = {
            "_id": "USR-003",
            "is_active": True,
            "roles": [],
        }

        decision = service.evaluate(user_id="USR-003", doctype="Lead", action="read")

        assert decision.allowed is False
        assert "역할이 할당" in decision.reason

    def test_권한_규칙_미매치_거부(self) -> None:
        service, role_perm_repo, user_repo = _make_service()
        user_repo.find_by_id.return_value = {
            "_id": "USR-001",
            "is_active": True,
            "roles": ["sales_rep"],
        }
        role_perm_repo.find_many.return_value = [
            {"role": "sales_rep", "doctype": "Lead", "read": True, "write": False}
        ]

        # write 권한 요청이지만 규칙은 write=False
        decision = service.evaluate(user_id="USR-001", doctype="Lead", action="write")

        assert decision.allowed is False


class TestSuper관리자권한:
    """Super Admin은 모든 권한 허용 (테넌트 경계 유지)."""

    def test_super_admin_즉시_허용(self) -> None:
        service, _, user_repo = _make_service()
        user_repo.find_by_id.return_value = {
            "_id": "USR-ADMIN",
            "is_active": True,
            "user_tier": "super_admin",
            "is_super_admin": True,
            "roles": [],
        }

        decision = service.evaluate(user_id="USR-ADMIN", doctype="AnyDoc", action="delete")

        assert decision.allowed is True
        assert decision.matched_role == "super_admin"
        assert "super_admin" in decision.reason

    def test_super_admin_교차_테넌트_접근_허용(self) -> None:
        """super_admin은 테넌트 경계를 넘을 수 있다."""
        service, _, user_repo = _make_service(tenant_id="tenant-A")
        user_repo.find_by_id.return_value = {
            "_id": "USR-ADMIN",
            "is_active": True,
            "user_tier": "super_admin",
            "is_super_admin": True,
            "roles": [],
        }

        decision = service.evaluate(
            user_id="USR-ADMIN",
            doctype="Lead",
            action="read",
            target_tenant_id="tenant-B",
        )

        assert decision.allowed is True


class Test멀티테넌트경계:
    """BR-APR-031: 멀티테넌트 격리."""

    def test_타_테넌트_접근_일반_사용자_거부(self) -> None:
        service, _, user_repo = _make_service(tenant_id="tenant-A")
        user_repo.find_by_id.return_value = {
            "_id": "USR-001",
            "is_active": True,
            "user_tier": "regular",
            "roles": ["sales_rep"],
        }

        decision = service.evaluate(
            user_id="USR-001",
            doctype="Lead",
            action="read",
            target_tenant_id="tenant-B",
        )

        assert decision.allowed is False
        assert "테넌트 경계" in decision.reason
        assert decision.tenant_scope == "tenant-B"


class Test명시적거부우선:
    """BR-APR-032: 명시적 deny 우선 평가."""

    def test_deny_규칙이_allow보다_우선(self) -> None:
        service, role_perm_repo, user_repo = _make_service()
        user_repo.find_by_id.return_value = {
            "_id": "USR-001",
            "is_active": True,
            "roles": ["sales_rep"],
        }

        # sales_rep는 Lead 읽기 가능, 그러나 deny 규칙 있음
        role_perm_repo.find_many.return_value = [
            {"role": "sales_rep", "doctype": "Lead", "read": True},
            {"role": "sales_rep", "doctype": "Lead", "read": True, "deny": True},
        ]

        decision = service.evaluate(user_id="USR-001", doctype="Lead", action="read")

        assert decision.allowed is False
        assert "명시적 거부" in decision.reason

    def test_다중_역할_deny_우선(self) -> None:
        """여러 역할 중 하나라도 deny면 거부."""
        service, role_perm_repo, user_repo = _make_service()
        user_repo.find_by_id.return_value = {
            "_id": "USR-001",
            "is_active": True,
            "roles": ["sales_rep", "observer"],
        }

        def _find_many(query: dict, limit: int) -> list[dict]:
            # or 쿼리 사용
            or_clauses = query.get("$or", [])
            role = or_clauses[0].get("role", "") if or_clauses else ""
            if role == "sales_rep":
                return [{"role": "sales_rep", "doctype": "Lead", "read": True}]
            if role == "observer":
                return [
                    {
                        "role": "observer",
                        "doctype": "Lead",
                        "read": True,
                        "deny": True,
                    }
                ]
            return []

        role_perm_repo.find_many.side_effect = _find_many

        decision = service.evaluate(user_id="USR-001", doctype="Lead", action="read")

        assert decision.allowed is False
        assert decision.denied_by == "observer"


class Test와일드카드매치:
    """doctype=* 와일드카드 지원."""

    def test_doctype_와일드카드_매치(self) -> None:
        service, role_perm_repo, user_repo = _make_service()
        user_repo.find_by_id.return_value = {
            "_id": "USR-001",
            "is_active": True,
            "roles": ["admin"],
        }
        # admin 역할은 모든 doctype에 대해 read 허용
        role_perm_repo.find_many.return_value = [
            {"role": "admin", "doctype": "*", "read": True, "write": True}
        ]

        decision = service.evaluate(user_id="USR-001", doctype="ArbitraryDoc", action="read")

        assert decision.allowed is True
        assert decision.matched_role == "admin"


class TestBulk평가:
    """벌크 권한 평가 API."""

    def test_복수_체크_동시_평가(self) -> None:
        service, role_perm_repo, user_repo = _make_service()
        user_repo.find_by_id.return_value = {
            "_id": "USR-001",
            "is_active": True,
            "roles": ["sales_rep"],
        }
        role_perm_repo.find_many.return_value = [
            {"role": "sales_rep", "doctype": "Lead", "read": True, "write": True}
        ]

        results = service.evaluate_bulk(
            user_id="USR-001",
            checks=[
                {"doctype": "Lead", "action": "read"},
                {"doctype": "Lead", "action": "write"},
                {"doctype": "Lead", "action": "delete"},
            ],
        )

        assert len(results) == 3
        assert results[0]["allowed"] is True
        assert results[1]["allowed"] is True
        assert results[2]["allowed"] is False  # delete 규칙 없음
