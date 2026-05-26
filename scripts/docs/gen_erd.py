#!/usr/bin/env python3
"""Pydantic 모델 → Mermaid erDiagram 자동 생성.

서비스별 models/ 디렉토리를 스캔하여 BaseDocument 상속 클래스의 필드를 추출한다.
"""

from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).resolve().parents[2]

SERVICES = [
    "gateway",
    "selling",
    "buying",
    "stock",
    "accounting",
    "hr",
    "payroll",
    "expenses",
]


def scan_models(service: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """서비스의 모델 디렉토리를 스캔하여 (클래스명, [(필드명, 타입)]) 목록을 반환한다."""
    models_dir = ROOT / "services" / service / "app" / "models"
    if not models_dir.exists():
        return []

    svc_dir = str(ROOT / "services" / service)

    # 이전 서비스의 app.* 모듈 캐시를 제거하여 충돌 방지
    stale_keys = [k for k in sys.modules if k == "app" or k.startswith("app.")]
    for k in stale_keys:
        del sys.modules[k]

    # 현재 서비스 디렉토리를 sys.path 최상위에 배치
    if svc_dir in sys.path:
        sys.path.remove(svc_dir)
    sys.path.insert(0, svc_dir)

    results = []
    for py_file in sorted(models_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        module_name = f"app.models.{py_file.stem}"
        try:
            mod = importlib.import_module(module_name)
        except Exception:
            continue

        for name, cls in inspect.getmembers(mod, inspect.isclass):
            model_fields = getattr(cls, "model_fields", None)
            if not isinstance(model_fields, dict):
                continue
            # BaseDocument 또는 BaseModel 상속 확인
            bases = [b.__name__ for b in cls.__mro__]
            if "BaseDocument" not in bases:
                continue

            fields = []
            for field_name, field_info in model_fields.items():
                if field_name in (
                    "id",
                    "tenant_id",
                    "docstatus",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                ):
                    continue
                annotation = getattr(field_info, "annotation", None)
                type_str = str(annotation) if annotation else "Any"
                # 간단한 타입 표시
                type_str = type_str.replace("typing.", "").replace("<class '", "").replace("'>", "")
                fields.append((field_name, type_str))

            if fields:
                results.append((name, fields))

    return results


def generate_mermaid(service: str, entities: list[tuple[str, list[tuple[str, str]]]]) -> str:
    """Mermaid erDiagram 텍스트를 생성한다."""
    lines = ["---", f"title: {service.upper()} 서비스 ERD", "---", "erDiagram"]
    for entity_name, fields in entities:
        lines.append(f"    {entity_name} {{")
        for field_name, field_type in fields:
            # Mermaid ERD에서는 타입 간소화
            simple_type = field_type.split("|")[0].strip().split("[")[0].strip()
            if "str" in simple_type:
                simple_type = "string"
            elif "int" in simple_type or "float" in simple_type or "Decimal" in simple_type:
                simple_type = "number"
            elif "date" in simple_type.lower():
                simple_type = "date"
            elif "bool" in simple_type:
                simple_type = "boolean"
            else:
                simple_type = "string"
            lines.append(f"        {simple_type} {field_name}")
        lines.append("    }")
    return "\n".join(lines)


def main() -> None:
    """모든 서비스의 ERD를 생성한다."""
    import argparse

    parser = argparse.ArgumentParser(description="ERD 자동 생성")
    parser.add_argument("--check", action="store_true", help="기존 파일과 비교만 수행")
    parser.add_argument("--output-dir", default="docs/generated", help="출력 디렉토리")
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    total_entities = 0
    for service in SERVICES:
        entities = scan_models(service)
        if not entities:
            continue

        mermaid = generate_mermaid(service, entities)
        output_file = output_dir / f"erd-{service}.md"

        content = f"# {service.upper()} 서비스 ERD\n\n> 자동 생성 — `scripts/docs/gen_erd.py`\n\n```mermaid\n{mermaid}\n```\n"

        if args.check:
            if output_file.exists():
                existing = output_file.read_text()
                if existing != content:
                    print(f"DRIFT: {output_file} — 재생성 필요")
                    sys.exit(1)
            else:
                print(f"MISSING: {output_file} — 생성 필요")
                sys.exit(1)
        else:
            output_file.write_text(content)
            print(f"생성: {output_file} ({len(entities)}개 엔티티)")

        total_entities += len(entities)

    print(f"\n총 {total_entities}개 엔티티 처리 완료")


if __name__ == "__main__":
    main()
