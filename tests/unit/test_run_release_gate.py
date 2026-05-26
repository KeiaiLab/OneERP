from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "ci" / "run_release_gate.sh"


def test_run_release_gate_script_exists_and_has_stage_labels() -> None:
    assert SCRIPT_PATH.exists(), f"release gate 스크립트가 없습니다: {SCRIPT_PATH}"

    content = SCRIPT_PATH.read_text(encoding="utf-8")

    for label in ("정적", "조립", "데이터", "사용자 시나리오"):
        assert label in content

    for script_name in (
        "./scripts/ci/run.sh",
        "./scripts/dev/stack-smoke.sh",
        "./scripts/dev/seed-data.sh",
        "./scripts/ci/run_e2e.sh",
    ):
        assert script_name in content

    assert "web/tests/e2e/smoke.spec.ts" in content


def test_run_release_gate_keeps_stack_alive_for_seed_data() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    smoke_call = "NATS_URL=nats://nats:4222 NOCLEAN=1 ./scripts/dev/stack-smoke.sh"
    assert smoke_call in content
    assert content.index(smoke_call) < content.index("./scripts/dev/seed-data.sh")


def test_run_release_gate_allocates_host_ports_before_compose_smoke() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    for snippet in (
        "pick_port",
        "ONEERP_FERRETDB_HOST_PORT",
        "ONEERP_NATS_HOST_PORT",
        "ONEERP_NATS_MONITOR_HOST_PORT",
        "ONEERP_VALKEY_HOST_PORT",
        "connect_ex",
        'sock.bind(("0.0.0.0", port))',
        "mongodb://localhost:${ONEERP_FERRETDB_HOST_PORT}",
        "nats://localhost:${ONEERP_NATS_HOST_PORT}",
        "redis://localhost:${ONEERP_VALKEY_HOST_PORT}",
        "NATS_URL=nats://nats:4222 NOCLEAN=1 ./scripts/dev/stack-smoke.sh",
    ):
        assert snippet in content


def test_run_e2e_respects_release_gate_connection_env() -> None:
    content = (ROOT / "scripts" / "ci" / "run_e2e.sh").read_text(encoding="utf-8")

    assert (
        'export ONEERP_FERRETDB_URI="${ONEERP_FERRETDB_URI:-mongodb://localhost:27017}"' in content
    )
    assert 'export FERRETDB_URI="${FERRETDB_URI:-${ONEERP_FERRETDB_URI}}"' in content
    assert "uv run --no-project --with pymongo python3 -c" in content
    assert "MongoClient(os.environ['FERRETDB_URI']" in content


def test_run_e2e_resets_ephemeral_test_database() -> None:
    content = (ROOT / "scripts" / "ci" / "run_e2e.sh").read_text(encoding="utf-8")

    assert 'export ONEERP_DATABASE_NAME="${ONEERP_DATABASE_NAME:-oneerp_e2e_test}"' in content
    assert "drop_database(os.environ['ONEERP_DATABASE_NAME'])" in content
    assert "=== E2E 테스트 DB 초기화 ===" in content
    assert "=== E2E 테스트 DB 삭제 ===" in content
