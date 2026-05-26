from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = ROOT / "docs" / "product" / "scope" / "IMPLEMENTATION-MASTER-PROMPT.md"


def test_master_prompt_has_required_sections() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")

    required_sections = [
        "## 프롬프트 역할",
        "## 입력 컨텍스트 우선순위",
        "## 전역 실행 원칙",
        "## 작업 선택 알고리즘",
        "## 모듈 실행 루프",
        "## 사용자 시나리오 명세 형식",
        "## 테스트 전략",
        "## 테스트 데이터 라이프사이클",
        "## 검증 명령어",
        "## 완료 보고 형식",
        "## 금지 사항",
        "## 참조 문서",
    ]

    for section in required_sections:
        assert section in text, f"필수 섹션 누락: {section}"


def test_master_prompt_references_source_of_truth_and_validation() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")

    required_snippets = [
        "docs/product/scope/00-source-of-truth.md",
        "docs/product/scope/MODULE-SERVICE-MAP.md",
        "docs/product/IMPLEMENTATION-GAP-REPORT.md",
        "docs/product/PROJECT-INTEGRITY-REPORT.md",
        "docs/product/scope/08-amaranth10-gap-analysis.md",
        "./scripts/ci/run.sh",
        "Playwright",
        "Appium",
        "한국어",
    ]

    for snippet in required_snippets:
        assert snippet in text, f"필수 참조 또는 규칙 누락: {snippet}"


def test_master_prompt_avoids_false_completion_claims() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")

    forbidden_snippets = [
        "전체 구현 완료",
        "56/56 모듈 구현 완료",
        "작업이 **완료**되었다",
    ]

    for snippet in forbidden_snippets:
        assert snippet not in text, f"오해를 부르는 완료 선언 제거 필요: {snippet}"
