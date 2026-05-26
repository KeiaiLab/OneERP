"""G3-1 authN · G3-2 시크릿 · G3-3 RBAC · G3-4 감사 이벤트 · G3-5 의존성."""

from __future__ import annotations

from pathlib import Path

from scripts.audit.gates import module_service_dir
from scripts.engine.validators import (
    GateResult,
    GateStatus,
    ValidationSpec,
    validate_evidence,
)


def gate_G3_1_authn(gate: str, module: str) -> GateResult:
    """OIDC 라우트 + auth 테스트 7종 pass (T1+T2)."""
    tests = Path(f"tests/security/{module}")
    if not tests.exists() or not list(tests.glob("test_auth_*.py")):
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"tests/security/{module}/test_auth_*.py 없음",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1", "T2"],
            artifact_glob={
                "T1": f"artifacts/T1/G3-1/{module}/*.log",
                "T2": f"artifacts/T2/G3-1/{module}/run-*.json",
            },
            verification_fields={
                "auth_tests_defined": {"gte": 7},
                "core_issuer_audience_verified": {"eq": 1},
                "oidc_inventory_claims": {"eq": 1},
                "externalsecret_defined": {"eq": 1},
                "jwt_secret_externalized": {"eq": 1},
                "httproute_defined": {"eq": 1},
                "rbac_default_deny": {"eq": 1},
                "runbook_auth_triage": {"eq": 1},
                "static_eval_passed": {"eq": 1},
            },
        ),
        gate=gate,
        module=module,
    )


def gate_G3_2_secret(gate: str, module: str) -> GateResult:
    """ExternalSecrets + rotation 스크립트 + T2 rotation 로그."""
    eso = Path(f"deploy/secrets/{module}/externalsecret.yaml")
    if not eso.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{eso} 없음",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T2"],
            artifact_glob={"T2": f"artifacts/secrets/{module}-rotation-*.log"},
            verification_fields={
                "externalsecret_defined": {"eq": 1},
                "vault_store_ref": {"eq": 1},
                "remote_refs": {"gte": 3},
                "rotation_log_lines": {"gte": 8},
            },
        ),
        gate=gate,
        module=module,
    )


def gate_G3_3_rbac(gate: str, module: str) -> GateResult:
    """OPA 정책 + 테스트 5+ pass."""
    pol_dir = Path(f"policies/{module}")
    if not pol_dir.exists() or not list(pol_dir.glob("*.rego")):
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"policies/{module}/*.rego 없음",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/T1/G3-3/{module}/*.log"},
            verification_fields={
                "policy_files": {"gte": 2},
                "rego_tests_defined": {"gte": 5},
                "default_deny": {"eq": 1},
                "least_privilege_rules": {"gte": 3},
                "opa_exit": {"eq": 0},
                "opa_tests_passed": {"gte": 5},
            },
        ),
        gate=gate,
        module=module,
    )


def gate_G3_4_audit(gate: str, module: str) -> GateResult:
    """audit_hooks.py 존재 · route 호출 증거 (T1)."""
    svc = module_service_dir(module)
    hooks = list(svc.rglob("audit_hooks.py"))
    if not hooks:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"audit_hooks.py 없음 ({svc})",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/T1/G3-4/{module}/*.log"},
            verification_fields={
                "audit_hooks_found": {"gte": 1},
                "audit_actions_defined": {"gte": 5},
                "emit_helper_found": {"eq": 1},
            },
        ),
        gate=gate,
        module=module,
    )


def gate_G3_5_dep(gate: str, module: str) -> GateResult:
    """pip-audit/pnpm audit — high/critical CVE 0건 (7일 이내)."""
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/dep-audit/{module}-*.log"},
            verification_fields={
                "pip_audit_exit": {"eq": 0},
                "pnpm_audit_exit": {"eq": 0},
                "high_critical_cve": {"eq": 0},
            },
        ),
        gate=gate,
        module=module,
    )
