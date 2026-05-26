from pathlib import Path


def test_responsibility_matrix_has_required_layers_and_rules() -> None:
    matrix_path = Path("docs/governance/architecture/responsibility-matrix.md")
    assert matrix_path.exists(), "책임 매트릭스 문서가 없습니다."

    content = matrix_path.read_text(encoding="utf-8")

    required_layers = ["core", "services", "planes", "web", "deploy/scripts"]
    for layer in required_layers:
        assert layer in content

    required_terms = [
        "소유 책임",
        "금지 책임",
        "허용 의존 방향",
        "ADR-0014",
    ]
    for term in required_terms:
        assert term in content
