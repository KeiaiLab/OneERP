"""PLM 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

7개 엔티티 중 Product, BOMVersion, ECO는 커스텀 라우트로 관리하고,
ECN, Drawing, Certification, PartApproval은 EntityMeta CRUD를 사용한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.certification import Certification, CertificationCreate, CertificationUpdate
from .models.drawing import Drawing, DrawingCreate, DrawingUpdate
from .models.eng_change_notice import ECNCreate, ECNUpdate, EngChangeNotice
from .models.part_approval import PartApproval, PartApprovalCreate, PartApprovalUpdate

ECN = EntityMeta(
    collection="eng_change_notices",
    prefix="ECN",
    api_path="/api/v1/plm/ecn",
    tag="PLM ECN",
    resource="plm_ecn",
    model=EngChangeNotice,
    create_schema=ECNCreate,
    update_schema=ECNUpdate,
    archetype="transaction",
    not_found_message="ECN을 찾을 수 없습니다",
)

DRAWING = EntityMeta(
    collection="drawings",
    prefix="DWG",
    api_path="/api/v1/plm/drawings",
    tag="PLM 도면",
    resource="plm_drawing",
    model=Drawing,
    create_schema=DrawingCreate,
    update_schema=DrawingUpdate,
    archetype="master",
    not_found_message="도면을 찾을 수 없습니다",
)

CERTIFICATION = EntityMeta(
    collection="certifications",
    prefix="CERT",
    api_path="/api/v1/plm/certifications",
    tag="PLM 인증",
    resource="plm_certification",
    model=Certification,
    create_schema=CertificationCreate,
    update_schema=CertificationUpdate,
    archetype="master",
    not_found_message="인증을 찾을 수 없습니다",
)

PART_APPROVAL = EntityMeta(
    collection="part_approvals",
    prefix="PAR",
    api_path="/api/v1/plm/part-approvals",
    tag="PLM 부품승인",
    resource="plm_part_approval",
    model=PartApproval,
    create_schema=PartApprovalCreate,
    update_schema=PartApprovalUpdate,
    archetype="transaction",
    not_found_message="부품 승인을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    ECN,
    DRAWING,
    CERTIFICATION,
    PART_APPROVAL,
]
