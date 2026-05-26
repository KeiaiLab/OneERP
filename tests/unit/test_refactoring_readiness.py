from pathlib import Path

DESIGN_DOC = Path("docs/plans/2026-04-13-architecture-first-refactoring-design.md")
MATRIX_DOC = Path("docs/governance/architecture/responsibility-matrix.md")


def _read(path: Path) -> str:
    assert path.exists(), f"문서가 없습니다: {path}"
    return path.read_text(encoding="utf-8")


def _assert_readiness(text: str, *, path: Path) -> None:
    assert "## 착수 조건" in text, f"{path}에 착수 조건 섹션이 없습니다"
    assert "다음 배치(planes 정리)" in text, f"{path}에 다음 배치 설명이 없습니다"

    required_items = [
        "scope SoT 공백 해소",
        "구조 검사 baseline 확보",
        "release gate 성공",
    ]
    for item in required_items:
        assert item in text, f"{path}에 {item}이 없습니다"


def test_refactoring_readiness_is_documented_in_both_sources() -> None:
    _assert_readiness(_read(DESIGN_DOC), path=DESIGN_DOC)
    _assert_readiness(_read(MATRIX_DOC), path=MATRIX_DOC)
