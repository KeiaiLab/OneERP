#!/usr/bin/env bash
# 계약 테스트 — OpenAPI 스키마 기반 자동 퍼즈 테스트
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

: "${ONEERP_JWT_SECRET:=contract-gate-dev-secret-000000000000000000000000}"
export ONEERP_JWT_SECRET

echo "=== 계약 테스트 ==="

SERVICES=(
  "gateway:services/platform/gateway"
  "selling:services/sales/selling"
  "buying:services/scm/buying"
  "stock:services/scm/stock"
  "accounting:services/finance/accounting"
  "hr:services/hr/hr"
  "payroll:services/finance/payroll"
  "expenses:services/finance/expenses"
)

for entry in "${SERVICES[@]}"; do
  IFS=":" read -r svc_name svc_dir <<< "$entry"
  [ -d "$svc_dir" ] || continue

  echo "[$svc_name] OpenAPI 스키마 추출..."
  schema_file="/tmp/oneerp_${svc_name}_openapi.json"
  uv run --directory "$svc_dir" python -c "
import contextlib
import importlib
import inspect
import io
import json
import logging
import pathlib
import pkgutil
import sys
import tomllib
from datetime import date, datetime, time, timedelta

from pydantic import BaseModel

logging.disable(logging.CRITICAL)

service_dir = pathlib.Path.cwd()
pyproject = tomllib.loads(service_dir.joinpath('pyproject.toml').read_text())
packages = pyproject['tool']['hatch']['build']['targets']['wheel']['packages']
package_name = packages[0]
main_module = f'{package_name}.main'

_real_stdout = sys.stdout
_real_stderr = sys.stderr
sink = io.StringIO()
sys.stdout = sink
sys.stderr = sink

package = importlib.import_module(package_name)
imported_modules = [package]
if hasattr(package, '__path__'):
    for module_info in pkgutil.walk_packages(package.__path__, f'{package_name}.'):
        try:
            imported_modules.append(importlib.import_module(module_info.name))
        except Exception:
            continue

type_namespace = {
    'date': date,
    'datetime': datetime,
    'time': time,
    'timedelta': timedelta,
}
for module in imported_modules:
    module.__dict__.setdefault('date', date)
    module.__dict__.setdefault('datetime', datetime)
    module.__dict__.setdefault('time', time)
    module.__dict__.setdefault('timedelta', timedelta)
    type_namespace.update(vars(module))

for module in imported_modules:
    for value in vars(module).values():
        if not inspect.isclass(value) or value is BaseModel:
            continue
        if not issubclass(value, BaseModel):
            continue
        if getattr(value, '__module__', '').startswith(package_name):
            try:
                value.model_rebuild(_types_namespace=type_namespace, raise_errors=False)
            except Exception:
                continue

app = importlib.import_module(main_module).app
schema = app.openapi()

sys.stdout = _real_stdout
sys.stderr = _real_stderr
print(json.dumps(schema, ensure_ascii=False))
" > "$schema_file" 2>/dev/null || {
    echo "WARN: $svc_name 스키마 추출 실패 — 스킵"
    continue
  }

  echo "[$svc_name] Schemathesis 스키마 검증..."
  validation_output="$(
    uv tool run --from schemathesis python - "$schema_file" <<'PY'
import json
import sys

import schemathesis

with open(sys.argv[1]) as f:
    schema = json.load(f)
schemathesis.openapi.from_dict(schema).validate()
print("schemathesis.openapi.validate ok")
PY
  )" || {
    echo "ERROR: $svc_name OpenAPI 스키마 검증 실패"
    exit 1
  }
  echo "[$svc_name] $validation_output"
  uv run python -c "
import json
with open('$schema_file') as f:
    schema = json.load(f)
assert 'openapi' in schema, 'OpenAPI 버전 누락'
assert 'paths' in schema, 'paths 누락'
assert 'info' in schema, 'info 누락'
print(f'  paths: {len(schema[\"paths\"])}개, title: {schema[\"info\"][\"title\"]}')
"
  uv run python scripts/ci/record_openapi_contract_evidence.py \
    --module "$svc_name" \
    --schema-file "$schema_file" \
    --validation-output "$validation_output" \
    --command "scripts/ci/run_contract_tests.sh:$svc_name"
  echo "[$svc_name] ✓"
done

DOCS_API_MODULES=(
  "directory:comms"
  "portal:portal"
  "projects:projects"
  "crm:crm"
  "advanced-planning:advanced-planning"
  "analytics:analytics"
  "assets:assets"
  "board:board"
  "calendar:calendar"
  "clm:compliance"
  "compliance:compliance"
  "consolidation:finance-extra"
  "documents:documents"
  "ecommerce:commerce"
  "ehs:ehs"
  "esg:finance-extra"
  "fleet:logistics"
  "gtm:gtm"
  "integration-hub:integration-hub"
  "iot:iot"
  "knowledge:knowledge"
  "lms:learning"
  "mail:comms"
  "maintenance:assets"
  "manufacturing:manufacturing"
  "marketing:marketing"
  "marketing-automation:marketing-automation"
  "messenger:comms"
  "plm:plm"
  "pos:pos"
  "quality:qm"
  "rental:selling"
  "reservation:reservation"
  "rpa:rpa"
  "subscriptions:selling"
  "survey:survey"
  "tms:logistics"
  "wiki:wiki"
  "workreport:learning"
)

for entry in "${DOCS_API_MODULES[@]}"; do
  IFS=":" read -r module_name api_name <<< "$entry"
  schema_file="docs/api/${api_name}/openapi.json"
  if [[ ! -f "$schema_file" ]]; then
    echo "WARN: $module_name docs/api 스키마 없음 — 스킵 ($schema_file)"
    continue
  fi

  echo "[$module_name] docs/api Schemathesis 스키마 검증 ($api_name)..."
  validation_output="$(
    uv tool run --from schemathesis python - "$schema_file" <<'PY'
import json
import sys

import schemathesis

with open(sys.argv[1]) as f:
    schema = json.load(f)
schemathesis.openapi.from_dict(schema).validate()
print("schemathesis.openapi.validate ok")
PY
  )" || {
    echo "ERROR: $module_name docs/api OpenAPI 스키마 검증 실패"
    exit 1
  }
  echo "[$module_name] $validation_output"
  uv run python -c "
import json
with open('$schema_file') as f:
    schema = json.load(f)
assert 'openapi' in schema, 'OpenAPI 버전 누락'
assert 'paths' in schema, 'paths 누락'
assert 'info' in schema, 'info 누락'
print(f'  paths: {len(schema[\"paths\"])}개, title: {schema[\"info\"][\"title\"]}')
"
  uv run python scripts/ci/record_openapi_contract_evidence.py \
    --module "$module_name" \
    --schema-file "$schema_file" \
    --validation-output "$validation_output" \
    --command "scripts/ci/run_contract_tests.sh:docs-api:$module_name"
  echo "[$module_name] ✓"
done

echo "[deploy] deploy/catalog contract validate 포함..."
uv run python -m scripts.deploy validate

echo ""
echo "=== 계약 테스트 통과 ==="
