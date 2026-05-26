"""ESG 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

5개 엔티티를 EntityMeta로 선언한다.
ESGMetric(마스터), SustainabilityReport/CarbonEmission/WasteManagement/ESGDisclosure(트랜잭션).
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.carbon_emission import (
    CarbonEmission,
    CarbonEmissionCreate,
    CarbonEmissionUpdate,
)
from .models.esg_disclosure import (
    ESGDisclosure,
    ESGDisclosureCreate,
    ESGDisclosureUpdate,
)
from .models.esg_metric import ESGMetric, ESGMetricCreate, ESGMetricUpdate
from .models.sustainability_report import (
    SustainabilityReport,
    SustainabilityReportCreate,
    SustainabilityReportUpdate,
)
from .models.waste_management import (
    WasteManagement,
    WasteManagementCreate,
    WasteManagementUpdate,
)

ESG_METRIC = EntityMeta(
    collection="esg_metrics",
    prefix="ESGM",
    api_path="/api/v1/esg-metrics",
    tag="ESG 지표",
    resource="esg_metric",
    model=ESGMetric,
    create_schema=ESGMetricCreate,
    update_schema=ESGMetricUpdate,
    archetype="master",
    not_found_message="ESG 지표를 찾을 수 없습니다",
)

SUSTAINABILITY_REPORT = EntityMeta(
    collection="sustainability_reports",
    prefix="ESGR",
    api_path="/api/v1/sustainability-reports",
    tag="지속가능성 보고서",
    resource="sustainability_report",
    model=SustainabilityReport,
    create_schema=SustainabilityReportCreate,
    update_schema=SustainabilityReportUpdate,
    archetype="transaction",
    not_found_message="지속가능성 보고서를 찾을 수 없습니다",
)

CARBON_EMISSION = EntityMeta(
    collection="carbon_emissions",
    prefix="CRBN",
    api_path="/api/v1/carbon-emissions",
    tag="탄소 배출",
    resource="carbon_emission",
    model=CarbonEmission,
    create_schema=CarbonEmissionCreate,
    update_schema=CarbonEmissionUpdate,
    archetype="transaction",
    not_found_message="탄소 배출 기록을 찾을 수 없습니다",
)

WASTE_MANAGEMENT = EntityMeta(
    collection="waste_managements",
    prefix="WST",
    api_path="/api/v1/waste-managements",
    tag="폐기물 관리",
    resource="waste_management",
    model=WasteManagement,
    create_schema=WasteManagementCreate,
    update_schema=WasteManagementUpdate,
    archetype="transaction",
    not_found_message="폐기물 관리 기록을 찾을 수 없습니다",
)

ESG_DISCLOSURE = EntityMeta(
    collection="esg_disclosures",
    prefix="ESGD",
    api_path="/api/v1/esg-disclosures",
    tag="ESG 공시",
    resource="esg_disclosure",
    model=ESGDisclosure,
    create_schema=ESGDisclosureCreate,
    update_schema=ESGDisclosureUpdate,
    archetype="transaction",
    not_found_message="ESG 공시를 찾을 수 없습니다",
)

ENTITY_METAS = [
    ESG_METRIC,
    SUSTAINABILITY_REPORT,
    CARBON_EMISSION,
    WASTE_MANAGEMENT,
    ESG_DISCLOSURE,
]
