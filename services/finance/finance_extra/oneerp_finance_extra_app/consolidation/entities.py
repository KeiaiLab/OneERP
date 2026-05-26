"""Consolidation 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

7개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.consolidated_report import (
    ConsolidatedReport,
    ConsolidatedReportCreate,
    ConsolidatedReportUpdate,
)
from .models.consolidation_entity import (
    ConsolidationEntity,
    ConsolidationEntityCreate,
    ConsolidationEntityUpdate,
)
from .models.consolidation_period import (
    ConsolidationPeriod,
    ConsolidationPeriodCreate,
    ConsolidationPeriodUpdate,
)
from .models.currency_translation import (
    CurrencyTranslation,
    CurrencyTranslationCreate,
    CurrencyTranslationUpdate,
)
from .models.elimination_rule import (
    EliminationRule,
    EliminationRuleCreate,
    EliminationRuleUpdate,
)
from .models.intercompany_balance import (
    IntercompanyBalance,
    IntercompanyBalanceCreate,
    IntercompanyBalanceUpdate,
)
from .models.investment_relation import (
    InvestmentRelation,
    InvestmentRelationCreate,
    InvestmentRelationUpdate,
)

# --- 마스터 데이터 ---

CONSOLIDATION_ENTITY = EntityMeta(
    collection="consolidation_entities",
    prefix="CENT",
    api_path="/api/v1/consolidation-entities",
    tag="연결 대상 법인",
    resource="consolidation_entity",
    model=ConsolidationEntity,
    create_schema=ConsolidationEntityCreate,
    update_schema=ConsolidationEntityUpdate,
    archetype="master",
    not_found_message="법인을 찾을 수 없습니다",
)

ELIMINATION_RULE = EntityMeta(
    collection="elimination_rules",
    prefix="ERULE",
    api_path="/api/v1/elimination-rules",
    tag="소거 규칙",
    resource="elimination_rule",
    model=EliminationRule,
    create_schema=EliminationRuleCreate,
    update_schema=EliminationRuleUpdate,
    archetype="master",
    not_found_message="소거 규칙을 찾을 ��� 없습니다",
)

# --- 트랜잭션 문서 ---

INVESTMENT_RELATION = EntityMeta(
    collection="investment_relations",
    prefix="IR",
    api_path="/api/v1/investment-relations",
    tag="투자 관계",
    resource="investment_relation",
    model=InvestmentRelation,
    create_schema=InvestmentRelationCreate,
    update_schema=InvestmentRelationUpdate,
    archetype="transaction",
    not_found_message="투자 관계를 찾�� 수 없습니다",
)

CONSOLIDATION_PERIOD = EntityMeta(
    collection="consolidation_periods",
    prefix="CPER",
    api_path="/api/v1/consolidation-periods",
    tag="연결 기간",
    resource="consolidation_period",
    model=ConsolidationPeriod,
    create_schema=ConsolidationPeriodCreate,
    update_schema=ConsolidationPeriodUpdate,
    archetype="transaction",
    not_found_message="연결 기간을 ��을 수 없습니다",
)

CONSOLIDATED_REPORT = EntityMeta(
    collection="consolidated_reports",
    prefix="CRPT",
    api_path="/api/v1/consolidated-reports",
    tag="연결 재무제표",
    resource="consolidated_report",
    model=ConsolidatedReport,
    create_schema=ConsolidatedReportCreate,
    update_schema=ConsolidatedReportUpdate,
    archetype="transaction",
    not_found_message="보고서를 찾을 수 없습니다",
)

CURRENCY_TRANSLATION = EntityMeta(
    collection="currency_translations",
    prefix="CTR",
    api_path="/api/v1/currency-translations",
    tag="통화 환산",
    resource="currency_translation",
    model=CurrencyTranslation,
    create_schema=CurrencyTranslationCreate,
    update_schema=CurrencyTranslationUpdate,
    archetype="transaction",
    not_found_message="통화 환산을 찾을 �� 없습니다",
)

INTERCOMPANY_BALANCE = EntityMeta(
    collection="intercompany_balances",
    prefix="ICB",
    api_path="/api/v1/intercompany-balances",
    tag="내부거래 잔액",
    resource="intercompany_balance",
    model=IntercompanyBalance,
    create_schema=IntercompanyBalanceCreate,
    update_schema=IntercompanyBalanceUpdate,
    archetype="transaction",
    not_found_message="내부거래 잔액을 찾��� 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    CONSOLIDATION_ENTITY,
    ELIMINATION_RULE,
    # 트랜잭션
    INVESTMENT_RELATION,
    CONSOLIDATION_PERIOD,
    CONSOLIDATED_REPORT,
    CURRENCY_TRANSLATION,
    INTERCOMPANY_BALANCE,
]
