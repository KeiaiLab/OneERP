"""연결회계 서비스(ConsolidationService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_accounting_app.services.consolidation_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_accounting_app.services.consolidation_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_accounting_app.services.consolidation_service import ConsolidationService

        service = ConsolidationService(tenant_id="test-tenant")
    return (
        service,
        repos["consolidation_groups"],
        repos["intercompany_transactions"],
        repos["elimination_entries"],
        repos["journal_entries"],
    )


class Test연결재무제표:
    def test_내부거래_제거_포함(self) -> None:
        service, group_repo, ic_repo, elim_repo, je_repo = _make_service()
        group_repo.find_by_id.return_value = {"_id": "CG-001"}
        ic_repo.find_many.return_value = [
            {
                "_id": "ICT-001",
                "amount": 1000000,
                "from_company": "A",
                "to_company": "B",
                "description": "원자재",
            },
        ]
        je_repo.find_many.return_value = []

        result = service.generate_consolidated_report("CG-001", "2026-01-01", "2026-12-31")

        assert result["elimination_count"] == 1
        assert result["total_eliminated"] == 1000000
        elim_repo.insert.assert_called_once()

    def test_그룹_미존재_에러(self) -> None:
        service, group_repo, _ic, _elim, _je = _make_service()
        group_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.generate_consolidated_report("CG-999", "2026-01-01", "2026-12-31")

    def test_내부거래_없으면_제거없음(self) -> None:
        service, group_repo, ic_repo, _elim, je_repo = _make_service()
        group_repo.find_by_id.return_value = {"_id": "CG-001"}
        ic_repo.find_many.return_value = []
        je_repo.find_many.return_value = []

        result = service.generate_consolidated_report("CG-001", "2026-01-01", "2026-12-31")

        assert result["elimination_count"] == 0
        assert result["total_eliminated"] == 0
