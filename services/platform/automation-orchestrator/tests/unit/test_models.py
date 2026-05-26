from oneerp_automation_orchestrator_app.models.automation_definition import (
    AutomationDefinitionCreate,
)


def test_automation_definition_defaults() -> None:
    model = AutomationDefinitionCreate(name="월마감")

    assert model.category == "general"
    assert model.is_active is False
