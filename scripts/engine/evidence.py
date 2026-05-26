"""증거 메타데이터 관리 — sha 계산 · 저장 · 인덱스 append · 최신 검색."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class EvidenceMeta:
    """한 증거의 메타데이터 레코드."""

    sha256: str
    gate: str
    module: str
    tier: str
    command: str
    executor: str
    git_sha: str
    host: str
    user: str
    started_at: str  # ISO8601 UTC
    duration_seconds: int
    exit_code: int
    stdout_sha256: str
    stderr_sha256: str
    artifact_paths: list[str] = field(default_factory=list)
    verification: dict[str, object] = field(default_factory=dict)
    parent_evidence: str | None = None

    @property
    def replay_command(self) -> str:
        """재실행 명령."""
        return f"scripts/engine/replay.py --sha {self.sha256}"


def compute_evidence_sha(*, command: str, exit_code: int, stdout: str, stderr: str) -> str:
    """(명령 + exit + stdout + stderr) 를 sha256 으로 결합."""
    h = hashlib.sha256()
    h.update(command.encode())
    h.update(b"\x00")
    h.update(str(exit_code).encode())
    h.update(b"\x00")
    h.update(stdout.encode())
    h.update(b"\x00")
    h.update(stderr.encode())
    return h.hexdigest()


def _meta_path(sha256: str, base_dir: Path) -> Path:
    return base_dir / "artifacts" / "_meta" / f"{sha256}.json"


def _index_path(base_dir: Path) -> Path:
    return base_dir / "artifacts" / "_meta" / "index.jsonl"


def write_meta(meta: EvidenceMeta, *, base_dir: Path) -> None:
    """개별 증거 메타 JSON 저장."""
    path = _meta_path(meta.sha256, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(meta)
    payload["replay_command"] = meta.replay_command
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def load_meta(sha256: str, *, base_dir: Path) -> EvidenceMeta:
    """개별 증거 메타 JSON 로드."""
    path = _meta_path(sha256, base_dir)
    payload = json.loads(path.read_text())
    payload.pop("replay_command", None)
    return EvidenceMeta(**payload)


def append_index(meta: EvidenceMeta, *, base_dir: Path) -> None:
    """index.jsonl 에 한 줄 append."""
    path = _index_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "sha256": meta.sha256,
        "gate": meta.gate,
        "module": meta.module,
        "tier": meta.tier,
        "started_at": meta.started_at,
        "exit_code": meta.exit_code,
    }
    with path.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def latest_evidence_for(
    gate: str, module: str, tier: str, *, base_dir: Path
) -> EvidenceMeta | None:
    """해당 gate·module·tier 의 가장 최근 증거 반환."""
    path = _index_path(base_dir)
    if not path.exists():
        return None
    candidates: list[dict] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry["gate"] == gate and entry["module"] == module and entry["tier"] == tier:
            candidates.append(entry)
    if not candidates:
        return None
    latest = max(candidates, key=lambda e: e["started_at"])
    return load_meta(latest["sha256"], base_dir=base_dir)
