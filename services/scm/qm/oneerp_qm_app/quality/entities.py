"""Quality 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

8개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 5개 엔티티(quality_inspections, quality_inspection_templates,
non_conformances, inspection_results, quality_goals)는 routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.capa import Capa, CapaCreate, CapaUpdate
from .models.certificate_of_analysis import (
    CertificateOfAnalysis,
    CertificateOfAnalysisCreate,
    CertificateOfAnalysisUpdate,
)
from .models.quality_action import QualityAction, QualityActionCreate, QualityActionUpdate
from .models.quality_meeting import QualityMeeting, QualityMeetingCreate, QualityMeetingUpdate
from .models.quality_metric import QualityMetric, QualityMetricCreate, QualityMetricUpdate
from .models.quality_procedure import (
    QualityProcedure,
    QualityProcedureCreate,
    QualityProcedureUpdate,
)
from .models.quality_review import QualityReview, QualityReviewCreate, QualityReviewUpdate
from .models.rma_inspection import RmaInspection, RmaInspectionCreate, RmaInspectionUpdate

# --- 마스터 데이터 ---

QUALITY_PROCEDURE = EntityMeta(
    collection="quality_procedures",
    prefix="QPRC",
    api_path="/api/v1/quality-procedures",
    tag="품질 절차",
    resource="quality_procedure",
    model=QualityProcedure,
    create_schema=QualityProcedureCreate,
    update_schema=QualityProcedureUpdate,
    archetype="master",
    not_found_message="품질 절차를 찾을 수 없습니다",
)

QUALITY_METRIC = EntityMeta(
    collection="quality_metrics",
    prefix="QMET",
    api_path="/api/v1/quality-metrics",
    tag="품질 지표",
    resource="quality_metric",
    model=QualityMetric,
    create_schema=QualityMetricCreate,
    update_schema=QualityMetricUpdate,
    archetype="master",
    not_found_message="품질 지표를 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

QUALITY_REVIEW = EntityMeta(
    collection="quality_reviews",
    prefix="QREV",
    api_path="/api/v1/quality-reviews",
    tag="품질 검토",
    resource="quality_review",
    model=QualityReview,
    create_schema=QualityReviewCreate,
    update_schema=QualityReviewUpdate,
    archetype="transaction",
    not_found_message="품질 검토를 찾을 수 없습니다",
)

QUALITY_ACTION = EntityMeta(
    collection="quality_actions",
    prefix="QACT",
    api_path="/api/v1/quality-actions",
    tag="품질 조치",
    resource="quality_action",
    model=QualityAction,
    create_schema=QualityActionCreate,
    update_schema=QualityActionUpdate,
    archetype="transaction",
    not_found_message="품질 조치를 찾을 수 없습니다",
)

QUALITY_MEETING = EntityMeta(
    collection="quality_meetings",
    prefix="QMTG",
    api_path="/api/v1/quality-meetings",
    tag="품질 회의",
    resource="quality_meeting",
    model=QualityMeeting,
    create_schema=QualityMeetingCreate,
    update_schema=QualityMeetingUpdate,
    archetype="transaction",
    not_found_message="품질 회의를 찾을 수 없습니다",
)

CAPA = EntityMeta(
    collection="capas",
    prefix="CAPA",
    api_path="/api/v1/capas",
    tag="시정예방조치",
    resource="capa",
    model=Capa,
    create_schema=CapaCreate,
    update_schema=CapaUpdate,
    archetype="transaction",
    not_found_message="시정예방조치를 찾을 수 없습니다",
)

CERTIFICATE_OF_ANALYSIS = EntityMeta(
    collection="certificates_of_analysis",
    prefix="COA",
    api_path="/api/v1/certificates-of-analysis",
    tag="분석 성적서",
    resource="certificate_of_analysis",
    model=CertificateOfAnalysis,
    create_schema=CertificateOfAnalysisCreate,
    update_schema=CertificateOfAnalysisUpdate,
    archetype="transaction",
    not_found_message="분석 성적서를 찾을 수 없습니다",
)

RMA_INSPECTION = EntityMeta(
    collection="rma_inspections",
    prefix="RMAI",
    api_path="/api/v1/rma-inspections",
    tag="반품 검사",
    resource="rma_inspection",
    model=RmaInspection,
    create_schema=RmaInspectionCreate,
    update_schema=RmaInspectionUpdate,
    archetype="transaction",
    not_found_message="반품 검사를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    QUALITY_PROCEDURE,
    QUALITY_METRIC,
    # 트랜잭션
    QUALITY_REVIEW,
    QUALITY_ACTION,
    QUALITY_MEETING,
    CAPA,
    CERTIFICATE_OF_ANALYSIS,
    RMA_INSPECTION,
]
