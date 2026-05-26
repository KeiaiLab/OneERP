"""/commercial-engine reset-v1 — v1 감사 결과를 v2 기준으로 전면 리셋.

Phase 0B 마이그레이션 — 사용자 --confirm 필수. 1회용.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _archive_v1_status(status_json: Path, archive_dir: Path) -> Path | None:
    """기존 v1 status.json 을 archived/ 로 백업."""
    if not status_json.exists():
        return None
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H%MZ")
    dest = archive_dir / f"commercial-status-v1-{ts}.json"
    shutil.copy(status_json, dest)
    return dest


def _run_v2_audit(base: Path) -> dict[str, object]:
    """v2 감사 실행 → JSON 반환."""
    result = subprocess.run(
        ["python3", "-m", "scripts.audit.commercial_readiness", "--format", "json"],
        capture_output=True,
        text=True,
        cwd=base,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"v2 감사 실행 실패:\n{result.stderr}")
    return json.loads(result.stdout)


def _update_progress_baseline(progress: Path, summary: dict[str, object]) -> None:
    """PROGRESS.md 의 v2 baseline 행을 갱신."""
    if not progress.exists():
        return
    text = progress.read_text()
    passed = summary.get("passed", 0)
    total = summary.get("total", 1081)
    percent = int(passed * 100 / max(total, 1))
    new_line = (
        f"- Baseline: {passed}/{total} ({percent}%) · 리셋 완료 {datetime.now(UTC).isoformat()}"
    )
    # 기존 placeholder 또는 이전 baseline 행 모두 대체
    text = re.sub(r"- Baseline: \(Phase 0B 완료 후 기록\)", new_line, text)
    text = re.sub(r"^- Baseline: .*$", new_line, text, count=1, flags=re.MULTILINE)
    progress.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="명시 확인 필수")
    parser.add_argument("--base-dir", default=str(Path.cwd()))
    args = parser.parse_args()

    if not args.confirm:
        print("[reset-v1] --confirm 플래그 필수. 중단.", file=sys.stderr)
        return 2

    base = Path(args.base_dir)
    status_json = base / "docs/generated/commercial-status.json"
    archive_dir = base / "docs/generated/archived"

    dest = _archive_v1_status(status_json, archive_dir)
    if dest is not None:
        print(f"[reset-v1] v1 상태 백업: {dest}")

    try:
        payload = _run_v2_audit(base)
    except RuntimeError as e:
        print(f"[reset-v1] {e}", file=sys.stderr)
        return 1

    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    summary = payload.get("summary", {})
    md = base / "docs/generated/commercial-status.md"
    md.write_text(
        f"# Commercial Readiness v2\n\n"
        f"Generated: {payload.get('generated_at')}\n\n"
        f"Baseline: {summary.get('passed', 0)}/{summary.get('total', 0)}\n"
    )

    _update_progress_baseline(base / "PROGRESS.md", summary)

    print(f"[reset-v1] 완료. baseline={summary.get('passed', 0)}/{summary.get('total', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
