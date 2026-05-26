"""WorkflowTriggerService — M3 platform/automation-orchestrator."""

from __future__ import annotations

from oneerp_core.service_base import TriggerService


class WorkflowTriggerService(TriggerService):
    REPO_KEY = "workflow_execution"
    TRIGGER_TYPE = "workflow"
