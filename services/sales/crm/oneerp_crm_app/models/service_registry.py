"""서비스 레지스트리 모델 — 등록된 마이크로서비스 정보."""

from __future__ import annotations

from pydantic import BaseModel


class ServiceInfo(BaseModel):
    """서비스 레지스트리 항목."""

    name: str
    url: str
    health_url: str
    status: str = "unknown"
