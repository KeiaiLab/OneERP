"""투자 관계 서비스(InvestmentService) 단위 테스트.

BR-CSL-001: 연결 방법 자동 판단
BR-CSL-005: 영업권 산출
ERR-CSL-025: 순환 투자 감지
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_finance_extra_app.consolidation.models.consolidation_entity import ConsolidationMethod


def _make_service():
    """InvestmentService와 모킹된 Repository들을 반환한다."""
    with patch(
        "oneerp_finance_extra_app.consolidation.services.investment_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_finance_extra_app.consolidation.services.investment_service import (
            InvestmentService,
        )

        service = InvestmentService(tenant_id="test-tenant")

    return service, repos


class Test연결방법자동판단:
    """BR-CSL-001: 의결권 비율에 따른 연결 방법 자동 판단 테스트."""

    def test_의결권_80퍼센트_완전연결(self) -> None:
        """80% 의결권 → full, is_control=True."""
        service, _ = _make_service()
        result = service.determine_consolidation_method(Decimal(80))

        assert result["consolidation_method"] == ConsolidationMethod.FULL
        assert result["is_control"] is True
        assert result["is_significant_influence"] is False

    def test_의결권_50_01퍼센트_완전연결(self) -> None:
        """경계값 50.01% → full (과반수 초과)."""
        service, _ = _make_service()
        result = service.determine_consolidation_method(Decimal("50.01"))

        assert result["consolidation_method"] == ConsolidationMethod.FULL
        assert result["is_control"] is True

    def test_의결권_정확히_50퍼센트_지분법(self) -> None:
        """경계값 50% → equity (유의적 영향력)."""
        service, _ = _make_service()
        result = service.determine_consolidation_method(Decimal(50))

        assert result["consolidation_method"] == ConsolidationMethod.EQUITY
        assert result["is_control"] is False
        assert result["is_significant_influence"] is True

    def test_의결권_35퍼센트_지분법(self) -> None:
        """35% → equity (관계기업)."""
        service, _ = _make_service()
        result = service.determine_consolidation_method(Decimal(35))

        assert result["consolidation_method"] == ConsolidationMethod.EQUITY
        assert result["is_significant_influence"] is True

    def test_의결권_정확히_20퍼센트_지분법(self) -> None:
        """경계값 20% → equity."""
        service, _ = _make_service()
        result = service.determine_consolidation_method(Decimal(20))

        assert result["consolidation_method"] == ConsolidationMethod.EQUITY
        assert result["is_significant_influence"] is True

    def test_의결권_19_99퍼센트_연결제외(self) -> None:
        """경계값 19.99% → none."""
        service, _ = _make_service()
        result = service.determine_consolidation_method(Decimal("19.99"))

        assert result["consolidation_method"] == ConsolidationMethod.NONE
        assert result["is_control"] is False
        assert result["is_significant_influence"] is False


class Test영업권산출:
    """BR-CSL-005: 영업권 산출 테스트."""

    def test_부분영업권법_정상(self) -> None:
        """취득대가 80억, 순자산 90억, 지분율 80% → 부분 8억."""
        service, _ = _make_service()
        result = service.calculate_goodwill(
            acquisition_cost=Decimal(8000000000),
            fair_value_net_assets=Decimal(9000000000),
            ownership_percentage=Decimal(80),
        )
        # 80억 - (90억 x 80%) = 80억 - 72억 = 8억
        assert result["partial_goodwill"] == Decimal(800000000)

    def test_전부영업권법_정상(self) -> None:
        """NCI 공정가치 포함 전부영업권법."""
        service, _ = _make_service()
        result = service.calculate_goodwill(
            acquisition_cost=Decimal(8000000000),
            fair_value_net_assets=Decimal(9000000000),
            ownership_percentage=Decimal(80),
            nci_fair_value=Decimal(2000000000),
        )
        # (80억 + 20억) - 90억 = 10억
        assert result["full_goodwill"] == Decimal(1000000000)

    def test_염가매수_음의영업권(self) -> None:
        """취득대가 < 지분 해당 순자산 → 음의 영업권."""
        service, _ = _make_service()
        result = service.calculate_goodwill(
            acquisition_cost=Decimal(5000000000),
            fair_value_net_assets=Decimal(9000000000),
            ownership_percentage=Decimal(80),
        )
        # 50억 - 72억 = -22억
        assert result["partial_goodwill"] == Decimal(-2200000000)

    def test_영업권_없음_완전소유(self) -> None:
        """100% 소유, 취득대가 = 순자산 → 영업권 0."""
        service, _ = _make_service()
        result = service.calculate_goodwill(
            acquisition_cost=Decimal(10000000000),
            fair_value_net_assets=Decimal(10000000000),
            ownership_percentage=Decimal(100),
        )
        assert result["partial_goodwill"] == Decimal(0)

    def test_시나리오_KR_HQ_to_JP_SUB01(self) -> None:
        """L3 SC-CSL-001 시나리오: KR-HQ→JP-SUB01 70%."""
        service, _ = _make_service()
        result = service.calculate_goodwill(
            acquisition_cost=Decimal(3500000000),
            fair_value_net_assets=Decimal(4200000000),
            ownership_percentage=Decimal(70),
        )
        # 35억 - (42억 x 70%) = 35억 - 29.4억 = 5.6억
        assert result["partial_goodwill"] == Decimal(560000000)


class Test순환투자검출:
    """ERR-CSL-025: 순환 투자 관계 감지 테스트."""

    def test_순환_관계_존재(self) -> None:
        """역방향 투자 관계가 있으면 순환으로 판단."""
        service, repos = _make_service()
        repos["investment_relations"].find_many.return_value = [
            {"_id": "IR-001", "status": "active"}
        ]

        assert service.check_circular_investment("CENT-001", "CENT-002") is True

    def test_순환_관계_없음(self) -> None:
        """역방향 투자 관계가 없으면 정상."""
        service, repos = _make_service()
        repos["investment_relations"].find_many.return_value = []

        assert service.check_circular_investment("CENT-001", "CENT-002") is False


class Test투자관계생성:
    """투자 관계 생성 통합 테스트."""

    def test_순환투자_시_에러(self) -> None:
        """순환 투자 감지 시 ERR-CSL-025 발생."""
        service, repos = _make_service()
        # 역방향 관계 존재
        repos["investment_relations"].find_many.return_value = [
            {"_id": "IR-001", "status": "active"}
        ]

        with pytest.raises(OneERPError) as exc_info:
            service.create_investment_relation(
                {
                    "investor_entity_id": "CENT-001",
                    "investee_entity_id": "CENT-002",
                    "voting_rights_percentage": Decimal(80),
                }
            )

        assert exc_info.value.error == "ERR-CSL-025"

    def test_중복투자_시_에러(self) -> None:
        """동일 투자 관계 중복 시 409 발생."""
        service, repos = _make_service()
        # 순환 없음, 중복 있음
        repos["investment_relations"].find_many.side_effect = [
            [],  # 순환 검사
            [{"_id": "IR-001"}],  # 중복 검사
        ]

        with pytest.raises(OneERPError) as exc_info:
            service.create_investment_relation(
                {
                    "investor_entity_id": "CENT-001",
                    "investee_entity_id": "CENT-002",
                    "voting_rights_percentage": Decimal(80),
                }
            )

        assert exc_info.value.status_code == 409

    def test_정상생성_연결방법_자동판단(self) -> None:
        """정상 생성 시 연결 방법이 자동으로 설정된다."""
        service, repos = _make_service()
        repos["investment_relations"].find_many.return_value = []

        result = service.create_investment_relation(
            {
                "investor_entity_id": "CENT-001",
                "investee_entity_id": "CENT-002",
                "voting_rights_percentage": Decimal(70),
                "ownership_percentage": Decimal(70),
                "acquisition_cost": Decimal(3500000000),
                "fair_value_net_assets": Decimal(4200000000),
            }
        )

        assert result["consolidation_method"] == ConsolidationMethod.FULL
        assert result["is_control"] is True
        assert result["goodwill"] == Decimal(560000000)
