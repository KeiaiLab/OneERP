from __future__ import annotations

import configparser
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_gitmodules_allows_only_core_and_web_submodules() -> None:
    parser = configparser.ConfigParser()
    loaded = parser.read(ROOT / ".gitmodules", encoding="utf-8")

    assert loaded == [str(ROOT / ".gitmodules")]

    paths = {
        parser[section]["path"] for section in parser.sections() if section.startswith("submodule ")
    }
    assert paths == {"core", "web"}


def test_services_is_root_owned_source_tree_not_gitlink() -> None:
    git = shutil.which("git")
    assert git is not None

    result = subprocess.run(  # noqa: S603
        [git, "ls-files", "-s", "--", "services"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    modes = {line.split()[0] for line in lines}

    assert lines
    assert "160000" not in modes
    assert modes <= {"100644", "100755", "120000"}


def test_services_has_no_nested_git_metadata() -> None:
    assert not (ROOT / "services" / ".git").exists()
    assert not (ROOT / ".git" / "modules" / "services").exists()


def test_local_generated_artifacts_are_ignored() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")

    for pattern in (
        "/.graphify_*",
        "/graphify-out/",
        "/output/",
        "/*-artif.txt",
    ):
        assert pattern in text


def test_new_evidence_artifacts_do_not_create_git_status_noise() -> None:
    git = shutil.which("git")
    assert git is not None

    for path in (
        "artifacts/T1/G1-2/accounting/openapi-contract-20990101T000000.log",
        "artifacts/T2/G2-1/gateway/slo-20990101T000000.log",
        "artifacts/T3/G4-4/gateway/staging-20990101T000000.log",
        "artifacts/_meta/20990101-local-evidence.json",
        "artifacts/k6/gateway-20990101T000000.csv",
        "artifacts/slo/gateway-20990101-30d.json",
    ):
        result = subprocess.run(  # noqa: S603
            [git, "check-ignore", "--quiet", "--", path],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 0, path


def test_legacy_document_entrypoints_link_to_canonical_indexes() -> None:
    tutorial = (ROOT / "docs" / "tutorial" / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "docs" / "manual" / "README.md").read_text(encoding="utf-8")
    ops = (ROOT / "docs" / "ops" / "README.md").read_text(encoding="utf-8")
    infra_ops = (ROOT / "docs" / "infra" / "ops" / "README.md").read_text(encoding="utf-8")

    assert "../tutorials/INDEX.md" in tutorial
    assert "../user-manual/INDEX.md" in manual
    assert "모듈별 runbook" in ops
    assert "운영 정책 정본" in infra_ops
