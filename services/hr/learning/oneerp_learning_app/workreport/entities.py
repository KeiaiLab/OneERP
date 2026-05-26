"""WorkReport 서비스 엔티티 메타 선언.

3개 엔티티를 EntityMeta로 선언한다.
업무일지(WorkReport)는 커스텀 라우터(제출/승인/반려/취소)를 사용하므로
ENTITY_METAS에는 포함하지 않는다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.work_report import (
    WorkReport,
    WorkReportCreate,
    WorkReportUpdate,
)
from .models.work_report_comment import (
    WorkReportComment,
    WorkReportCommentCreate,
    WorkReportCommentUpdate,
)
from .models.work_report_template import (
    WorkReportTemplate,
    WorkReportTemplateCreate,
    WorkReportTemplateUpdate,
)

# --- 마스터 데이터 ---

WORK_REPORT_TEMPLATE = EntityMeta(
    collection="work_report_templates",
    prefix="WRT",
    api_path="/api/v1/work-report-templates",
    tag="업무일지템플릿",
    resource="work_report_template",
    model=WorkReportTemplate,
    create_schema=WorkReportTemplateCreate,
    update_schema=WorkReportTemplateUpdate,
    archetype="master",
    not_found_message="업무일지 템플릿을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

WORK_REPORT = EntityMeta(
    collection="work_reports",
    prefix="WR",
    api_path="/api/v1/work-reports",
    tag="업무일지",
    resource="work_report",
    model=WorkReport,
    create_schema=WorkReportCreate,
    update_schema=WorkReportUpdate,
    archetype="transaction",
    not_found_message="업무일지를 찾을 수 없습니다",
)

WORK_REPORT_COMMENT = EntityMeta(
    collection="work_report_comments",
    prefix="WRC",
    api_path="/api/v1/work-report-comments",
    tag="업무일지코멘트",
    resource="work_report_comment",
    model=WorkReportComment,
    create_schema=WorkReportCommentCreate,
    update_schema=WorkReportCommentUpdate,
    archetype="transaction",
    not_found_message="업무일지 코멘트를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
# — 모든 엔티티가 커스텀 라우터(extra_routers)를 사용하므로
#   자동 CRUD 생성 대상은 없다.
ENTITY_METAS: list[EntityMeta] = []
