from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

required = [
    ROOT / "docs/infra/ops/backup-restore.md",
    ROOT / "docs/ops/runbook-db-backup-restore.md",
    ROOT / "docs/generated/commercial-status.md",
]

missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
if missing:
    print("missing required rehearsal evidence files:")
    for item in missing:
        print(f"- {item}")
    raise SystemExit(1)

print("release rehearsal evidence presence check ok")
