from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "scripts" / "ci" / "release_verification_matrix.yaml"


def test_release_verification_matrix_declares_backend_and_web_flows() -> None:
    assert MATRIX_PATH.exists(), (
        f"release verification matrix가 없습니다: {MATRIX_PATH.relative_to(ROOT)}"
    )

    text = MATRIX_PATH.read_text(encoding="utf-8")
    assert "backend_e2e" in text
    assert "web_e2e" in text
