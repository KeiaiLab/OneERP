"""커넥터 모델 — 외부 시스템 연동 커넥터 설정을 관리한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ConnectorCreate(BaseModel):
    """커넥터 생성 요청 스키마."""

    connector_name: str
    connector_type: str = "rest_api"  # rest_api/graphql/sftp/webhook/database/edi
    base_url: str = ""
    auth_type: str = "none"  # none/api_key/oauth2/basic/certificate
    auth_config: dict = {}
    headers: dict = {}
    description: str = ""
    retry_policy: dict = {}  # max_retries, backoff_factor


class ConnectorUpdate(BaseModel):
    """커넥터 수정 요청 스키마."""

    connector_name: str | None = None
    base_url: str | None = None
    auth_type: str | None = None
    auth_config: dict | None = None
    headers: dict | None = None
    description: str | None = None
    is_active: bool | None = None
    retry_policy: dict | None = None


class Connector(BaseDocument):
    """커넥터 문서 — 외부 시스템 연동 설정 정보를 저장한다."""

    connector_name: str = ""
    connector_type: str = "rest_api"
    base_url: str = ""
    auth_type: str = "none"
    auth_config: dict = {}
    headers: dict = {}
    description: str = ""
    is_active: bool = True
    retry_policy: dict = {}
    last_health_check: str = ""
    health_status: str = "unknown"  # unknown/healthy/unhealthy
