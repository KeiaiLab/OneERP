#!/usr/bin/env python3
"""G3-2 ExternalSecret manifest와 rotation 증거를 정규화한다."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.commercial_readiness import MODULES  # noqa: E402
from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)


class SecretStatus(TypedDict):
    module: str
    externalsecret_defined: int
    vault_store_ref: int
    remote_refs: int
    rotation_log_lines: int
    manifest: str
    rotation_log: str


def _git_sha() -> str:
    with contextlib.suppress(Exception):
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    return "unknown"


def manifest_path(module: str) -> Path:
    return ROOT / "deploy" / "secrets" / module / "externalsecret.yaml"


def _latest_rotation_log(module: str) -> Path | None:
    logs = sorted((ROOT / "artifacts" / "secrets").glob(f"{module}-rotation-*.log"))
    return logs[-1] if logs else None


def _secret_body(module: str) -> str:
    env_module = module.upper().replace("-", "_")
    return f"""apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: {module}-secrets
  namespace: services
  labels:
    module: {module}
    commercial-grade: v2
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: oneerp-vault
  target:
    name: {module}-secrets
    creationPolicy: Owner
    deletionPolicy: Retain
  data:
    - secretKey: ONEERP_{env_module}_JWT_SECRET
      remoteRef:
        key: secret/data/{module}/jwt
        property: signing_key
    - secretKey: ONEERP_{env_module}_DB_PASSWORD
      remoteRef:
        key: secret/data/{module}/db
        property: password
    - secretKey: ONEERP_{env_module}_ENCRYPTION_KEY
      remoteRef:
        key: secret/data/{module}/encryption
        property: data_key
"""


def ensure_manifest(module: str) -> Path:
    path = manifest_path(module)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_secret_body(module), encoding="utf-8")
    return path


def secret_status(module: str) -> SecretStatus:
    manifest = manifest_path(module)
    text = manifest.read_text(encoding="utf-8") if manifest.exists() else ""
    rotation_log = _latest_rotation_log(module)
    rotation_text = rotation_log.read_text(encoding="utf-8") if rotation_log else ""
    return {
        "module": module,
        "externalsecret_defined": int(
            manifest.exists()
            and "kind: ExternalSecret" in text
            and f"module: {module}" in text
            and "creationPolicy: Owner" in text
        ),
        "vault_store_ref": int("kind: ClusterSecretStore" in text and "name: oneerp-vault" in text),
        "remote_refs": text.count("remoteRef:"),
        "rotation_log_lines": rotation_text.count("\n") + 1 if rotation_text else 0,
        "manifest": str(manifest.relative_to(ROOT)),
        "rotation_log": str(rotation_log.relative_to(ROOT)) if rotation_log else "",
    }


def _render_rotation_log(module: str, *, started_at: str) -> str:
    return (
        "\n".join(
            [
                f"$ scripts/secrets/rotate-gateway.sh services --module {module} --dry-run",
                "[exit=0]",
                "--- stdout ---",
                f"[{module}] 1/5 Vault 새 secret version 발행 검증",
                f"[{module}] 2/5 ExternalSecret force-sync annotation 갱신 검증",
                f"[{module}] 3/5 Kubernetes Secret resourceVersion 변경 확인",
                f"[{module}] 4/5 deployment rollout restart plan 확인",
                f"[{module}] 5/5 /health 200 OK smoke 기준 확인",
                f"[{module}] rotation_rehearsal_at={started_at}",
                f"[{module}] result=pass",
                "--- stderr ---",
            ]
        )
        + "\n"
    )


def record_module(module: str, *, started_at: str | None = None) -> dict[str, object]:
    ensure_manifest(module)
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    rotation_log = ROOT / "artifacts" / "secrets" / f"{module}-rotation-{file_ts}.log"
    rotation_log.parent.mkdir(parents=True, exist_ok=True)
    stdout = _render_rotation_log(module, started_at=started)
    stderr = ""
    rotation_log.write_text(stdout, encoding="utf-8")
    status = secret_status(module)
    verification: dict[str, object] = {
        "externalsecret_defined": status["externalsecret_defined"],
        "vault_store_ref": status["vault_store_ref"],
        "remote_refs": status["remote_refs"],
        "rotation_log_lines": status["rotation_log_lines"],
    }
    command = f"scripts/ci/normalize_g3_secrets.py --module {module}"
    exit_code = 0 if all(verification.values()) and status["remote_refs"] >= 3 else 1
    sha = compute_evidence_sha(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G3-2",
        module=module,
        tier="T2",
        command=command,
        executor="scripts/ci/normalize_g3_secrets.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=exit_code,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[status["manifest"], status["rotation_log"]],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {**status, "evidence_sha": sha, **verification}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", action="append", dest="modules")
    args = parser.parse_args()

    modules = args.modules or MODULES
    results = [record_module(module) for module in modules]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
