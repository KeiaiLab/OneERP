"""위험 매트릭스 서비스(RiskMatrixService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """RiskMatrixService와 mock 레포지토리를 생성한다."""
    with patch(
        "oneerp_compliance_app.compliance_mod.services.risk_matrix_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_compliance_app.compliance_mod.services.risk_matrix_service import (
            RiskMatrixService,
        )

        service = RiskMatrixService(tenant_id="test-tenant")
    return service, repos["risk_assessments"]


class Test위험매트릭스:
    """위험 매트릭스 생성 테스트."""

    def test_빈_매트릭스(self) -> None:
        """위험 평가가 없으면 빈 매트릭스를 반환한다."""
        service, risk_repo = _make_service()
        risk_repo.find_many.return_value = []

        result = service.generate_matrix()

        assert result["total_assessments"] == 0
        assert result["high_risk_count"] == 0
        assert result["matrix"]["1x1"] == 0

    def test_고위험_항목_식별(self) -> None:
        """점수 >= 15인 항목을 고위험으로 분류한다."""
        service, risk_repo = _make_service()
        risk_repo.find_many.return_value = [
            {"risk_name": "재무 리스크", "likelihood": 5, "impact": 4},
            {"risk_name": "운영 리스크", "likelihood": 2, "impact": 2},
        ]

        result = service.generate_matrix()

        assert result["total_assessments"] == 2
        assert result["high_risk_count"] == 1
        assert result["high_risks"][0]["risk_name"] == "재무 리스크"
        assert result["high_risks"][0]["score"] == 20

    def test_매트릭스_셀_카운트(self) -> None:
        """매트릭스 셀에 위험 항목 수가 올바르게 집계된다."""
        service, risk_repo = _make_service()
        risk_repo.find_many.return_value = [
            {"risk_name": "A", "likelihood": 3, "impact": 3},
            {"risk_name": "B", "likelihood": 3, "impact": 3},
            {"risk_name": "C", "likelihood": 1, "impact": 5},
        ]

        result = service.generate_matrix()

        assert result["matrix"]["3x3"] == 2
        assert result["matrix"]["1x5"] == 1
        assert result["matrix"]["2x2"] == 0
