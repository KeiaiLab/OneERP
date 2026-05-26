"""연결결산 모델 단위 테스트.

모델 직렬화, 열거형, 기본값 검증을 수행한다.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from oneerp_finance_extra_app.consolidation.models.consolidated_report import (
    NCIBreakdown,
    NCIEntityDetail,
    ReportLineItem,
    ReportStatus,
    ReportTotals,
    ReportType,
)
from oneerp_finance_extra_app.consolidation.models.consolidation_entity import (
    ConsolidationEntity,
    ConsolidationEntityCreate,
    ConsolidationMethod,
    EntityStatus,
    EntityType,
)
from oneerp_finance_extra_app.consolidation.models.consolidation_period import (
    ConsolidationPeriodCreate,
    EntityCollectionStatus,
    PeriodStatus,
    PeriodType,
    ProcessStatus,
)
from oneerp_finance_extra_app.consolidation.models.currency_translation import (
    FCTADetail,
    HistoricalRate,
    TranslationItem,
    TranslationStatus,
)
from oneerp_finance_extra_app.consolidation.models.elimination_rule import (
    EliminationLineTemplate,
    EliminationRuleCreate,
    EliminationType,
    EntityPair,
    MatchingCriteria,
    RuleStatus,
)
from oneerp_finance_extra_app.consolidation.models.intercompany_balance import (
    IntercompanyBalanceCreate,
    IntercompanyBalanceType,
    MatchStatus,
)
from oneerp_finance_extra_app.consolidation.models.investment_relation import (
    InvestmentRelationCreate,
    RelationStatus,
)


class Test열거형:
    """열거형 값 검증."""

    def test_EntityType_값(self) -> None:
        assert EntityType.PARENT == "parent"
        assert EntityType.SUBSIDIARY == "subsidiary"
        assert EntityType.ASSOCIATE == "associate"
        assert EntityType.JOINT_VENTURE == "joint_venture"

    def test_ConsolidationMethod_값(self) -> None:
        assert ConsolidationMethod.FULL == "full"
        assert ConsolidationMethod.EQUITY == "equity"
        assert ConsolidationMethod.PROPORTIONATE == "proportionate"
        assert ConsolidationMethod.NONE == "none"

    def test_PeriodStatus_값(self) -> None:
        assert PeriodStatus.NOT_STARTED == "not_started"
        assert PeriodStatus.OPEN == "open"
        assert PeriodStatus.CLOSED == "closed"
        assert PeriodStatus.REOPENED == "reopened"

    def test_ProcessStatus_값(self) -> None:
        assert ProcessStatus.PENDING == "pending"
        assert ProcessStatus.COMPLETED == "completed"

    def test_EliminationType_값(self) -> None:
        assert EliminationType.REVENUE_EXPENSE == "revenue_expense"
        assert EliminationType.INVESTMENT_EQUITY == "investment_equity"

    def test_MatchStatus_값(self) -> None:
        assert MatchStatus.UNMATCHED == "unmatched"
        assert MatchStatus.MATCHED == "matched"
        assert MatchStatus.WITHIN_TOLERANCE == "within_tolerance"
        assert MatchStatus.MISMATCH == "mismatch"

    def test_ReportType_값(self) -> None:
        assert ReportType.BALANCE_SHEET == "balance_sheet"
        assert ReportType.INCOME_STATEMENT == "income_statement"

    def test_TranslationStatus_값(self) -> None:
        assert TranslationStatus.PENDING == "pending"
        assert TranslationStatus.COMPLETED == "completed"
        assert TranslationStatus.ERROR == "error"

    def test_RelationStatus_값(self) -> None:
        assert RelationStatus.ACTIVE == "active"
        assert RelationStatus.DISPOSED == "disposed"

    def test_RuleStatus_값(self) -> None:
        assert RuleStatus.ACTIVE == "active"
        assert RuleStatus.DRAFT == "draft"

    def test_ReportStatus_값(self) -> None:
        assert ReportStatus.DRAFT == "draft"
        assert ReportStatus.FINAL == "final"
        assert ReportStatus.SUPERSEDED == "superseded"


class Test법인모델:
    """ConsolidationEntity 모델 테스트."""

    def test_기본값(self) -> None:
        entity = ConsolidationEntity(entity_code="KR-HQ", entity_name="원얼프")
        assert entity.entity_type == EntityType.SUBSIDIARY
        assert entity.country_code == "KR"
        assert entity.functional_currency == "KRW"
        assert entity.consolidation_method == ConsolidationMethod.FULL
        assert entity.is_parent is False
        assert entity.status == EntityStatus.ACTIVE

    def test_생성스키마(self) -> None:
        create = ConsolidationEntityCreate(
            entity_code="JP-SUB01",
            entity_name="OneERP Japan",
            entity_type=EntityType.SUBSIDIARY,
            country_code="JP",
            functional_currency="JPY",
        )
        assert create.entity_code == "JP-SUB01"
        assert create.functional_currency == "JPY"


class Test투자관계모델:
    """InvestmentRelation 모델 테스트."""

    def test_생성스키마(self) -> None:
        create = InvestmentRelationCreate(
            investor_entity_id="CENT-001",
            investee_entity_id="CENT-002",
            ownership_percentage=Decimal(70),
            voting_rights_percentage=Decimal(70),
            acquisition_date=date(2023, 4, 1),
            acquisition_cost=Decimal(3500000000),
        )
        assert create.ownership_percentage == Decimal(70)
        assert create.acquisition_cost == Decimal(3500000000)


class Test연결기간모델:
    """ConsolidationPeriod 모델 테스트."""

    def test_생성스키마(self) -> None:
        create = ConsolidationPeriodCreate(
            period_name="2026-03",
            period_type=PeriodType.MONTHLY,
            from_date=date(2026, 3, 1),
            to_date=date(2026, 3, 31),
            fiscal_year="2026",
        )
        assert create.period_name == "2026-03"
        assert create.period_type == PeriodType.MONTHLY

    def test_EntityCollectionStatus(self) -> None:
        ecs = EntityCollectionStatus(entity_id="CENT-001", entity_name="원얼프")
        assert ecs.status == "not_started"
        assert ecs.individual_period_closed is False


class Test소거규칙모델:
    """EliminationRule 모델 테스트."""

    def test_생성스키마(self) -> None:
        create = EliminationRuleCreate(
            rule_code="ELIM-REV-EXP",
            rule_name="매출/매입 소거",
            elimination_type=EliminationType.REVENUE_EXPENSE,
        )
        assert create.priority == 100
        assert create.is_automatic is True

    def test_MatchingCriteria(self) -> None:
        mc = MatchingCriteria(
            source_account_pattern="내부매출*",
            target_account_pattern="내부매입*",
        )
        assert mc.match_by == "amount"
        assert mc.currency_match is True

    def test_EntityPair(self) -> None:
        pair = EntityPair(entity_a_id="CENT-001", entity_b_id="CENT-002")
        assert pair.entity_a_id == "CENT-001"

    def test_EliminationLineTemplate(self) -> None:
        template = EliminationLineTemplate(
            account_code="GRP-4100",
            entity_role="seller",
            amount_source="matched_amount",
        )
        assert template.fixed_amount is None


class Test내부거래잔액모델:
    """IntercompanyBalance 모델 테스트."""

    def test_생성스키마(self) -> None:
        create = IntercompanyBalanceCreate(
            period_id="CPER-001",
            entity_a_id="CENT-001",
            entity_b_id="CENT-002",
            balance_type=IntercompanyBalanceType.REVENUE_EXPENSE,
        )
        assert create.entity_a_amount == Decimal(0)
        assert create.entity_a_currency == "KRW"


class Test임베디드타입:
    """임베디드 타입 검증."""

    def test_ReportLineItem(self) -> None:
        item = ReportLineItem(
            line_no=1,
            account_code="GRP-1000",
            account_name="현금",
            current_period=Decimal(1000000),
        )
        assert item.is_subtotal is False
        assert item.account_level == 1

    def test_ReportTotals(self) -> None:
        totals = ReportTotals(
            total_assets=Decimal(100000000),
            total_liabilities=Decimal(40000000),
            total_equity=Decimal(60000000),
        )
        assert totals.bs_balance_check is None

    def test_NCIBreakdown(self) -> None:
        nci = NCIBreakdown(
            total_nci_equity=Decimal(1000000000),
            total_nci_profit=Decimal(200000000),
            entity_details=[
                NCIEntityDetail(
                    entity_id="CENT-002",
                    entity_name="일본법인",
                    nci_percentage=Decimal(30),
                    nci_equity=Decimal(500000000),
                    nci_profit=Decimal(100000000),
                ),
            ],
        )
        assert len(nci.entity_details) == 1

    def test_TranslationItem(self) -> None:
        item = TranslationItem(
            account_code="GRP-1100",
            account_name="매출채권",
            account_category="asset",
            original_amount=Decimal(800000000),
            applied_rate=Decimal("9.05"),
            rate_type="closing",
            translated_amount=Decimal(7240000000),
        )
        assert item.rate_type == "closing"

    def test_HistoricalRate(self) -> None:
        hr = HistoricalRate(
            account_code="GRP-3100",
            rate=Decimal("8.50"),
            rate_date=date(2023, 4, 1),
        )
        assert hr.rate == Decimal("8.50")

    def test_FCTADetail(self) -> None:
        detail = FCTADetail(
            bs_translation_total=Decimal(10860000000),
            pl_translation_total=Decimal(900000000),
            equity_translation_total=Decimal(2550000000),
            opening_fcta=Decimal(0),
            current_fcta=Decimal(7410000000),
            closing_fcta=Decimal(7410000000),
        )
        assert detail.closing_fcta == detail.opening_fcta + detail.current_fcta

    def test_EntityStatus_값(self) -> None:
        assert EntityStatus.ACTIVE == "active"
        assert EntityStatus.INACTIVE == "inactive"
        assert EntityStatus.PENDING == "pending"

    def test_IntercompanyBalanceType_값(self) -> None:
        assert IntercompanyBalanceType.REVENUE_EXPENSE == "revenue_expense"
        assert IntercompanyBalanceType.LOAN == "loan"
        assert IntercompanyBalanceType.DIVIDEND == "dividend"
