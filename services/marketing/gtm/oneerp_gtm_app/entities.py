"""GTM 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용."""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.compliance_check import ComplianceCheck, ComplianceCheckCreate, ComplianceCheckUpdate
from .models.export_license import ExportLicense, ExportLicenseCreate, ExportLicenseUpdate
from .models.hs_classification import (
    HSClassification,
    HSClassificationCreate,
    HSClassificationUpdate,
)
from .models.origin_certificate import (
    OriginCertificate,
    OriginCertificateCreate,
    OriginCertificateUpdate,
)
from .models.trade_agreement import TradeAgreement, TradeAgreementCreate, TradeAgreementUpdate

ENTITY_METAS: list[EntityMeta] = [
    EntityMeta(
        collection="trade_agreements",
        prefix="TA",
        api_path="/api/v1/gtm/trade-agreements",
        tag="무역협정",
        resource="trade_agreement",
        model=TradeAgreement,
        create_schema=TradeAgreementCreate,
        update_schema=TradeAgreementUpdate,
        archetype="master",
        not_found_message="무역협정을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="hs_classifications",
        prefix="HSC",
        api_path="/api/v1/gtm/hs-classifications",
        tag="HS분류",
        resource="hs_classification",
        model=HSClassification,
        create_schema=HSClassificationCreate,
        update_schema=HSClassificationUpdate,
        archetype="master",
        not_found_message="HS 분류를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="export_licenses",
        prefix="EXL",
        api_path="/api/v1/gtm/export-licenses",
        tag="수출허가",
        resource="export_license",
        model=ExportLicense,
        create_schema=ExportLicenseCreate,
        update_schema=ExportLicenseUpdate,
        archetype="transaction",
        not_found_message="수출허가를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="compliance_checks",
        prefix="CCK",
        api_path="/api/v1/gtm/compliance-checks",
        tag="준수점검",
        resource="compliance_check",
        model=ComplianceCheck,
        create_schema=ComplianceCheckCreate,
        update_schema=ComplianceCheckUpdate,
        archetype="transaction",
        not_found_message="준수점검을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="origin_certificates",
        prefix="ORC",
        api_path="/api/v1/gtm/origin-certificates",
        tag="원산지증명서",
        resource="origin_certificate",
        model=OriginCertificate,
        create_schema=OriginCertificateCreate,
        update_schema=OriginCertificateUpdate,
        archetype="transaction",
        not_found_message="원산지증명서를 찾을 수 없습니다",
    ),
]
