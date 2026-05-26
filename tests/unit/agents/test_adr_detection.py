from __future__ import annotations

from scripts.agents.adr_detection import ADRTrigger, detect_triggers


def test_router_decorator_추가는_API_트리거() -> None:
    diff = """\
diff --git a/services/buying/app/routers/price.py b/services/buying/app/routers/price.py
+@router.post("/price/quote")
+def quote_price(...):
+    ...
"""
    triggers = detect_triggers(diff)
    assert ADRTrigger.API_ENDPOINT in triggers


def test_BaseModel_정의_diff는_PYDANTIC_트리거() -> None:
    diff = """\
diff --git a/services/hr/app/schemas/employee.py b/services/hr/app/schemas/employee.py
+class EmployeeCreate(BaseModel):
+    name: str
"""
    triggers = detect_triggers(diff)
    assert ADRTrigger.PYDANTIC_SCHEMA in triggers


def test_ONEERP_환경변수_추가는_ENV_트리거() -> None:
    diff = """\
diff --git a/packages/core/oneerp_core/settings.py b/packages/core/oneerp_core/settings.py
+    ONEERP_BUYING_PRICE_CACHE_TTL: int = 60
"""
    triggers = detect_triggers(diff)
    assert ADRTrigger.ENV_VAR in triggers


def test_migrations_경로_변경은_DB_MIGRATION_트리거() -> None:
    diff = """\
diff --git a/migrations/2026_04_30_add_price_table.py b/migrations/2026_04_30_add_price_table.py
new file mode 100644
"""
    triggers = detect_triggers(diff)
    assert ADRTrigger.DB_MIGRATION in triggers


def test_pyproject_의존성_추가는_DEPENDENCY_트리거() -> None:
    diff = """\
diff --git a/pyproject.toml b/pyproject.toml
@@ -10,6 +10,7 @@
 dependencies = [
     "fastapi>=0.115.0",
+    "redis>=5.0",
 ]
"""
    triggers = detect_triggers(diff)
    assert ADRTrigger.DEPENDENCY in triggers


def test_변경_없는_diff는_빈_트리거() -> None:
    diff = """\
diff --git a/README.md b/README.md
+# 제목 변경
"""
    triggers = detect_triggers(diff)
    assert triggers == set()


def test_빈_string은_빈_트리거() -> None:
    """detect_triggers("") → set() (regression safety)."""
    assert detect_triggers("") == set()


def test_주석_안_ONEERP_변수는_트리거_안_됨() -> None:
    """주석에 기존 ONEERP_ 변수 언급은 ADR 트리거 아님 (false positive 방지)."""
    diff = """\
diff --git a/services/buying/app/main.py b/services/buying/app/main.py
+    # ONEERP_BUYING_CACHE_TTL 기본값은 60초이며 운영 환경에서 조정 가능
"""
    triggers = detect_triggers(diff)
    assert ADRTrigger.ENV_VAR not in triggers
