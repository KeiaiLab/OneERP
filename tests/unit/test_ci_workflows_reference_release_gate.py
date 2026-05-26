from pathlib import Path

CORE_WORKFLOW = Path("core/.gitea/workflows/ci.yml")
WEB_WORKFLOW = Path("web/.gitea/workflows/ci.yml")


def test_ci_workflows_align_with_release_gate() -> None:
    core_text = CORE_WORKFLOW.read_text(encoding="utf-8")
    web_text = WEB_WORKFLOW.read_text(encoding="utf-8")

    assert "run_release_gate.sh" in core_text
    assert "tests/e2e/smoke.spec.ts" in web_text
