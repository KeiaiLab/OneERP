"""CLM 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

3개 엔티티를 EntityMeta로 선언한다.
ContractTemplate(마스터), Contract(트랜잭션), ContractRenewal(트랜잭션).
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.contract import Contract, ContractCreate, ContractUpdate
from .models.contract_renewal import (
    ContractRenewal,
    ContractRenewalCreate,
    ContractRenewalUpdate,
)
from .models.contract_template import (
    ContractTemplate,
    ContractTemplateCreate,
    ContractTemplateUpdate,
)

CONTRACT_TEMPLATE = EntityMeta(
    collection="contract_templates",
    prefix="CTT",
    api_path="/api/v1/contract-templates",
    tag="계약 템플릿",
    resource="contract_template",
    model=ContractTemplate,
    create_schema=ContractTemplateCreate,
    update_schema=ContractTemplateUpdate,
    archetype="master",
    not_found_message="계약 템플릿을 찾을 수 없습니다",
)

CONTRACT = EntityMeta(
    collection="contracts",
    prefix="CTR",
    api_path="/api/v1/contracts",
    tag="계약",
    resource="contract",
    model=Contract,
    create_schema=ContractCreate,
    update_schema=ContractUpdate,
    archetype="transaction",
    not_found_message="계약을 찾을 수 없습니다",
)

CONTRACT_RENEWAL = EntityMeta(
    collection="contract_renewals",
    prefix="CTRN",
    api_path="/api/v1/contract-renewals",
    tag="계약 갱신",
    resource="contract_renewal",
    model=ContractRenewal,
    create_schema=ContractRenewalCreate,
    update_schema=ContractRenewalUpdate,
    archetype="transaction",
    not_found_message="계약 갱신을 찾을 수 없습니다",
)

ENTITY_METAS = [
    CONTRACT_TEMPLATE,
    CONTRACT,
    CONTRACT_RENEWAL,
]
