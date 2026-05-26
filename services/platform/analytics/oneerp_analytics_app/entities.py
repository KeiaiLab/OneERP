"""Analytics 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

16개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.carbon_emission import (
    CarbonEmission,
    CarbonEmissionCreate,
    CarbonEmissionUpdate,
)
from .models.compliance_checklist import (
    ComplianceChecklist,
    ComplianceChecklistCreate,
    ComplianceChecklistUpdate,
)
from .models.compliance_report import (
    ComplianceReport,
    ComplianceReportCreate,
    ComplianceReportUpdate,
)
from .models.custom_report import CustomReport, CustomReportCreate, CustomReportUpdate
from .models.dashboard import Dashboard, DashboardCreate, DashboardUpdate
from .models.dashboard_widget import (
    DashboardWidget,
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
)
from .models.data_source import DataSource, DataSourceCreate, DataSourceUpdate
from .models.esg_disclosure import (
    ESGDisclosure,
    ESGDisclosureCreate,
    ESGDisclosureUpdate,
)
from .models.esg_metric import ESGMetric, ESGMetricCreate, ESGMetricUpdate
from .models.internal_control import (
    InternalControl,
    InternalControlCreate,
    InternalControlUpdate,
)
from .models.kpi_definition import (
    KPIDefinition,
    KPIDefinitionCreate,
    KPIDefinitionUpdate,
)
from .models.kpi_snapshot import KPISnapshot, KPISnapshotCreate, KPISnapshotUpdate
from .models.regulatory_sandbox import (
    RegulatorySandbox,
    RegulatorySandboxCreate,
    RegulatorySandboxUpdate,
)
from .models.risk_assessment import (
    RiskAssessment,
    RiskAssessmentCreate,
    RiskAssessmentUpdate,
)
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

# --- 마스터 데이터 ---

DASHBOARD = EntityMeta(
    collection="dashboards",
    prefix="DASH",
    api_path="/api/v1/dashboards",
    tag="대시보드",
    resource="dashboard",
    model=Dashboard,
    create_schema=DashboardCreate,
    update_schema=DashboardUpdate,
    archetype="master",
    not_found_message="대시보드를 찾을 수 없습니다",
)

KPI_DEFINITION = EntityMeta(
    collection="kpi_definitions",
    prefix="KPID",
    api_path="/api/v1/kpi-definitions",
    tag="KPI 정의",
    resource="kpi_definition",
    model=KPIDefinition,
    create_schema=KPIDefinitionCreate,
    update_schema=KPIDefinitionUpdate,
    archetype="master",
    not_found_message="KPI 정의를 찾을 수 없습니다",
)

DATA_SOURCE = EntityMeta(
    collection="data_sources",
    prefix="DSRC",
    api_path="/api/v1/data-sources",
    tag="데이터 소스",
    resource="data_source",
    model=DataSource,
    create_schema=DataSourceCreate,
    update_schema=DataSourceUpdate,
    archetype="master",
    not_found_message="데이터 소스를 찾을 수 없습니다",
)

INTERNAL_CONTROL = EntityMeta(
    collection="internal_controls",
    prefix="ICTRL",
    api_path="/api/v1/internal-controls",
    tag="내부 통제",
    resource="internal_control",
    model=InternalControl,
    create_schema=InternalControlCreate,
    update_schema=InternalControlUpdate,
    archetype="master",
    not_found_message="내부 통제를 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

CUSTOM_REPORT = EntityMeta(
    collection="custom_reports",
    prefix="CUSRPT",
    api_path="/api/v1/custom-reports",
    tag="커스텀 보고서",
    resource="custom_report",
    model=CustomReport,
    create_schema=CustomReportCreate,
    update_schema=CustomReportUpdate,
    archetype="transaction",
    not_found_message="커스텀 보고서를 찾을 수 없습니다",
)

DASHBOARD_WIDGET = EntityMeta(
    collection="dashboard_widgets",
    prefix="DWGT",
    api_path="/api/v1/dashboard-widgets",
    tag="대시보드 위젯",
    resource="dashboard_widget",
    model=DashboardWidget,
    create_schema=DashboardWidgetCreate,
    update_schema=DashboardWidgetUpdate,
    archetype="transaction",
    not_found_message="대시보드 위젯을 찾을 수 없습니다",
)

KPI_SNAPSHOT = EntityMeta(
    collection="kpi_snapshots",
    prefix="KPIS",
    api_path="/api/v1/kpi-snapshots",
    tag="KPI 스냅샷",
    resource="kpi_snapshot",
    model=KPISnapshot,
    create_schema=KPISnapshotCreate,
    update_schema=KPISnapshotUpdate,
    archetype="transaction",
    not_found_message="KPI 스냅샷을 찾을 수 없습니다",
)

COMPLIANCE_CHECKLIST = EntityMeta(
    collection="compliance_checklists",
    prefix="CCHL",
    api_path="/api/v1/compliance-checklists",
    tag="컴플라이언스 체크리스트",
    resource="compliance_checklist",
    model=ComplianceChecklist,
    create_schema=ComplianceChecklistCreate,
    update_schema=ComplianceChecklistUpdate,
    archetype="transaction",
    not_found_message="컴플라이언스 체크리스트를 찾을 수 없습니다",
)

RISK_ASSESSMENT = EntityMeta(
    collection="risk_assessments",
    prefix="RISK",
    api_path="/api/v1/risk-assessments",
    tag="리스크 평가",
    resource="risk_assessment",
    model=RiskAssessment,
    create_schema=RiskAssessmentCreate,
    update_schema=RiskAssessmentUpdate,
    archetype="transaction",
    not_found_message="리스크 평가를 찾을 수 없습니다",
)

COMPLIANCE_REPORT = EntityMeta(
    collection="compliance_reports",
    prefix="CRPT",
    api_path="/api/v1/compliance-reports",
    tag="컴플라이언스 보고서",
    resource="compliance_report",
    model=ComplianceReport,
    create_schema=ComplianceReportCreate,
    update_schema=ComplianceReportUpdate,
    archetype="transaction",
    not_found_message="컴플라이언스 보고서를 찾을 수 없습니다",
)

REGULATORY_SANDBOX = EntityMeta(
    collection="regulatory_sandboxes",
    prefix="RGSB",
    api_path="/api/v1/regulatory-sandboxes",
    tag="규제 샌드박스",
    resource="regulatory_sandbox",
    model=RegulatorySandbox,
    create_schema=RegulatorySandboxCreate,
    update_schema=RegulatorySandboxUpdate,
    archetype="transaction",
    not_found_message="규제 샌드박스를 찾을 수 없습니다",
)

CARBON_EMISSION = EntityMeta(
    collection="carbon_emissions",
    prefix="CARB",
    api_path="/api/v1/carbon-emissions",
    tag="탄소 배출",
    resource="carbon_emission",
    model=CarbonEmission,
    create_schema=CarbonEmissionCreate,
    update_schema=CarbonEmissionUpdate,
    archetype="transaction",
    not_found_message="탄소 배출을 찾을 수 없습니다",
)

ESG_METRIC = EntityMeta(
    collection="esg_metrics",
    prefix="ESG",
    api_path="/api/v1/esg-metrics",
    tag="ESG 지표",
    resource="esg_metric",
    model=ESGMetric,
    create_schema=ESGMetricCreate,
    update_schema=ESGMetricUpdate,
    archetype="transaction",
    not_found_message="ESG 지표를 찾을 수 없습니다",
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

SUSTAINABILITY_REPORT = EntityMeta(
    collection="sustainability_reports",
    prefix="SRPT",
    api_path="/api/v1/sustainability-reports",
    tag="지속가능성 보고서",
    resource="sustainability_report",
    model=SustainabilityReport,
    create_schema=SustainabilityReportCreate,
    update_schema=SustainabilityReportUpdate,
    archetype="transaction",
    not_found_message="지속가능성 보고서를 찾을 수 없습니다",
)

WASTE_MANAGEMENT = EntityMeta(
    collection="waste_managements",
    prefix="WSTM",
    api_path="/api/v1/waste-managements",
    tag="폐기물 관리",
    resource="waste_management",
    model=WasteManagement,
    create_schema=WasteManagementCreate,
    update_schema=WasteManagementUpdate,
    archetype="transaction",
    not_found_message="폐기물 관리를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    DASHBOARD,
    KPI_DEFINITION,
    DATA_SOURCE,
    INTERNAL_CONTROL,
    # 트랜잭션
    CUSTOM_REPORT,
    DASHBOARD_WIDGET,
    KPI_SNAPSHOT,
    COMPLIANCE_CHECKLIST,
    RISK_ASSESSMENT,
    COMPLIANCE_REPORT,
    REGULATORY_SANDBOX,
    CARBON_EMISSION,
    ESG_METRIC,
    ESG_DISCLOSURE,
    SUSTAINABILITY_REPORT,
    WASTE_MANAGEMENT,
]
