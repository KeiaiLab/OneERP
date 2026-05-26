"""git diff 텍스트 → ADR 트리거 패턴 검출.

5 패턴: API_ENDPOINT / PYDANTIC_SCHEMA / ENV_VAR / DB_MIGRATION / DEPENDENCY.
T7 oe-feature-pipeliner의 Stage 1 종료 후 호출되어 documentation-sync-agent
sub-Task 위임 여부를 결정한다.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Final


class ADRTrigger(StrEnum):
    API_ENDPOINT = "api_endpoint"
    PYDANTIC_SCHEMA = "pydantic_schema"
    ENV_VAR = "env_var"
    DB_MIGRATION = "db_migration"
    DEPENDENCY = "dependency"


# 추가/제거 라인 모두 ADR 트리거 (`+`/`-`로 시작, `+++`/`---` 헤더는 제외)
_ADDED_OR_REMOVED_LINE: Final[re.Pattern[str]] = re.compile(r"^[+\-](?![+\-]).*$", re.MULTILINE)

# 가정: `class X(BaseModel):` 단일 라인. 멀티라인 class 선언은 OneERP에서 드물어 미지원.
_PATTERNS: Final[dict[ADRTrigger, re.Pattern[str]]] = {
    ADRTrigger.API_ENDPOINT: re.compile(r"@router\.(get|post|put|delete|patch)\b"),
    ADRTrigger.PYDANTIC_SCHEMA: re.compile(r"\bclass\s+\w+\s*\(\s*BaseModel\s*\)"),
    ADRTrigger.ENV_VAR: re.compile(r"\bONEERP_[A-Z0-9_]+(?=\s*[:=])"),
}

# 가정: git diff 헤더가 non-quoted path. quoted path("a/...")는 OneERP 환경에서 드물어 미지원.
_FILE_PATH_HEADER: Final[re.Pattern[str]] = re.compile(r"^diff --git a/(\S+) b/\S+", re.MULTILINE)

_DEPENDENCY_FILES: Final[frozenset[str]] = frozenset(
    {
        "pyproject.toml",
        "uv.lock",
        "package.json",
        "pnpm-lock.yaml",
    }
)


def detect_triggers(diff_text: str) -> set[ADRTrigger]:
    """git diff 텍스트에서 트리거 집합을 반환한다."""
    triggers: set[ADRTrigger] = set()

    # 라인 패턴 (API/Pydantic/ENV) — 추가/제거 라인만 검사
    for match in _ADDED_OR_REMOVED_LINE.finditer(diff_text):
        line = match.group(0)
        for trig, pat in _PATTERNS.items():
            if pat.search(line):
                triggers.add(trig)

    # 파일 경로 패턴 (DB_MIGRATION / DEPENDENCY)
    for path_match in _FILE_PATH_HEADER.finditer(diff_text):
        path = path_match.group(1)
        if path.startswith("migrations/") or "/alembic/versions/" in path:
            triggers.add(ADRTrigger.DB_MIGRATION)
        if path in _DEPENDENCY_FILES:
            triggers.add(ADRTrigger.DEPENDENCY)

    return triggers
