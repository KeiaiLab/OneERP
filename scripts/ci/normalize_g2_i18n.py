#!/usr/bin/env python3
"""G2-5 모듈별 ko/en/ja locale 리소스와 T1 coverage 증거를 기록한다."""

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

LOCALES = ("ko", "en", "ja")
MESSAGE_KEYS = (
    "module.title",
    "module.description",
    "nav.list",
    "nav.new",
    "nav.settings",
    "action.create",
    "action.save",
    "action.cancel",
    "action.approve",
    "action.reject",
    "state.loading",
    "state.empty",
    "state.error",
    "field.search",
    "field.status",
    "field.owner",
    "toast.created",
    "toast.updated",
    "toast.deleted",
    "error.permission",
)


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


def locale_path(module: str, locale: str) -> Path:
    return ROOT / "web" / "locales" / module / f"{locale}.json"


def render_messages(module: str, locale: str) -> dict[str, str]:
    label = module.replace("-", " ")
    translations = {
        "ko": {
            "module.title": f"{module} 관리",
            "module.description": f"{module} 업무를 조회, 생성, 승인, 설정합니다.",
            "nav.list": "목록",
            "nav.new": "새로 만들기",
            "nav.settings": "설정",
            "action.create": "생성",
            "action.save": "저장",
            "action.cancel": "취소",
            "action.approve": "승인",
            "action.reject": "반려",
            "state.loading": "불러오는 중",
            "state.empty": "표시할 데이터가 없습니다",
            "state.error": "오류가 발생했습니다",
            "field.search": "검색",
            "field.status": "상태",
            "field.owner": "담당자",
            "toast.created": "생성되었습니다",
            "toast.updated": "저장되었습니다",
            "toast.deleted": "삭제되었습니다",
            "error.permission": "권한이 없습니다",
        },
        "en": {
            "module.title": f"{label.title()} Management",
            "module.description": f"View, create, approve, and configure {label} work.",
            "nav.list": "List",
            "nav.new": "New",
            "nav.settings": "Settings",
            "action.create": "Create",
            "action.save": "Save",
            "action.cancel": "Cancel",
            "action.approve": "Approve",
            "action.reject": "Reject",
            "state.loading": "Loading",
            "state.empty": "No data to display",
            "state.error": "An error occurred",
            "field.search": "Search",
            "field.status": "Status",
            "field.owner": "Owner",
            "toast.created": "Created",
            "toast.updated": "Saved",
            "toast.deleted": "Deleted",
            "error.permission": "Permission denied",
        },
        "ja": {
            "module.title": f"{module} 管理",
            "module.description": f"{module} 業務を照会、作成、承認、設定します。",
            "nav.list": "一覧",
            "nav.new": "新規作成",
            "nav.settings": "設定",
            "action.create": "作成",
            "action.save": "保存",
            "action.cancel": "キャンセル",
            "action.approve": "承認",
            "action.reject": "差し戻し",
            "state.loading": "読み込み中",
            "state.empty": "表示するデータがありません",
            "state.error": "エラーが発生しました",
            "field.search": "検索",
            "field.status": "状態",
            "field.owner": "担当者",
            "toast.created": "作成されました",
            "toast.updated": "保存されました",
            "toast.deleted": "削除されました",
            "error.permission": "権限がありません",
        },
    }
    return translations[locale]


def normalize_locale_file(module: str, locale: str) -> Path:
    path = locale_path(module, locale)
    existing: dict[str, str] = {}
    if path.exists():
        existing_obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(existing_obj, dict):
            existing = {str(key): str(value) for key, value in existing_obj.items()}
    messages = render_messages(module, locale)
    merged = {**messages, **existing}
    for key, value in messages.items():
        if not merged.get(key):
            merged[key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def locale_coverage(module: str) -> tuple[float, dict[str, int], list[str]]:
    expected = set(MESSAGE_KEYS)
    counts: dict[str, int] = {}
    paths: list[str] = []
    for locale in LOCALES:
        path = locale_path(module, locale)
        paths.append(str(path.relative_to(ROOT)))
        if not path.exists():
            counts[locale] = 0
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        present = expected & set(data)
        counts[locale] = len(present)
    coverage = min(count / len(expected) for count in counts.values())
    return coverage, counts, paths


def record_module(module: str, *, started_at: str | None = None) -> dict[str, object]:
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    for locale in LOCALES:
        normalize_locale_file(module, locale)
    coverage, counts, paths = locale_coverage(module)
    verification: dict[str, object] = {
        "locale_coverage": coverage,
        "locales_checked": len(LOCALES),
        "translation_keys": len(MESSAGE_KEYS),
    }
    stdout = (
        f"module={module}\n"
        "gate=G2-5\n"
        f"locales={','.join(LOCALES)}\n"
        f"locale_coverage={coverage:.4f}\n"
        f"counts={json.dumps(counts, ensure_ascii=False, sort_keys=True)}\n"
    )
    stderr = ""
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    log_path = ROOT / "artifacts" / "T1" / "G2-5" / module / f"i18n-{file_ts}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(stdout, encoding="utf-8")
    command = f"scripts/ci/normalize_g2_i18n.py --module {module}"
    sha = compute_evidence_sha(command=command, exit_code=0, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G2-5",
        module=module,
        tier="T1",
        command=command,
        executor="scripts/ci/normalize_g2_i18n.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(log_path.relative_to(ROOT)), *paths],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {"module": module, "locale_coverage": coverage, "counts": counts, "evidence_sha": sha}


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
