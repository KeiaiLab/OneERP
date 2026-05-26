from __future__ import annotations

from pathlib import Path

from scripts.audit.gates.g1_docs import gate_G1_1_adr
from scripts.audit.gates.g1_tests import module_openapi_path
from scripts.engine.validators import GateStatus


def test_g1_2_openapi_uses_docs_api_canonical_spec_for_sales_scm_modules() -> None:
    for module in ("selling", "buying", "stock"):
        assert module_openapi_path(module) == Path("docs") / "api" / module / "openapi.yaml"


def test_g1_2_openapi_prefers_docs_api_even_when_service_spec_exists() -> None:
    assert module_openapi_path("gateway") == Path("docs/api/gateway/openapi.yaml")


def test_g1_2_openapi_uses_docs_api_alias_for_merged_modules() -> None:
    assert module_openapi_path("ecommerce") == Path("docs/api/commerce/openapi.yaml")
    assert module_openapi_path("quality") == Path("docs/api/qm/openapi.yaml")
    assert module_openapi_path("workreport") == Path("docs/api/learning/openapi.yaml")


def test_g1_1_adr_accepts_module_boundary_catalog(tmp_path: Path, monkeypatch) -> None:
    catalog = tmp_path / "docs" / "kb" / "adr" / "0021-module-boundary-catalog.md"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        "\n".join(
            [
                "---",
                "status: Accepted",
                "date: 2026-05-07",
                "decision: 모듈 경계 카탈로그를 G1-1 정본 ADR로 둔다.",
                "consequences: 모듈별 경계 변경은 이 ADR 또는 개별 bounds ADR로 갱신한다.",
                "---",
                "",
                "# ADR-0021: 모듈 경계 카탈로그",
                "",
                "## selling — 판매 경계",
                "",
                *[f"근거 라인 {i}" for i in range(100)],
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    result = gate_G1_1_adr("G1-1", "selling")

    assert result.status == GateStatus.PASS


def test_g1_1_adr_does_not_match_module_name_inside_unrelated_word(
    tmp_path: Path,
    monkeypatch,
) -> None:
    adr = tmp_path / "docs" / "governance" / "adr" / "0011-runtime-cluster-decomposition.md"
    adr.parent.mkdir(parents=True)
    adr.write_text("# unrelated\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = gate_G1_1_adr("G1-1", "pos")

    assert result.status == GateStatus.NOT_IMPLEMENTED
