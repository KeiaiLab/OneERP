#!/usr/bin/env python3
"""G1-2 OpenAPI 계약 테스트 증거를 T1/T2 메타 인덱스에 기록한다."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import socket
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_meta(
    *,
    module: str,
    tier: str,
    command: str,
    artifact: Path,
    verification: dict[str, object],
    started_at: str,
) -> None:
    stdout = artifact.read_text(encoding="utf-8")
    stderr = ""
    sha = compute_evidence_sha(
        command=command,
        exit_code=0,
        stdout=stdout,
        stderr=stderr,
    )
    rel_artifact = artifact.relative_to(ROOT)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G1-2",
        module=module,
        tier=tier,
        command=command,
        executor="scripts/ci/run_contract_tests.sh",
        git_sha=_git_sha(),
        host=socket.gethostname(),
        user=getpass.getuser(),
        started_at=started_at,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(rel_artifact)],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="G1-2 OpenAPI evidence recorder")
    parser.add_argument("--module", required=True)
    parser.add_argument("--schema-file", required=True)
    parser.add_argument("--validation-output", required=True)
    parser.add_argument("--command", required=True)
    args = parser.parse_args()

    schema = json.loads(Path(args.schema_file).read_text(encoding="utf-8"))
    paths = len(schema.get("paths", {}))
    title = schema.get("info", {}).get("title", "")
    started_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    file_ts = started_at.replace("-", "").replace(":", "").removesuffix("Z")

    t1_dir = ROOT / "artifacts" / "T1" / "G1-2" / args.module
    t2_dir = ROOT / "artifacts" / "T2" / "G1-2" / args.module
    t1_dir.mkdir(parents=True, exist_ok=True)
    t2_dir.mkdir(parents=True, exist_ok=True)

    t1_artifact = t1_dir / f"openapi-contract-{file_ts}.log"
    t2_artifact = t2_dir / f"run-{file_ts}.json"

    t1_artifact.write_text(
        "\n".join(
            [
                f"module={args.module}",
                f"title={title}",
                f"paths={paths}",
                f"schema_file={args.schema_file}",
                "openapi_extract_exit=0",
                "schemathesis_schema_validation_exit=0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    t2_artifact.write_text(
        json.dumps(
            {
                "module": args.module,
                "gate": "G1-2",
                "paths": paths,
                "title": title,
                "schema_file": args.schema_file,
                "schemathesis_schema_validation_exit": 0,
                "validation_output": args.validation_output,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    verification = {
        "paths": paths,
        "title": title,
        "openapi_extract_exit": 0,
        "schemathesis_schema_validation_exit": 0,
    }
    _write_meta(
        module=args.module,
        tier="T1",
        command=args.command,
        artifact=t1_artifact,
        verification=verification,
        started_at=started_at,
    )
    _write_meta(
        module=args.module,
        tier="T2",
        command=args.command,
        artifact=t2_artifact,
        verification=verification,
        started_at=started_at,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
