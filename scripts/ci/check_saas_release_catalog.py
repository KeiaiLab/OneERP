#!/usr/bin/env python3
"""SaaS production 릴리즈 카탈로그 fail-stop 검증."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MUTABLE_TAGS = {"latest", "dev", "main", "master", "edge", "snapshot"}


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML 루트는 mapping이어야 합니다: {path}")
    return loaded


def is_mutable_tag(tag: str) -> bool:
    normalized = tag.strip().lower()
    if normalized in MUTABLE_TAGS:
        return True
    return normalized.endswith(("-dev", "-snapshot")) or "latest" in normalized


def _target_revisions(document: Any) -> list[str]:
    revisions: list[str] = []
    if isinstance(document, dict):
        for key, value in document.items():
            if key == "targetRevision":
                revisions.append(str(value))
            else:
                revisions.extend(_target_revisions(value))
    elif isinstance(document, list):
        for item in document:
            revisions.extend(_target_revisions(item))
    return revisions


def validate_release_catalog(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    release_path = root / "deploy" / "catalog" / "releases" / "current.yaml"
    release = _load_yaml(release_path)

    version = str(release.get("version", ""))
    if not version or is_mutable_tag(version):
        errors.append(
            f"{release_path.relative_to(root)}: production 릴리즈 버전이 불변 값이 아님: {version}"
        )

    default_tag = str(release.get("defaultImageTag", ""))
    if not default_tag or is_mutable_tag(default_tag):
        errors.append(
            f"{release_path.relative_to(root)}: defaultImageTag는 불변 값이어야 함: {default_tag}"
        )

    services = release.get("services", {})
    if not isinstance(services, dict) or not services:
        errors.append(
            f"{release_path.relative_to(root)}: services mapping이 비어 있거나 올바르지 않음"
        )
        services = {}

    for name, raw_config in services.items():
        config = raw_config if isinstance(raw_config, dict) else {}
        effective_tag = str(config.get("imageTag", default_tag))
        if not effective_tag or is_mutable_tag(effective_tag):
            errors.append(
                f"{release_path.relative_to(root)}: {name}.imageTag가 불변 값이 아님: {effective_tag}"
            )

    app_dir = root / "deploy" / "apps"
    for app_path in sorted(app_dir.glob("*.yaml")):
        loaded = yaml.safe_load(app_path.read_text(encoding="utf-8"))
        errors.extend(
            f"{app_path.relative_to(root)}: production targetRevision이 불변 값이 아님: {revision}"
            for revision in _target_revisions(loaded)
            if not revision or is_mutable_tag(revision)
        )

    return errors


def main() -> int:
    errors = validate_release_catalog()
    if errors:
        print("SaaS release catalog 검증 실패:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("SaaS release catalog 검증 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
