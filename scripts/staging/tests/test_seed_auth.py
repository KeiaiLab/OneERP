"""seed_auth 유닛 테스트 — realm 구성 계약 검증."""

from __future__ import annotations

from scripts.staging.seed_auth import build_realm


def test_build_realm_has_three_users_and_one_client() -> None:
    realm = build_realm()
    assert realm["realm"] == "oneerp-staging"
    assert realm["enabled"] is True
    assert len(realm["users"]) == 3
    assert {u["username"] for u in realm["users"]} == {
        "stg-user-1",
        "stg-user-2",
        "stg-user-3",
    }
    assert len(realm["clients"]) == 1
    client = realm["clients"][0]
    assert client["clientId"] == "oneerp-web"
    assert client["standardFlowEnabled"] is True
    assert client["attributes"]["pkce.code.challenge.method"] == "S256"
    mapper_names = {mapper["name"] for mapper in client["protocolMappers"]}
    assert {"tenant_id", "roles"} <= mapper_names
