"""자원 관리 서비스(ResourceService) 단위 테스트.

BR-RSV-001, BR-RSV-002 비즈니스 규칙을 검증한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service():
    """ResourceService와 mock Repository를 생성한다."""
    with patch(
        "oneerp_reservation_app.reservation.services.resource_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            repo.find_many.return_value = []
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_reservation_app.reservation.services.resource_service import ResourceService

        service = ResourceService(tenant_id="test-tenant")
    return service, repos


class Test자원명_고유성:
    """BR-RSV-001: 자원명 고유성 검증."""

    def test_고유명_통과(self) -> None:
        """동일 이름이 없으면 통과."""
        service, repos = _make_service()
        repos["resources"].find_many.return_value = []

        # 예외가 발생하지 않아야 한다
        service.validate_unique_name("회의실A")

    def test_중복명_에러(self) -> None:
        """동일 이름이 있으면 ERR-RSV-001 발생."""
        service, repos = _make_service()
        repos["resources"].find_many.return_value = [
            {"_id": "RSC-001", "name": "회의실A"},
        ]

        with pytest.raises(OneERPError, match="ERR-RSV-001"):
            service.validate_unique_name("회의실A")

    def test_자기자신_제외_고유성(self) -> None:
        """수정 시 자기 자신은 중복 검사에서 제외."""
        service, repos = _make_service()
        repos["resources"].find_many.return_value = [
            {"_id": "RSC-001", "name": "회의실A"},
        ]

        # 자기 자신 제외이므로 통과
        service.validate_unique_name("회의실A", exclude_id="RSC-001")

    def test_다른_자원과_중복시_에러(self) -> None:
        """수정 시 다른 자원과 이름 중복이면 에러."""
        service, repos = _make_service()
        repos["resources"].find_many.return_value = [
            {"_id": "RSC-002", "name": "회의실A"},
        ]

        with pytest.raises(OneERPError, match="ERR-RSV-001"):
            service.validate_unique_name("회의실A", exclude_id="RSC-001")


class Test자원_비활성화:
    """BR-RSV-002: 활성 예약이 없을 때만 비활성화 가능."""

    def test_활성예약_없으면_비활성화_성공(self) -> None:
        """활성 예약이 없으면 비활성화 가능."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "status": "active",
        }
        repos["reservations"].find_many.return_value = []

        result = service.deactivate_resource("RSC-001")
        assert result["status"] == "inactive"
        repos["resources"].update_by_id.assert_called_once()

    def test_활성예약_있으면_비활성화_불가(self) -> None:
        """활성 예약이 있으면 ERR-RSV-003 발생."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "status": "active",
        }
        repos["reservations"].find_many.return_value = [
            {"_id": "RSV-001", "status": "confirmed"},
        ]

        with pytest.raises(OneERPError, match="ERR-RSV-003"):
            service.deactivate_resource("RSC-001")

    def test_자원_미존재_에러(self) -> None:
        """자원이 존재하지 않으면 ERR-RSV-005 발생."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = None

        with pytest.raises(OneERPError, match="ERR-RSV-005"):
            service.deactivate_resource("RSC-999")

    def test_비활성화_가능여부_확인(self) -> None:
        """can_deactivate 메서드 정상 동작."""
        service, repos = _make_service()
        repos["reservations"].find_many.return_value = []

        assert service.can_deactivate("RSC-001") is True

    def test_활성예약_있으면_비활성화_불가능(self) -> None:
        """활성 예약이 있으면 can_deactivate가 False."""
        service, repos = _make_service()
        repos["reservations"].find_many.return_value = [
            {"_id": "RSV-001", "status": "confirmed"},
        ]

        assert service.can_deactivate("RSC-001") is False
