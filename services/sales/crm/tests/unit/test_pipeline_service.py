"""PipelineService 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_crm_app.services.pipeline_service.generate_name",
        side_effect=lambda prefix, **kw: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """PipelineService + mock 리포지터리를 생성한다."""
    with patch("oneerp_crm_app.services.pipeline_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_crm_app.services.pipeline_service import PipelineService

        service = PipelineService(tenant_id="test-tenant")
    return service, repos


class Test리드전환:
    def test_리드를_기회로_전환(self) -> None:
        service, repos = _make_service()
        lead_repo = repos["leads"]
        opp_repo = repos["opportunities"]
        lead_repo.find_by_id.return_value = {
            "_id": "LEAD-001",
            "status": "qualified",
            "lead_name": "테스트 리드",
        }

        result = service.convert_lead_to_opportunity("LEAD-001")

        assert result["lead_id"] == "LEAD-001"
        assert result["opportunity_id"] == "OPP-001"
        assert result["status"] == "open"
        lead_repo.update_by_id.assert_called_once_with("LEAD-001", {"status": "converted"})
        opp_repo.insert.assert_called_once()

    def test_존재하지_않는_리드_에러(self) -> None:
        service, repos = _make_service()
        repos["leads"].find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.convert_lead_to_opportunity("LEAD-999")

    def test_이미_전환된_리드_에러(self) -> None:
        service, repos = _make_service()
        repos["leads"].find_by_id.return_value = {
            "_id": "LEAD-001",
            "status": "converted",
        }

        with pytest.raises(OneERPError, match="ERR-CRM-001"):
            service.convert_lead_to_opportunity("LEAD-001")


class Test단계진행:
    def test_open에서_quotation으로_진행(self) -> None:
        service, repos = _make_service()
        repos["opportunities"].find_by_id.return_value = {
            "_id": "OPP-001",
            "status": "open",
        }

        result = service.advance_stage("OPP-001", "quotation")

        assert result["new_stage"] == "quotation"
        assert result["previous_stage"] == "open"
        repos["opportunities"].update_by_id.assert_called_once()

    def test_잘못된_전환_에러(self) -> None:
        service, repos = _make_service()
        repos["opportunities"].find_by_id.return_value = {
            "_id": "OPP-001",
            "status": "won",
        }

        with pytest.raises(OneERPError, match="ERR-CRM-002"):
            service.advance_stage("OPP-001", "open")


class Test견적전환:
    def test_기회를_견적으로_전환_이벤트_발행(self) -> None:
        """기회 전환 시 quotations 직접 쓰기 대신 Outbox 이벤트를 발행한다."""
        service, repos = _make_service()
        repos["opportunities"].find_by_id.return_value = {
            "_id": "OPP-001",
            "status": "open",
        }

        result = service.convert_opportunity_to_quotation(
            "OPP-001", "CUST-001", [{"item": "A", "qty": 1}]
        )

        assert result["opportunity_id"] == "OPP-001"
        # quotations 컬렉션에 직접 insert하지 않음
        assert "quotations" not in repos
        # opportunities에 상태 변경 + outbox 이벤트가 기록됨
        opp_repo = repos["opportunities"]
        update_call = opp_repo.update_by_id.call_args
        assert update_call[0][0] == "OPP-001"
        update_data = update_call[0][1]
        assert update_data["status"] == "quotation"
        # Outbox 이벤트가 포함되었는지 검증
        outbox_entries = update_data["_outbox_pending"]
        assert len(outbox_entries) == 1
        assert outbox_entries[0]["event_type"] == "opportunity.converted"
        assert outbox_entries[0]["data"]["customer_id"] == "CUST-001"


class TestWonLost:
    def test_성사_처리(self) -> None:
        service, repos = _make_service()
        repos["opportunities"].find_by_id.return_value = {
            "_id": "OPP-001",
            "status": "open",
        }

        result = service.mark_won("OPP-001")

        assert result["new_stage"] == "won"

    def test_실패_처리(self) -> None:
        service, repos = _make_service()
        repos["opportunities"].find_by_id.return_value = {
            "_id": "OPP-001",
            "status": "open",
        }

        result = service.mark_lost("OPP-001", lost_reason="가격", competitor="경쟁사A")

        assert result["status"] == "lost"
        assert result["lost_reason"] == "가격"
        assert result["competitor"] == "경쟁사A"


class Test집계:
    def test_파이프라인_요약(self) -> None:
        service, repos = _make_service()
        opp_repo = repos["opportunities"]
        opp_repo.find_many.side_effect = [
            [{"expected_amount": 100}, {"expected_amount": 200}],  # open
            [{"expected_amount": 300}],  # quotation
            [{"expected_amount": 500}],  # won
            [],  # lost
        ]

        result = service.get_pipeline_summary()

        assert len(result["stages"]) == 4
        assert result["stages"][0]["count"] == 2
        assert result["stages"][0]["total_amount"] == 300

    def test_전환율_계산(self) -> None:
        service, repos = _make_service()
        lead_repo = repos["leads"]
        opp_repo = repos["opportunities"]
        lead_repo.count.side_effect = [100, 30]  # total, converted
        opp_repo.count.side_effect = [30, 10]  # total, won

        result = service.get_conversion_metrics()

        assert result["lead_to_opportunity_rate"] == 30.0
        assert result["opportunity_to_won_rate"] == pytest.approx(33.33)


class Test리드스코어링:
    """BR-CRM-017: 리드 스코어링 가중치 테스트."""

    def test_스코어링_기준_적용(self) -> None:
        """리드 속성에 가중치를 적용하여 total_score를 산출한다."""
        service, repos = _make_service()
        lead_repo = repos["leads"]
        scoring_repo = repos["lead_scorings"]

        lead_repo.find_by_id.return_value = {
            "_id": "LEAD-001",
            "company": "테스트사",
            "industry": "IT",
            "source": "",
        }
        scoring_repo.find_many.return_value = [
            {"scoring_criteria": "company", "score": 30},
            {"scoring_criteria": "industry", "score": 20},
            {"scoring_criteria": "source", "score": 10},  # 빈 문자열이므로 미매칭
        ]

        result = service.calculate_lead_score("LEAD-001")

        assert result["total_score"] == 50.0  # company(30) + industry(20), source 미적용
        assert result["criteria_count"] == 3
        assert result["details"][0]["matched"] is True
        assert result["details"][2]["matched"] is False
        lead_repo.update_by_id.assert_called_once_with("LEAD-001", {"lead_score": 50.0})

    def test_스코어링_기준_없음_에러(self) -> None:
        """스코어링 기준이 없으면 에러를 발생시킨다."""
        service, repos = _make_service()
        repos["leads"].find_by_id.return_value = {"_id": "LEAD-001"}
        repos["lead_scorings"].find_many.return_value = []

        with pytest.raises(OneERPError, match="ERR-CRM-017"):
            service.calculate_lead_score("LEAD-001")

    def test_존재하지_않는_리드_에러(self) -> None:
        service, repos = _make_service()
        repos["leads"].find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.calculate_lead_score("LEAD-999")


class Test설문집계:
    """BR-CRM-019: 설문 응답 집계 테스트."""

    def test_설문_응답_집계(self) -> None:
        """해당 설문의 응답을 집계하여 평균 점수와 응답 수를 반환한다."""
        service, repos = _make_service()
        repos["survey_responses"].find_many.return_value = [
            {"score": 4},
            {"score": 5},
            {"score": 3},
            {"score": 4},
        ]

        result = service.aggregate_survey_responses("SURVEY-001")

        assert result["survey_id"] == "SURVEY-001"
        assert result["response_count"] == 4
        assert result["average_score"] == 4.0

    def test_응답_없는_설문(self) -> None:
        """응답이 없으면 0건, 평균 0.0을 반환한다."""
        service, repos = _make_service()
        repos["survey_responses"].find_many.return_value = []

        result = service.aggregate_survey_responses("SURVEY-999")

        assert result["response_count"] == 0
        assert result["average_score"] == 0.0
