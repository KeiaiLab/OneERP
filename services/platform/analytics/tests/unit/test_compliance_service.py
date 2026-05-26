"""컴플라이언스 서비스(ComplianceService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_analytics_app.services.compliance_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_analytics_app.services.compliance_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_analytics_app.services.compliance_service import ComplianceService

        service = ComplianceService(tenant_id="test-tenant")
    return (
        service,
        repos["risk_assessments"],
        repos["audit_trails"],
        repos["internal_controls"],
        repos["compliance_reports"],
    )


class Test위험평가:
    def test_위험평가_생성(self) -> None:
        service, risk_repo, _audit, _control, _report = _make_service()

        result = service.create_risk_assessment(
            "재무",
            [
                {"description": "환율 리스크", "probability": 4, "impact": 5},
                {"description": "신용 리스크", "probability": 2, "impact": 3},
            ],
            "감사팀장",
        )

        assert result["risk_assessment_id"] == "RA-001"
        assert result["risk_count"] == 2
        # (4*5 + 2*3) / 2 = 13.0 → medium
        assert result["overall_risk_score"] == 13.0
        risk_repo.insert.assert_called_once()


class Test보고서:
    def test_보고서_생성(self) -> None:
        service, _risk, audit_repo, control_repo, report_repo = _make_service()
        audit_repo.find_many.return_value = [{"_id": "AT-001"}, {"_id": "AT-002"}]
        control_repo.find_many.return_value = [{"_id": "IC-001"}]

        result = service.generate_compliance_report("2026-Q1")

        assert result["report_id"] == "CR-001"
        assert result["audit_count"] == 2
        assert result["active_controls"] == 1
        report_repo.insert.assert_called_once()
