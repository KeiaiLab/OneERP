"""채용 서비스(RecruitmentService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_hr_app.services.recruitment_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_hr_app.services.recruitment_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_hr_app.services.recruitment_service import RecruitmentService

        service = RecruitmentService(tenant_id="test-tenant")
    return (
        service,
        repos["job_openings"],
        repos["job_applicants"],
        repos["offer_letters"],
    )


class Test지원자진행:
    def test_다음단계_진행(self) -> None:
        service, _opening, applicant_repo, _offer = _make_service()
        applicant_repo.find_by_id.return_value = {"_id": "JA-001", "stage": "applied"}

        result = service.advance_applicant("JA-001", "screening")

        assert result["current_stage"] == "screening"
        applicant_repo.update_by_id.assert_called_once()

    def test_유효하지않은_단계_에러(self) -> None:
        service, _opening, applicant_repo, _offer = _make_service()
        applicant_repo.find_by_id.return_value = {"_id": "JA-001", "stage": "applied"}

        with pytest.raises(OneERPError) as exc_info:
            service.advance_applicant("JA-001", "invalid_stage")
        assert exc_info.value.status_code == 400
        assert "유효하지 않은" in (exc_info.value.detail or "")

    def test_역방향_이동_차단(self) -> None:
        """BR-HR-005: offered → applied 등 역방향 이동 시 422 에러가 발생한다."""
        service, _opening, applicant_repo, _offer = _make_service()
        applicant_repo.find_by_id.return_value = {"_id": "JA-001", "stage": "offered"}

        with pytest.raises(OneERPError) as exc_info:
            service.advance_applicant("JA-001", "applied")
        assert exc_info.value.status_code == 422
        assert "유효하지 않은 단계 이동" in (exc_info.value.detail or "")

    def test_동일단계_이동_차단(self) -> None:
        """같은 단계로의 이동도 차단한다."""
        service, _opening, applicant_repo, _offer = _make_service()
        applicant_repo.find_by_id.return_value = {"_id": "JA-001", "stage": "screening"}

        with pytest.raises(OneERPError) as exc_info:
            service.advance_applicant("JA-001", "screening")
        assert exc_info.value.status_code == 422

    def test_지원자_미존재_에러(self) -> None:
        service, _opening, applicant_repo, _offer = _make_service()
        applicant_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.advance_applicant("JA-999", "screening")
        assert exc_info.value.status_code == 404
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")


class Test합격통보:
    def test_합격통보서_생성(self) -> None:
        service, _opening, applicant_repo, offer_repo = _make_service()
        applicant_repo.find_by_id.return_value = {"_id": "JA-001", "applicant_name": "홍길동"}

        result = service.create_offer("JA-001", "과장", "개발팀", 5000000)

        assert result["offer_id"] == "OFL-001"
        assert result["salary"] == 5000000
        offer_repo.insert.assert_called_once()
        applicant_repo.update_by_id.assert_called_once()


class Test파이프라인요약:
    def test_단계별_집계(self) -> None:
        service, _opening, applicant_repo, _offer = _make_service()
        applicant_repo.find_many.return_value = [
            {"stage": "applied"},
            {"stage": "applied"},
            {"stage": "interview"},
            {"stage": "offered"},
        ]

        result = service.get_pipeline_summary("JO-001")

        assert result["total_applicants"] == 4
        assert result["stage_counts"]["applied"] == 2
        assert result["stage_counts"]["interview"] == 1
        assert result["stage_counts"]["offered"] == 1


class Test채용제안서만료:
    """BR-HR-013: 유효기한 경과 채용제안서 자동 만료."""

    def test_만료_정상처리(self) -> None:
        """valid_until이 과거인 pending 제안서가 expired로 갱신된다."""
        service, _opening, _applicant, offer_repo = _make_service()
        offer_repo.find_many.return_value = [
            {
                "_id": "OFL-001",
                "applicant": "JA-001",
                "status": "pending",
                "valid_until": "2020-01-01",
            },
            {
                "_id": "OFL-002",
                "applicant": "JA-002",
                "status": "pending",
                "valid_until": "2020-06-15",
            },
        ]

        result = service.expire_stale_offers()

        assert len(result) == 2
        assert result[0]["offer_id"] == "OFL-001"
        assert offer_repo.update_by_id.call_count == 2

    def test_유효기한_미경과_건_유지(self) -> None:
        """valid_until이 미래인 pending 제안서는 만료 처리되지 않는다."""
        service, _opening, _applicant, offer_repo = _make_service()
        offer_repo.find_many.return_value = [
            {
                "_id": "OFL-003",
                "applicant": "JA-003",
                "status": "pending",
                "valid_until": "2099-12-31",
            },
        ]

        result = service.expire_stale_offers()

        assert len(result) == 0
        offer_repo.update_by_id.assert_not_called()

    def test_valid_until_없는_건_무시(self) -> None:
        """valid_until 필드가 없는 제안서는 무시한다."""
        service, _opening, _applicant, offer_repo = _make_service()
        offer_repo.find_many.return_value = [
            {"_id": "OFL-004", "applicant": "JA-004", "status": "pending"},
        ]

        result = service.expire_stale_offers()

        assert len(result) == 0
