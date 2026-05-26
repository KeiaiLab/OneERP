"""E2E API 호출 헬퍼 — 생성/제출/폴링을 단순화한다."""

from __future__ import annotations

import time
from typing import Any

import httpx

HEADERS = {
    "X-Tenant-Id": "test",
    "X-User-Sub": "e2e-test",
    "X-User-Roles": "admin",
    "X-User-Permissions": "*:*",
    "X-User-Tier": "super_admin",
}


def create_doc(client: httpx.Client, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
    """문서를 생성하고 응답 JSON을 반환한다."""
    resp = client.post(f"/api/v1/{endpoint}", json=data, headers=HEADERS)
    assert resp.status_code == 201, f"생성 실패: {resp.status_code} {resp.text}"
    return resp.json()


def submit_doc(client: httpx.Client, endpoint: str, doc_id: str) -> dict[str, Any]:
    """문서를 제출(submit)하고 응답 JSON을 반환한다."""
    resp = client.post(f"/api/v1/{endpoint}/{doc_id}/submit", headers=HEADERS)
    assert resp.status_code == 200, f"제출 실패: {resp.status_code} {resp.text}"
    return resp.json()


def create_and_submit(client: httpx.Client, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
    """문서를 생성한 뒤 즉시 제출한다."""
    doc = create_doc(client, endpoint, data)
    doc_id = doc.get("_id") or doc.get("id") or ""
    return submit_doc(client, endpoint, doc_id)


def poll_until(
    client: httpx.Client,
    url: str,
    *,
    check_field: str,
    expected: object,
    timeout: float = 10.0,
    interval: float = 0.5,
) -> dict[str, Any]:
    """응답의 특정 필드가 기대값이 될 때까지 폴링한다."""
    deadline = time.monotonic() + timeout
    last_body: dict[str, Any] = {}
    while time.monotonic() < deadline:
        resp = client.get(url, headers=HEADERS)
        if resp.status_code == 200:
            last_body = resp.json()
            if "data" in last_body and isinstance(last_body["data"], list):
                for item in last_body["data"]:
                    if item.get(check_field) == expected:
                        return last_body
            elif last_body.get(check_field) == expected:
                return last_body
        time.sleep(interval)
    msg = f"{url}에서 {check_field}=={expected} 대기 실패 ({timeout}초). 마지막 응답: {last_body}"
    raise TimeoutError(msg)


def get_doc(client: httpx.Client, endpoint: str, doc_id: str) -> dict[str, Any]:
    """문서 단건을 조회한다."""
    resp = client.get(f"/api/v1/{endpoint}/{doc_id}", headers=HEADERS)
    assert resp.status_code == 200, f"조회 실패: {resp.status_code} {resp.text}"
    return resp.json()


def list_docs(client: httpx.Client, endpoint: str, **params: Any) -> list[dict[str, Any]]:
    """문서 목록을 조회한다."""
    resp = client.get(f"/api/v1/{endpoint}", params=params, headers=HEADERS)
    assert resp.status_code == 200, f"목록 조회 실패: {resp.status_code} {resp.text}"
    body = resp.json()
    return body.get("data", []) if isinstance(body, dict) else body
