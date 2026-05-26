"""CSV 엔티티 카탈로그 파서."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# 프로젝트 루트 기준 CSV 경로
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CSV_PATH = _PROJECT_ROOT / "docs" / "product" / "scope" / "01-module-catalog.csv"
ALIASES_PATH = _PROJECT_ROOT / "docs" / "product" / "scope" / "entity-aliases.yaml"
SERVICES_DIR = _PROJECT_ROOT / "services"
FE_MODULES_DIR = _PROJECT_ROOT / "apps" / "web" / "lib" / "modules"


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """CSV 카탈로그의 한 행을 표현하는 데이터 클래스."""

    module: str
    feature: str
    doctype_or_entity: str
    api_endpoints: str = ""
    reports: str = ""
    workflows: str = ""
    roles: str = ""
    permissions: str = ""
    page_urls: str = ""
    notes: str = ""
    phase: str = ""
    service: str = ""
    naming_prefix: str = ""
    parent_module: str = ""
    kr_specific: bool = False
    complexity: str = ""
    dependencies: str = ""

    @property
    def is_p0(self) -> bool:
        """P0 엔티티 여부."""
        return self.phase == "P0"


def _parse_bool(value: str) -> bool:
    """Y/N 문자열을 bool로 변환한다."""
    return value.strip().upper() == "Y"


def load_catalog(csv_path: Path | None = None) -> list[CatalogEntry]:
    """CSV 파일에서 카탈로그 엔트리 목록을 로드한다."""
    path = csv_path or CSV_PATH
    entries: list[CatalogEntry] = []

    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 빈 행 건너뛰기
            if not row.get("doctype_or_entity", "").strip():
                continue
            entries.append(
                CatalogEntry(
                    module=row.get("module", "").strip(),
                    feature=row.get("feature", "").strip(),
                    doctype_or_entity=row.get("doctype_or_entity", "").strip(),
                    api_endpoints=row.get("api_endpoints", "").strip(),
                    reports=row.get("reports", "").strip(),
                    workflows=row.get("workflows", "").strip(),
                    roles=row.get("roles", "").strip(),
                    permissions=row.get("permissions", "").strip(),
                    page_urls=row.get("page_urls", "").strip(),
                    notes=row.get("notes", "").strip(),
                    phase=row.get("phase", "").strip(),
                    service=row.get("service", "").strip(),
                    naming_prefix=row.get("naming_prefix", "").strip(),
                    parent_module=row.get("parent_module", "").strip(),
                    kr_specific=_parse_bool(row.get("kr_specific", "N")),
                    complexity=row.get("complexity", "").strip(),
                    dependencies=row.get("dependencies", "").strip(),
                ),
            )

    return entries


def load_aliases(aliases_path: Path | None = None) -> dict[str, str]:
    """entity-aliases.yaml에서 엔티티명 매핑을 로드한다.

    반환: {CSV 엔티티명: 실제 모델 파일명(확장자 없음)} 딕셔너리.
    """
    path = aliases_path or ALIASES_PATH
    if not path.exists():
        return {}

    try:
        import yaml
    except ImportError:
        return {}

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        return {}

    return {str(k): str(v) for k, v in data.items()}


def get_entity_to_service_map(
    entries: Sequence[CatalogEntry],
) -> dict[str, str]:
    """엔티티명 → 서비스명 매핑을 반환한다."""
    return {e.doctype_or_entity: e.service for e in entries}
