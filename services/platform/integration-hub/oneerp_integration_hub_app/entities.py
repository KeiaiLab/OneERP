"""통합허브 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용."""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.connector import Connector, ConnectorCreate, ConnectorUpdate
from .models.data_mapping import DataMapping, DataMappingCreate, DataMappingUpdate
from .models.integration_flow import IntegrationFlow, IntegrationFlowCreate, IntegrationFlowUpdate
from .models.integration_log import IntegrationLog, IntegrationLogCreate, IntegrationLogUpdate
from .models.webhook_endpoint import WebhookEndpoint, WebhookEndpointCreate, WebhookEndpointUpdate

ENTITY_METAS: list[EntityMeta] = [
    EntityMeta(
        collection="connectors",
        prefix="CONN",
        api_path="/api/v1/integration/connectors",
        tag="커넥터",
        resource="connector",
        model=Connector,
        create_schema=ConnectorCreate,
        update_schema=ConnectorUpdate,
        archetype="master",
        not_found_message="커넥터를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="data_mappings",
        prefix="DMAP",
        api_path="/api/v1/integration/data-mappings",
        tag="데이터매핑",
        resource="data_mapping",
        model=DataMapping,
        create_schema=DataMappingCreate,
        update_schema=DataMappingUpdate,
        archetype="master",
        not_found_message="데이터 매핑을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="integration_flows",
        prefix="IFLOW",
        api_path="/api/v1/integration/flows",
        tag="통합플로우",
        resource="integration_flow",
        model=IntegrationFlow,
        create_schema=IntegrationFlowCreate,
        update_schema=IntegrationFlowUpdate,
        archetype="master",
        not_found_message="통합 플로우를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="integration_logs",
        prefix="ILOG",
        api_path="/api/v1/integration/logs",
        tag="통합로그",
        resource="integration_log",
        model=IntegrationLog,
        create_schema=IntegrationLogCreate,
        update_schema=IntegrationLogUpdate,
        archetype="transaction",
        not_found_message="통합 로그를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="webhook_endpoints",
        prefix="WHK",
        api_path="/api/v1/integration/webhooks",
        tag="웹훅",
        resource="webhook_endpoint",
        model=WebhookEndpoint,
        create_schema=WebhookEndpointCreate,
        update_schema=WebhookEndpointUpdate,
        archetype="master",
        not_found_message="웹훅 엔드포인트를 찾을 수 없습니다",
    ),
]
