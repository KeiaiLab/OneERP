from __future__ import annotations

from pathlib import Path

from scripts.ci.check_saas_release_catalog import is_mutable_tag, validate_release_catalog


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_mutable_tag_detector_blocks_dev_latest_and_main() -> None:
    for tag in ("latest", "0.1.0-dev", "main", "build-latest"):
        assert is_mutable_tag(tag)

    assert not is_mutable_tag("1.2.3-20260507-a1b2c3d")


def test_release_catalog_checker_rejects_mutable_release_inputs(tmp_path: Path) -> None:
    _write(
        tmp_path / "deploy/catalog/releases/current.yaml",
        """
apiVersion: oneerp/v1alpha1
version: 0.1.0-dev
defaultImageTag: latest
services:
  gateway: {}
""",
    )
    _write(
        tmp_path / "deploy/apps/applicationset.yaml",
        """
spec:
  template:
    spec:
      source:
        targetRevision: main
""",
    )

    errors = validate_release_catalog(tmp_path)

    assert any("릴리즈 버전이 불변 값이 아님" in error for error in errors)
    assert any("defaultImageTag는 불변 값이어야 함" in error for error in errors)
    assert any("gateway.imageTag가 불변 값이 아님" in error for error in errors)
    assert any("production targetRevision이 불변 값이 아님" in error for error in errors)


def test_release_catalog_checker_accepts_immutable_release_inputs(tmp_path: Path) -> None:
    _write(
        tmp_path / "deploy/catalog/releases/current.yaml",
        """
apiVersion: oneerp/v1alpha1
version: 1.2.3
defaultImageTag: 1.2.3-20260507-a1b2c3d
services:
  gateway: {}
  web:
    imageTag: 1.2.3-web-a1b2c3d
""",
    )
    _write(
        tmp_path / "deploy/apps/applicationset.yaml",
        """
spec:
  template:
    spec:
      source:
        targetRevision: release/1.2.3
""",
    )

    assert validate_release_catalog(tmp_path) == []
