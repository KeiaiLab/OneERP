"""G4-3/4/5 드릴 증거 필드 강화 테스트 (ADR-0013 / Ultraplan Step 1.1).

배경: 기존 G4-3/G4-4/G4-5 는 런북·정책 문서 존재 크기만 체크해 47 모듈 전수
100% PASS 를 자가 신고해 왔으나, ADR-0001 §6.4 는 "스테이징 롤백 시뮬레이션
통과" 같은 실드릴 증거를 요구한다. 본 테스트는 드릴 증거 계약을 잠근다:

계약:
- `docs/ops/drills/<gate-id>/*.md` 파일이 존재하고
- 파일 frontmatter 에 `drill_date: YYYY-MM-DD` 가 있으며
- 오늘 기준 `max_age_days` 이내일 것.

상태 매핑:
- 런북·정책 누락      → FAIL (기존과 동일)
- 런북 존재 + 드릴 없음 → NOT_IMPLEMENTED (통계 왜곡 차단)
- 런북 존재 + 최근 드릴 → PASS
- 런북 존재 + 오래된 드릴 → NOT_IMPLEMENTED
"""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "audit"))

import commercial_readiness  # noqa: E402


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """임시 레포 루트로 REPO 를 치환해 게이트를 격리 테스트한다."""
    monkeypatch.setattr(commercial_readiness, "REPO", tmp_path)
    return tmp_path


def _write_runbook(repo: Path, rel: str, size: int = 600) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x" * size, encoding="utf-8")


def _write_drill(repo: Path, gate_id: str, module: str, drill_date: date) -> Path:
    """드릴 아티팩트 작성 — `docs/ops/drills/<gate_id>/<date>-<module>.md`."""
    gate_dir = repo / f"docs/ops/drills/{gate_id}"
    gate_dir.mkdir(parents=True, exist_ok=True)
    path = gate_dir / f"{drill_date.isoformat()}-{module}.md"
    body = (
        f"---\n"
        f"gate: {gate_id}\n"
        f"module: {module}\n"
        f"drill_date: {drill_date.isoformat()}\n"
        f"---\n\n"
        f"# {gate_id} 드릴 기록 — {module}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# G4-3 백업·복구
# ---------------------------------------------------------------------------


def test_G4_3_런북만_있고_드릴_없으면_NOT_IMPLEMENTED(repo: Path) -> None:
    _write_runbook(repo, "docs/ops/runbook-db-backup-restore.md")
    _write_runbook(repo, "docs/infra/ops/backup-restore.md")

    result = commercial_readiness._gate_G4_3_backup("selling")

    assert result.status == commercial_readiness.Status.NOT_IMPLEMENTED
    assert "drill" in result.evidence.lower()


def test_G4_3_90일_이내_드릴_있으면_PASS(repo: Path) -> None:
    _write_runbook(repo, "docs/ops/runbook-db-backup-restore.md")
    _write_runbook(repo, "docs/infra/ops/backup-restore.md")
    _write_drill(repo, "G4-3", "selling", datetime.now(tz=UTC).date() - timedelta(days=10))

    result = commercial_readiness._gate_G4_3_backup("selling")

    assert result.status == commercial_readiness.Status.PASS


def test_G4_3_오래된_드릴은_NOT_IMPLEMENTED(repo: Path) -> None:
    _write_runbook(repo, "docs/ops/runbook-db-backup-restore.md")
    _write_runbook(repo, "docs/infra/ops/backup-restore.md")
    _write_drill(repo, "G4-3", "selling", datetime.now(tz=UTC).date() - timedelta(days=120))

    result = commercial_readiness._gate_G4_3_backup("selling")

    assert result.status == commercial_readiness.Status.NOT_IMPLEMENTED


def test_G4_3_런북_누락은_FAIL(repo: Path) -> None:
    _write_drill(repo, "G4-3", "selling", datetime.now(tz=UTC).date())

    result = commercial_readiness._gate_G4_3_backup("selling")

    assert result.status == commercial_readiness.Status.FAIL


def test_G4_3_드릴은_해당_모듈을_대상으로_해야한다(repo: Path) -> None:
    _write_runbook(repo, "docs/ops/runbook-db-backup-restore.md")
    _write_runbook(repo, "docs/infra/ops/backup-restore.md")
    _write_drill(repo, "G4-3", "selling", datetime.now(tz=UTC).date())

    buying_result = commercial_readiness._gate_G4_3_backup("buying")

    assert buying_result.status == commercial_readiness.Status.NOT_IMPLEMENTED


# ---------------------------------------------------------------------------
# G4-4 롤백
# ---------------------------------------------------------------------------


def test_G4_4_런북만_있고_드릴_없으면_NOT_IMPLEMENTED(repo: Path) -> None:
    _write_runbook(repo, "docs/infra/ops/rollback.md")

    result = commercial_readiness._gate_G4_4_rollback("accounting")

    assert result.status == commercial_readiness.Status.NOT_IMPLEMENTED


def test_G4_4_최근_드릴_있으면_PASS(repo: Path) -> None:
    _write_runbook(repo, "docs/infra/ops/rollback.md")
    _write_drill(repo, "G4-4", "accounting", datetime.now(tz=UTC).date() - timedelta(days=30))

    result = commercial_readiness._gate_G4_4_rollback("accounting")

    assert result.status == commercial_readiness.Status.PASS


# ---------------------------------------------------------------------------
# G4-5 on-call
# ---------------------------------------------------------------------------


def test_G4_5_런북만_있고_드릴_없으면_NOT_IMPLEMENTED(repo: Path) -> None:
    _write_runbook(repo, "docs/ops/runbook-incident-response.md")

    result = commercial_readiness._gate_G4_5_oncall("stock")

    assert result.status == commercial_readiness.Status.NOT_IMPLEMENTED


def test_G4_5_최근_드릴_있으면_PASS(repo: Path) -> None:
    _write_runbook(repo, "docs/ops/runbook-incident-response.md")
    _write_drill(repo, "G4-5", "stock", datetime.now(tz=UTC).date())

    result = commercial_readiness._gate_G4_5_oncall("stock")

    assert result.status == commercial_readiness.Status.PASS


# ---------------------------------------------------------------------------
# 규약 외부 노출 — 헬퍼가 공개 상수를 가진다
# ---------------------------------------------------------------------------


def test_드릴_디렉토리_규약이_모듈_상수로_노출된다() -> None:
    assert hasattr(commercial_readiness, "DRILL_ROOT")
    assert hasattr(commercial_readiness, "DRILL_MAX_AGE_DAYS")
    assert commercial_readiness.DRILL_MAX_AGE_DAYS == 90
