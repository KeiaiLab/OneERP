"""staging Keycloak 시드 JSON (admin-cli import 대상)."""

from __future__ import annotations

from typing import Any


def build_realm() -> dict[str, Any]:
    """staging 용 Keycloak realm 구성 반환 — user 3 + public client 1."""
    return {
        "realm": "oneerp-staging",
        "enabled": True,
        "users": [
            {
                "username": f"stg-user-{i}",
                "enabled": True,
                "credentials": [{"type": "password", "value": f"StgP@ss{i}"}],
            }
            for i in (1, 2, 3)
        ],
        "clients": [
            {
                "clientId": "oneerp-web",
                "publicClient": True,
                "redirectUris": ["https://staging.oneerp.dev/*"],
                "standardFlowEnabled": True,
                "attributes": {"pkce.code.challenge.method": "S256"},
                "protocolMappers": [
                    {
                        "name": "tenant_id",
                        "protocol": "openid-connect",
                        "protocolMapper": "oidc-usermodel-attribute-mapper",
                        "config": {
                            "user.attribute": "tenant_id",
                            "claim.name": "tenant_id",
                            "jsonType.label": "String",
                            "id.token.claim": "true",
                            "access.token.claim": "true",
                        },
                    },
                    {
                        "name": "roles",
                        "protocol": "openid-connect",
                        "protocolMapper": "oidc-usermodel-realm-role-mapper",
                        "config": {
                            "claim.name": "roles",
                            "jsonType.label": "String",
                            "multivalued": "true",
                            "id.token.claim": "true",
                            "access.token.claim": "true",
                        },
                    },
                ],
            }
        ],
    }


def main() -> None:
    """CLI 엔트리 — realm JSON 출력."""
    import json
    import sys

    json.dump(build_realm(), sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
