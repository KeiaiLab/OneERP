"""Compliance 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

7개 엔티티를 EntityMeta로 선언한다.
위험 매트릭스 보고서는 routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.audit_trail import AuditTrail, AuditTrailCreate, AuditTrailUpdate
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
from .models.data_privacy_record import (
    DataPrivacyRecord,
    DataPrivacyRecordCreate,
    DataPrivacyRecordUpdate,
)
from .models.internal_control import (
    InternalControl,
    InternalControlCreate,
    InternalControlUpdate,
)
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

# --- 마스터 데이터 ---

INTERNAL_CONTROL = EntityMeta(
    collection="internal_controls",
    prefix="IC",
    api_path="/api/v1/internal-controls",
    tag="내부 통제",
    resource="internal_control",
    model=InternalControl,
    create_schema=InternalControlCreate,
    update_schema=InternalControlUpdate,
    archetype="master",
    not_found_message="내부 통제를 찾을 수 없습니다",
)

AUDIT_TRAIL = EntityMeta(
    collection="audit_trails",
    prefix="AT",
    api_path="/api/v1/audit-trails",
    tag="감사 추적",
    resource="audit_trail",
    model=AuditTrail,
    create_schema=AuditTrailCreate,
    update_schema=AuditTrailUpdate,
    archetype="transaction",
    not_found_message="감사 추적을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

COMPLIANCE_CHECKLIST = EntityMeta(
    collection="compliance_checklists",
    prefix="CL",
    api_path="/api/v1/compliance-checklists",
    tag="준수 체크리스트",
    resource="compliance_checklist",
    model=ComplianceChecklist,
    create_schema=ComplianceChecklistCreate,
    update_schema=ComplianceChecklistUpdate,
    archetype="transaction",
    not_found_message="준수 체크리스트를 찾을 수 없습니다",
)

RISK_ASSESSMENT = EntityMeta(
    collection="risk_assessments",
    prefix="RA",
    api_path="/api/v1/risk-assessments",
    tag="위험 평가",
    resource="risk_assessment",
    model=RiskAssessment,
    create_schema=RiskAssessmentCreate,
    update_schema=RiskAssessmentUpdate,
    archetype="transaction",
    not_found_message="위험 평가를 찾을 수 없습니다",
)

COMPLIANCE_REPORT = EntityMeta(
    collection="compliance_reports",
    prefix="CRP",
    api_path="/api/v1/compliance-reports",
    tag="컴플라이언스 보고서",
    resource="compliance_report",
    model=ComplianceReport,
    create_schema=ComplianceReportCreate,
    update_schema=ComplianceReportUpdate,
    archetype="transaction",
    not_found_message="컴플라이언스 보고서를 찾을 수 없습니다",
)

DATA_PRIVACY_RECORD = EntityMeta(
    collection="data_privacy_records",
    prefix="DPR",
    api_path="/api/v1/data-privacy-records",
    tag="개인정보 처리 기록부",
    resource="data_privacy_record",
    model=DataPrivacyRecord,
    create_schema=DataPrivacyRecordCreate,
    update_schema=DataPrivacyRecordUpdate,
    archetype="master",
    not_found_message="개인정보 처리 기록부를 찾을 수 없습니다",
)

REGULATORY_SANDBOX = EntityMeta(
    collection="regulatory_sandboxes",
    prefix="RSBOX",
    api_path="/api/v1/regulatory-sandboxes",
    tag="규제 샌드박스",
    resource="regulatory_sandbox",
    model=RegulatorySandbox,
    create_schema=RegulatorySandboxCreate,
    update_schema=RegulatorySandboxUpdate,
    archetype="master",
    not_found_message="규제 샌드박스를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    INTERNAL_CONTROL,
    DATA_PRIVACY_RECORD,
    REGULATORY_SANDBOX,
    # 트랜잭션
    AUDIT_TRAIL,
    COMPLIANCE_CHECKLIST,
    RISK_ASSESSMENT,
    COMPLIANCE_REPORT,
]
