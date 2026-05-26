#!/usr/bin/env bash
# OpenAPI JSON → TypeScript 타입 자동 생성
# 서비스를 HTTP 기동하지 않고 현재 서비스 패키지에서 직접 JSON 추출
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

: "${ONEERP_JWT_SECRET:=contract-gate-dev-secret-000000000000000000000000}"
export ONEERP_JWT_SECRET

OUTPUT_DIR="web/lib/types/generated"
mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_DIR"/*.openapi.json

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

echo "=== OpenAPI → TypeScript 타입 생성 ==="

generated_services=()

for entry in "${SERVICES[@]}"; do
  IFS=":" read -r svc_name svc_dir <<< "$entry"

  if [ ! -d "$svc_dir" ]; then
    echo "SKIP: $svc_dir 디렉토리 없음"
    continue
  fi

  echo "[$svc_name] OpenAPI JSON 추출 중..."

  # Python으로 직접 OpenAPI JSON 추출 (서버 기동 불필요)
  uv run --directory "$svc_dir" python -c "
import contextlib
import importlib
import inspect
import json
import io
import pathlib
import pkgutil
import tomllib
from datetime import date, datetime, time, timedelta

from pydantic import BaseModel

service_dir = pathlib.Path.cwd()
pyproject = tomllib.loads(service_dir.joinpath('pyproject.toml').read_text())
packages = pyproject['tool']['hatch']['build']['targets']['wheel']['packages']
package_name = packages[0]
main_module = f'{package_name}.main'
sink = io.StringIO()

with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
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

print(json.dumps(schema, ensure_ascii=False, indent=2))
" > "$OUTPUT_DIR/${svc_name}.openapi.json" 2>/dev/null || {
    rm -f "$OUTPUT_DIR/${svc_name}.openapi.json"
    echo "WARN: $svc_name OpenAPI 추출 실패 — 스킵"
    continue
  }

  echo "[$svc_name] TypeScript 타입 생성 중..."
  npm exec --prefix web openapi-typescript -- "$OUTPUT_DIR/${svc_name}.openapi.json" \
    -o "$OUTPUT_DIR/${svc_name}.ts" --export-type 2>/dev/null || {
    rm -f "$OUTPUT_DIR/${svc_name}.openapi.json"
    echo "WARN: $svc_name TypeScript 생성 실패 — 스킵"
    continue
  }

  rm -f "$OUTPUT_DIR/${svc_name}.openapi.json"

  generated_services+=("$svc_name")
  echo "[$svc_name] 완료"
done

if [ "${#generated_services[@]}" -gt 0 ]; then
  {
    printf '/**\n'
    printf ' * BE 서비스 OpenAPI 스키마에서 자동 생성된 타입 재수출.\n'
    printf ' * 이 파일은 gen_openapi_types.sh가 자동 생성하므로 직접 수정하지 않는다.\n'
    printf ' */\n\n'
    for svc_name in $(printf '%s\n' "${generated_services[@]}" | sort); do
      printf 'export type * as %s from "./%s";\n' "$(python3 - "$svc_name" <<'PY'
import sys
name = sys.argv[1]
print(''.join(part[:1].upper() + part[1:] for part in name.replace('_', '-').split('-')))
PY
)" "$svc_name"
    done
  } > "$OUTPUT_DIR/index.ts"
fi

echo ""
echo "=== 타입 생성 완료 ==="
