from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("domain", "minimum_paths"),
    [
        ("selling", 100),
        ("buying", 50),
        ("stock", 90),
    ],
)
def test_sales_scm_domains_serve_openapi_schema(
    monkeypatch: pytest.MonkeyPatch,
    domain: str,
    minimum_paths: int,
) -> None:
    monkeypatch.setenv("ONEERP_JWT_SECRET", "test-openapi-contract-secret-0000")
    monkeypatch.setenv("ONEERP_DEBUG", "true")

    module = importlib.import_module("plane_api.main")
    client = TestClient(module.app)

    response = client.get(f"/{domain}/openapi.json")

    assert response.status_code == 200
    assert len(response.json().get("paths", {})) >= minimum_paths
