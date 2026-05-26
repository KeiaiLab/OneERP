"""E2E: 전체 서비스 헬스체크 검증."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.conftest import SERVICE_PORTS

pytestmark = pytest.mark.e2e


class TestHealthCheck:
    """모든 서비스의 /health 엔드포인트가 정상 응답하는지 검증한다."""

    @pytest.mark.parametrize(
        ("service_name", "expected_service"),
        [(name, name) for name in SERVICE_PORTS],
    )
    def test_헬스체크_응답(
        self,
        services: dict[str, str],
        service_name: str,
        expected_service: str,
    ) -> None:
        """각 서비스의 /health가 status=ok, service, version을 반환한다."""
        with httpx.Client(base_url=services[service_name], timeout=5.0) as client:
            resp = client.get("/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == expected_service
        assert "version" in body
