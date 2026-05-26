from __future__ import annotations

from scripts.ci.normalize_g4_monitoring import (
    MIN_ALERTS,
    MIN_PANELS,
    render_alerts,
    render_dashboard,
)


def test_render_dashboard_satisfies_g4_1_panel_shape() -> None:
    dashboard = render_dashboard("selling")

    assert dashboard["title"] == "OneERP selling Overview"
    assert len(dashboard["panels"]) >= MIN_PANELS
    assert dashboard["links"][0]["url"] == "docs/ops/runbook-selling.md"
    assert all(panel["targets"] for panel in dashboard["panels"])


def test_render_alerts_satisfies_g4_1_rule_shape() -> None:
    alerts = render_alerts("advanced-planning")
    rules = alerts["groups"][0]["rules"]

    assert len(rules) >= MIN_ALERTS
    assert {rule["labels"]["module"] for rule in rules} == {"advanced-planning"}
    assert all(
        rule["annotations"]["runbook"] == "docs/ops/runbook-advanced-planning.md" for rule in rules
    )
