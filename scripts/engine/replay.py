"""/commercial-engine replay <sha> — 특정 증거를 재실행해 해시 일치 검증."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from scripts.engine.evidence import load_meta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--base-dir", default=str(Path.cwd()))
    args = parser.parse_args()

    base = Path(args.base_dir)
    meta = load_meta(args.sha, base_dir=base)

    print(f"[replay] replaying: {meta.command}")
    result = subprocess.run(  # noqa: S602
        meta.command, shell=True, capture_output=True, text=True, check=False
    )
    new_stdout_sha = hashlib.sha256(result.stdout.encode()).hexdigest()
    new_stderr_sha = hashlib.sha256(result.stderr.encode()).hexdigest()

    ok = (
        result.returncode == meta.exit_code
        and new_stdout_sha == meta.stdout_sha256
        and new_stderr_sha == meta.stderr_sha256
    )

    if ok:
        print("[replay] OK — hashes match")
        return 0
    print("[replay] MISMATCH")
    print(f"  exit_code: expected={meta.exit_code} actual={result.returncode}")
    print(f"  stdout_sha: expected={meta.stdout_sha256[:16]} actual={new_stdout_sha[:16]}")
    print(f"  stderr_sha: expected={meta.stderr_sha256[:16]} actual={new_stderr_sha[:16]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
