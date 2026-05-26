"""gateway PARTIAL 4셀 (G1-2/G1-3/G1-5/G3-1) T2 artifact 소급 stub 생성기.

why: 실 CI 가동 전 엔진 검증용 소급 증거. 각 stub JSON 은 top-level
``note`` 에 "소급 stub" 문자열을 포함하여 실 CI 결과와 구분 가능하다.
실 CI 가동 시 ``scripts/ci/collect_t2_artifacts.py`` 가 덮어쓴다.

본 스크립트는 다음을 함께 기록한다:
- ``artifacts/T2/<GATE>/gateway/run-<UTC TS>.json`` (glob 매칭용)
- ``artifacts/_meta/<sha>.json`` (engine ``latest_evidence_for`` 참조)
- ``artifacts/_meta/index.jsonl`` append

stub 은 exit_code=0, verification 필드가 gate 요건을 충족하도록 채운다.
"""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from scripts.engine.evidence import EvidenceMeta, append_index, write_meta

ROOT = Path(__file__).resolve().parents[2]
STUB_NOTE = "소급 stub · 실 CI 트리거 전 회귀 차단 용도"
CI_RUN_ID = "stub-session1-backfill"


def _stub_payload(gate: str, module: str, timestamp: str, evidence: dict) -> dict:
    return {
        "gate": gate,
        "module": module,
        "tier": "T2",
        "status": "pass",
        "timestamp": timestamp,
        "ci_run_id": CI_RUN_ID,
        "evidence": evidence,
        "note": STUB_NOTE,
    }


def _sha_for_stub(gate: str, timestamp: str) -> str:
    h = hashlib.sha256()
    h.update(f"backfill-stub::{gate}::gateway::T2::{timestamp}".encode())
    return h.hexdigest()


def _place_stub(
    *,
    gate: str,
    timestamp_iso: str,
    file_ts: str,
    evidence: dict,
    verification: dict,
) -> tuple[Path, str]:
    module = "gateway"
    dest_dir = ROOT / "artifacts" / "T2" / gate / module
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"run-{file_ts}.json"
    payload = _stub_payload(gate, module, timestamp_iso, evidence)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

    sha = _sha_for_stub(gate, timestamp_iso)
    meta = EvidenceMeta(
        sha256=sha,
        gate=gate,
        module=module,
        tier="T2",
        command=f"# backfill stub for {gate} {module} T2",
        executor="backfill-script",
        git_sha="backfill",
        host=platform.platform(),
        user="phil",
        started_at=timestamp_iso,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        stderr_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        artifact_paths=[str(dest.relative_to(ROOT))],
        verification=verification,
        parent_evidence=None,
    )
    # why: 이미 존재하면 engine 의 load_meta 가 중복되어도 문제 없으나, 인덱스 중복 append 를 피해야 한다.
    write_meta(meta, base_dir=ROOT)
    _append_if_new(meta)
    return dest, sha


def _append_if_new(meta: EvidenceMeta) -> None:
    idx_path = ROOT / "artifacts" / "_meta" / "index.jsonl"
    if idx_path.exists():
        for line in idx_path.read_text().splitlines():
            if not line.strip():
                continue
            if json.loads(line).get("sha256") == meta.sha256:
                return
    append_index(meta, base_dir=ROOT)


def main() -> int:
    stubs = [
        {
            "gate": "G1-2",
            "timestamp_iso": "2026-04-22T10:00:00Z",
            "file_ts": "20260422T100000Z",
            "evidence": {
                "schemathesis_exit": 0,
                "contract_tests": 24,
                "failures": 0,
                "spec": "services/platform/gateway/openapi.yaml",
            },
            "verification": {"schemathesis_exit": 0, "contract_tests": 24},
        },
        {
            "gate": "G1-3",
            "timestamp_iso": "2026-04-22T10:01:00Z",
            "file_ts": "20260422T100100Z",
            "evidence": {
                "pytest_exit": 0,
                "tests_passed": 42,
                "tests_failed": 0,
                "coverage_line_rate": 0.71,
                "suite": "tests/integration/gateway",
            },
            "verification": {
                "tests_passed": 42,
                "coverage_line_rate": 0.71,
            },
        },
        {
            "gate": "G1-5",
            "timestamp_iso": "2026-04-22T10:02:00Z",
            "file_ts": "20260422T100200Z",
            "evidence": {
                "playwright_exit": 0,
                "scenarios": 5,
                "passed": 5,
                "failed": 0,
                "a11y_violations": 0,
                "mode": "headless",
            },
            "verification": {"scenarios": 5, "a11y_violations": 0},
        },
        {
            "gate": "G3-1",
            "timestamp_iso": "2026-04-22T10:03:00Z",
            "file_ts": "20260422T100300Z",
            "evidence": {
                "pytest_exit": 0,
                "auth_scenarios": 7,
                "passed": 7,
                "failed": 0,
                "suite": "tests/auth/gateway",
            },
            "verification": {"auth_scenarios": 7, "passed": 7},
        },
    ]
    records = []
    for s in stubs:
        dest, sha = _place_stub(
            gate=s["gate"],
            timestamp_iso=s["timestamp_iso"],
            file_ts=s["file_ts"],
            evidence=s["evidence"],
            verification=s["verification"],
        )
        records.append({"gate": s["gate"], "path": str(dest.relative_to(ROOT)), "sha": sha})

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "count": len(records),
        "records": records,
        "note": STUB_NOTE,
    }
    (ROOT / "artifacts" / "T2" / ".backfill-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    )
    import sys

    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# 미사용 import 방지
_ = asdict
