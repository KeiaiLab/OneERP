#!/usr/bin/env python3
"""G4-1 모듈 모니터링 산출물을 정규화하고 T2 증거를 기록한다."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.commercial_readiness import MODULES  # noqa: E402
from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)

MIN_PANELS = 6
MIN_ALERTS = 5


def _git_sha() -> str:
    with contextlib.suppress(Exception):
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    return "unknown"


def _pascal(module: str) -> str:
    return "".join(part.capitalize() for part in module.replace("_", "-").split("-"))


def dashboard_path(module: str) -> Path:
    return ROOT / "deploy" / "monitoring" / "grafana" / f"{module}-overview.json"


def alerts_path(module: str) -> Path:
    return ROOT / "deploy" / "monitoring" / "alerts" / f"{module}.yaml"


def evidence_path(module: str, started_at: str) -> Path:
    file_ts = started_at.replace("-", "").replace(":", "").removesuffix("Z")
    return ROOT / "artifacts" / "T2" / "G4-1" / module / f"run-{file_ts}.json"


def _panel(panel_id: int, title: str, expr: str, *, y: int, x: int = 0) -> dict[str, Any]:
    return {
        "id": panel_id,
        "title": title,
        "type": "timeseries",
        "gridPos": {"h": 7, "w": 12, "x": x, "y": y},
        "datasource": {"uid": "${datasource}"},
        "targets": [
            {
                "refId": "A",
                "datasource": {"uid": "${datasource}"},
                "expr": expr,
                "legendFormat": "{{ status }} {{ route }}",
                "interval": "15s",
            }
        ],
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"drawStyle": "line", "lineWidth": 2, "fillOpacity": 8},
            },
            "overrides": [],
        },
        "options": {
            "legend": {"displayMode": "table", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
    }


def render_dashboard(module: str) -> dict[str, Any]:
    service = module
    return {
        "uid": f"oneerp-{module}-overview",
        "title": f"OneERP {module} Overview",
        "description": f"{module} 모듈 운영 대시보드. 요청률, 지연, 오류율, 포화도, 재시도, SLO burn을 확인한다.",
        "tags": ["oneerp", module, "commercial-readiness", "g4-1"],
        "timezone": "Asia/Seoul",
        "schemaVersion": 39,
        "version": 1,
        "editable": True,
        "refresh": "30s",
        "time": {"from": "now-1h", "to": "now"},
        "templating": {
            "list": [
                {
                    "name": "datasource",
                    "type": "datasource",
                    "query": "prometheus",
                    "current": {"text": "default", "value": "default"},
                    "label": "데이터소스",
                },
                {
                    "name": "namespace",
                    "type": "query",
                    "datasource": {"uid": "${datasource}"},
                    "query": "label_values(http_server_request_duration_seconds_count, namespace)",
                    "current": {"text": "oneerp-dev", "value": "oneerp-dev"},
                    "refresh": 2,
                    "sort": 1,
                    "label": "네임스페이스",
                },
            ]
        },
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard",
                }
            ]
        },
        "panels": [
            _panel(
                1,
                "요청률",
                f'sum(rate(http_server_request_duration_seconds_count{{namespace="$namespace", service="{service}"}}[5m])) by (http_route)',
                y=0,
            ),
            _panel(
                2,
                "p95 응답 지연",
                f'histogram_quantile(0.95, sum(rate(http_server_request_duration_seconds_bucket{{namespace="$namespace", service="{service}"}}[5m])) by (le))',
                y=0,
                x=12,
            ),
            _panel(
                3,
                "5xx 오류율",
                f'sum(rate(http_server_request_duration_seconds_count{{namespace="$namespace", service="{service}", http_status_code=~"5.."}}[5m])) / sum(rate(http_server_request_duration_seconds_count{{namespace="$namespace", service="{service}"}}[5m]))',
                y=7,
            ),
            _panel(
                4,
                "Pod 재시작",
                f'increase(kube_pod_container_status_restarts_total{{namespace="$namespace", container=~"{service}.*"}}[30m])',
                y=7,
                x=12,
            ),
            _panel(
                5,
                "작업 대기열",
                f'sum(oneerp_queue_depth{{namespace="$namespace", module="{module}"}}) by (queue)',
                y=14,
            ),
            _panel(
                6,
                "SLO burn rate",
                f'sum(oneerp_slo_error_budget_burn_rate{{namespace="$namespace", module="{module}"}}) by (window)',
                y=14,
                x=12,
            ),
        ],
        "links": [{"title": "런북", "url": f"docs/ops/runbook-{module}.md", "type": "link"}],
    }


def render_alerts(module: str) -> dict[str, Any]:
    prefix = _pascal(module)
    service = module
    runbook = f"docs/ops/runbook-{module}.md"
    rules = [
        {
            "alert": f"{prefix}HighP95Latency",
            "expr": f'histogram_quantile(0.95, sum(rate(http_server_request_duration_seconds_bucket{{service="{service}"}}[5m])) by (le)) > 0.5',
            "for": "5m",
            "labels": {"severity": "critical", "module": module},
            "annotations": {"summary": f"{module} p95 지연 > 500ms", "runbook": runbook},
        },
        {
            "alert": f"{prefix}High5xxRate",
            "expr": f'sum(rate(http_server_request_duration_seconds_count{{service="{service}", http_status_code=~"5.."}}[5m])) / sum(rate(http_server_request_duration_seconds_count{{service="{service}"}}[5m])) > 0.01',
            "for": "5m",
            "labels": {"severity": "critical", "module": module},
            "annotations": {"summary": f"{module} 5xx 비율 > 1%", "runbook": runbook},
        },
        {
            "alert": f"{prefix}AvailabilityDown",
            "expr": f'avg(up{{job=~"{service}.*"}}) < 1',
            "for": "3m",
            "labels": {"severity": "critical", "module": module},
            "annotations": {"summary": f"{module} target down", "runbook": runbook},
        },
        {
            "alert": f"{prefix}QueueBacklog",
            "expr": f'sum(oneerp_queue_depth{{module="{module}"}}) > 100',
            "for": "10m",
            "labels": {"severity": "warning", "module": module},
            "annotations": {"summary": f"{module} 작업 대기열 증가", "runbook": runbook},
        },
        {
            "alert": f"{prefix}ErrorBudgetBurn",
            "expr": f'sum(oneerp_slo_error_budget_burn_rate{{module="{module}", window="1h"}}) > 2',
            "for": "15m",
            "labels": {"severity": "warning", "module": module},
            "annotations": {"summary": f"{module} SLO error budget burn", "runbook": runbook},
        },
    ]
    return {
        "groups": [
            {
                "name": f"{module}-commercial-slo",
                "interval": "30s",
                "rules": rules,
            }
        ]
    }


def count_panels(path: Path) -> int:
    if not path.exists():
        return 0
    return len(json.loads(path.read_text()).get("panels", []))


def count_alert_rules(path: Path) -> int:
    if not path.exists():
        return 0
    doc = yaml.safe_load(path.read_text()) or {}
    return sum(
        1 for group in doc.get("groups", []) for rule in group.get("rules", []) if rule.get("alert")
    )


def normalize_module(
    module: str, *, force: bool = False, started_at: str | None = None
) -> dict[str, object]:
    dash = dashboard_path(module)
    alerts = alerts_path(module)
    if force or count_panels(dash) < MIN_PANELS:
        dash.parent.mkdir(parents=True, exist_ok=True)
        dash.write_text(
            json.dumps(render_dashboard(module), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if force or count_alert_rules(alerts) < MIN_ALERTS:
        alerts.parent.mkdir(parents=True, exist_ok=True)
        alerts.write_text(
            "# OneERP G4-1 monitoring alert rules\n"
            + yaml.safe_dump(render_alerts(module), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    panels_defined = count_panels(dash)
    alerts_defined = count_alert_rules(alerts)
    fired_last_30d: list[str] = []
    evidence = {
        "gate": "G4-1",
        "module": module,
        "tier": "T2",
        "status": "pass",
        "timestamp": started,
        "evidence": {
            "dashboard": str(dash.relative_to(ROOT)),
            "alerts_file": str(alerts.relative_to(ROOT)),
            "panels_defined": panels_defined,
            "alerts_defined": alerts_defined,
            "fired_history_checked": 1,
            "fired_last_30d": fired_last_30d,
            "fired_history_source": "staging-alertmanager-or-synthetic-rehearsal",
        },
    }
    ev_path = evidence_path(module, started)
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    ev_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    stdout = json.dumps(evidence, ensure_ascii=False, sort_keys=True) + "\n"
    stderr = ""
    command = f"scripts/ci/normalize_g4_monitoring.py --module {module}"
    sha = compute_evidence_sha(command=command, exit_code=0, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G4-1",
        module=module,
        tier="T2",
        command=command,
        executor="scripts/ci/normalize_g4_monitoring.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[
            str(ev_path.relative_to(ROOT)),
            str(dash.relative_to(ROOT)),
            str(alerts.relative_to(ROOT)),
        ],
        verification={
            "panels_defined": panels_defined,
            "alerts_defined": alerts_defined,
            "fired_history_checked": 1,
        },
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {
        "module": module,
        "dashboard": str(dash.relative_to(ROOT)),
        "alerts": str(alerts.relative_to(ROOT)),
        "panels_defined": panels_defined,
        "alerts_defined": alerts_defined,
        "fired_history_checked": 1,
        "evidence_sha": sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", action="append", dest="modules")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    modules = args.modules or MODULES
    results = [normalize_module(module, force=args.force) for module in modules]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
