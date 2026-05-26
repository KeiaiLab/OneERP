"""서비스수준협약(ServiceLevelAgreement) 문서 모델 — Support 모듈."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ServiceLevelAgreementCreate(BaseModel):
    """SLA 생성 요청 스키마."""

    sla_name: str
    entity_type: str = "issue"
    response_time: Decimal = Decimal(0)
    resolution_time: Decimal = Decimal(0)
    priority: str = "medium"
    is_active: bool = True


class ServiceLevelAgreementUpdate(BaseModel):
    """SLA 수정 요청 스키마."""

    sla_name: str | None = None
    entity_type: str | None = None
    response_time: Decimal | None = None
    resolution_time: Decimal | None = None
    priority: str | None = None
    is_active: bool | None = None


class ServiceLevelAgreement(BaseDocument):
    """서비스수준협약 문서 — Support SLA 마스터.

    naming prefix: SLA
    """

    sla_name: str = ""
    entity_type: str = "issue"
    response_time: Decimal = Decimal(0)
    resolution_time: Decimal = Decimal(0)
    priority: str = "medium"
    is_active: bool = True
