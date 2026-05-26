"""인명부 검색 서비스(DirectorySearchService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    """DirectorySearchService와 관련 Repository mock을 생성한다."""
    with patch(
        "oneerp_portal_comms_app.directory.services.directory_search_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_portal_comms_app.directory.services.directory_search_service import (
            DirectorySearchService,
        )

        service = DirectorySearchService(tenant_id="test-tenant")
    return service, repos


class Test인명부검색:
    def test_키워드_검색(self) -> None:
        """키워드로 인명부를 검색한다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = [
            {"_id": "EDIR-001", "employee_name": "홍길동", "email": "hong@test.com"},
        ]
        repos["employee_directories"].count.return_value = 1

        result = service.search_directory(keyword="홍길동")

        assert result["total"] == 1
        assert len(result["data"]) == 1
        assert result["page"] == 1

    def test_조직단위_필터(self) -> None:
        """조직 단위 ID로 필터링한다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = []
        repos["employee_directories"].count.return_value = 0

        result = service.search_directory(org_unit_id="UNIT-001")

        assert result["total"] == 0
        call_args = repos["employee_directories"].find_many.call_args
        # 쿼리에 org_unit_id 조건이 포함되어야 한다
        assert "org_unit_id" in str(call_args)

    def test_빈_결과(self) -> None:
        """검색 결과가 없으면 빈 목록을 반환한다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = []
        repos["employee_directories"].count.return_value = 0

        result = service.search_directory(keyword="존재하지않는이름")

        assert result["data"] == []
        assert result["total"] == 0


class Test조직단위구성원:
    def test_단일_단위_구성원(self) -> None:
        """하위 조직 미포함으로 단일 단위 구성원을 조회한다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = [
            {"_id": "EDIR-001", "employee_name": "홍길동"},
            {"_id": "EDIR-002", "employee_name": "김철수"},
        ]

        result = service.get_unit_members("UNIT-001")

        assert len(result) == 2

    def test_하위_조직_포함_조회(self) -> None:
        """하위 조직 포함으로 구성원을 조회한다."""
        service, repos = _make_service()
        repos["org_units"].find_many.return_value = [
            {"_id": "UNIT-002"},
            {"_id": "UNIT-003"},
        ]
        repos["employee_directories"].find_many.return_value = [
            {"_id": "EDIR-001"},
            {"_id": "EDIR-002"},
            {"_id": "EDIR-003"},
        ]

        result = service.get_unit_members("UNIT-001", include_sub_units=True)

        assert len(result) == 3


class Test주소속검증:
    def test_주소속_없으면_통과(self) -> None:
        """기존 주 소속이 없으면 True를 반환한다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = []

        result = service.validate_primary_assignment("EMP-001")
        assert result is True

    def test_주소속_중복_에러(self) -> None:
        """이미 주 소속이 있으면 ValueError를 발생시킨다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = [
            {
                "_id": "EDIR-001",
                "employee_id": "EMP-001",
                "org_unit_id": "UNIT-001",
                "is_primary": True,
            },
        ]

        with pytest.raises(ValueError, match="ERR-DIR-009"):
            service.validate_primary_assignment("EMP-001")

    def test_수정시_자기자신_제외(self) -> None:
        """수정 시 자기 자신의 엔트리는 제외한다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = [
            {
                "_id": "EDIR-001",
                "employee_id": "EMP-001",
                "org_unit_id": "UNIT-001",
                "is_primary": True,
            },
        ]

        result = service.validate_primary_assignment("EMP-001", exclude_entry_id="EDIR-001")
        assert result is True


class Test배치등록:
    def test_배치_정상_등록(self) -> None:
        """정상적인 배치 등록이 수행된다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = []  # 기존 주소속 없음

        entries = [
            {"employee_id": "EMP-001", "is_primary": True, "org_unit_id": "UNIT-001"},
            {"employee_id": "EMP-002", "is_primary": True, "org_unit_id": "UNIT-001"},
        ]
        result = service.batch_register(entries)

        assert result["success"] == 2
        assert result["failed"] == 0

    def test_배치내_주소속_중복(self) -> None:
        """동일 배치 내에서 같은 직원의 주 소속 중복을 감지한다."""
        service, repos = _make_service()
        repos["employee_directories"].find_many.return_value = []

        entries = [
            {"employee_id": "EMP-001", "is_primary": True},
            {"employee_id": "EMP-001", "is_primary": True},  # 중복
        ]
        result = service.batch_register(entries)

        assert result["success"] == 1
        assert result["failed"] == 1
        assert "ERR-DIR-015" in result["errors"][0]["error"]

    def test_직원ID_누락(self) -> None:
        """직원 ID가 누락된 엔트리는 실패 처리된다."""
        service, _repos = _make_service()

        entries = [
            {"employee_id": "", "is_primary": True},
        ]
        result = service.batch_register(entries)

        assert result["success"] == 0
        assert result["failed"] == 1
