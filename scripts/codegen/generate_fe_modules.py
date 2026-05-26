"""FE 모듈 코드젠 — BE EntityMeta + Pydantic 모델에서 EntityConfig TS 파일 자동 생성.

14개 서비스의 entities.py에서 ENTITY_METAS를 AST로 파싱하고,
각 모델의 CreateSchema 필드를 추출하여 올바른 EntityConfig를 생성한다.

사용법:
    uv run python scripts/codegen/generate_fe_modules.py
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- 상수 ---

ROOT = Path(__file__).resolve().parents[2]
SERVICES_DIR = ROOT / "services"
MODULES_DIR = ROOT / "apps" / "web" / "lib" / "modules"

# FE ServiceKey에 없는 서비스 매핑
SERVICE_MAP: dict[str, str] = {
    "manufacturing": "stock",
    "analytics": "accounting",
    "pos": "gateway",
}

# FE에 존재하는 ServiceKey 목록
VALID_SERVICE_KEYS = frozenset(
    {
        "selling",
        "buying",
        "stock",
        "accounting",
        "gateway",
        "hr",
        "payroll",
        "expenses",
        "crm",
        "assets",
        "projects",
        "quality",
    }
)

# Python 타입 → FE FieldType 매핑
TYPE_MAP: dict[str, str] = {
    "str": "text",
    "int": "number",
    "float": "number",
    "Decimal": "currency",
    "bool": "checkbox",
    "date": "date",
    "datetime": "date",
}

# Python 타입 → FE FormatType 매핑 (컬럼용)
FORMAT_MAP: dict[str, str] = {
    "Decimal": "currency",
    "float": "number",
    "int": "number",
    "date": "date",
    "datetime": "date",
}

# 컬럼에 표시하지 않는 필드 패턴
SKIP_COLUMN_FIELDS = frozenset(
    {
        "description",
        "remarks",
        "notes",
        "comment",
        "memo",
        "created_by",
        "updated_by",
        "tenant_id",
    }
)

# 필드 이름에서 한국어 라벨 추정 (공통 패턴)
FIELD_LABEL_MAP: dict[str, str] = {
    "name": "이름",
    "title": "제목",
    "code": "코드",
    "description": "설명",
    "status": "상태",
    "is_active": "활성 여부",
    "is_default": "기본 여부",
    "amount": "금액",
    "total": "합계",
    "total_amount": "총 금액",
    "quantity": "수량",
    "qty": "수량",
    "rate": "단가",
    "date": "날짜",
    "start_date": "시작일",
    "end_date": "종료일",
    "posting_date": "전기일",
    "due_date": "만기일",
    "currency": "통화",
    "company": "회사",
    "remarks": "비고",
    "notes": "메모",
    "item_code": "품목코드",
    "item_name": "품목명",
    "warehouse": "창고",
    "customer": "고객",
    "supplier": "공급사",
    "employee": "직원",
    "employee_id": "직원 ID",
    "employee_name": "직원명",
    "department": "부서",
    "designation": "직급",
    "fiscal_year": "회계연도",
    "account": "계정",
    "account_name": "계정명",
    "debit": "차변",
    "credit": "대변",
    "balance": "잔액",
    "tax_amount": "세액",
    "net_amount": "순액",
    "grand_total": "총합계",
    "discount": "할인",
    "discount_amount": "할인금액",
    "type": "유형",
    "category": "분류",
    "priority": "우선순위",
    "reference": "참조",
    "bank_name": "은행명",
    "account_number": "계좌번호",
}

# --- 데이터 클래스 ---


@dataclass
class FieldInfo:
    """Pydantic 모델 필드 정보."""

    name: str
    python_type: str
    has_default: bool
    default_value: Any = None


@dataclass
class EntityInfo:
    """BE EntityMeta에서 추출한 엔티티 정보."""

    collection: str
    tag: str
    api_path: str
    archetype: str
    service: str  # 서비스 디렉토리명
    create_schema_name: str  # CreateSchema 클래스명
    model_file: str  # 모델 파일 경로 (상대)
    fields: list[FieldInfo] = field(default_factory=list)


# --- AST 파싱 함수 ---


def _extract_string_value(node: ast.expr) -> str | None:
    """AST 노드에서 문자열 값 추출."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_entity_metas_from_file(entities_path: Path, service_name: str) -> list[EntityInfo]:
    """entities.py에서 EntityMeta 인스턴스 정보를 AST로 추출한다."""
    source = entities_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(entities_path))

    # import 문에서 create_schema → 모델 파일 매핑 구축
    # from .models.xxx import YyyCreate 형태
    schema_to_module: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.module:
            continue
        # 상대 import: level >= 1, module = "models.xxx"
        # 절대 import: level == 0, module = ".models.xxx"
        module_str = node.module
        is_models_import = (
            node.level >= 1 and module_str.startswith("models.")
        ) or module_str.startswith(".models.")
        if is_models_import:
            clean_module = module_str.lstrip(".")  # "models.bank_account"
            for alias in node.names:
                if alias.name.endswith("Create"):
                    module_path = clean_module.replace(".", "/") + ".py"
                    schema_to_module[alias.name] = module_path

    entities: list[EntityInfo] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue

        # EntityMeta(...) 호출 감지
        func = node.value
        func_name = ""
        if isinstance(func.func, ast.Name):
            func_name = func.func.id
        elif isinstance(func.func, ast.Attribute):
            func_name = func.func.attr

        if func_name != "EntityMeta":
            continue

        # 키워드 인자 추출
        kwargs: dict[str, Any] = {}
        for kw in func.keywords:
            if kw.arg is None:
                continue
            val = _extract_string_value(kw.value)
            if val is not None:
                kwargs[kw.arg] = val
            elif isinstance(kw.value, ast.Name):
                kwargs[kw.arg] = kw.value.id
            elif isinstance(kw.value, ast.Attribute):
                kwargs[kw.arg] = kw.value.attr

        collection = kwargs.get("collection", "")
        tag = kwargs.get("tag", "")
        api_path = kwargs.get("api_path", "")
        archetype = kwargs.get("archetype", "master")
        create_schema_name = kwargs.get("create_schema", "")

        if not collection or not create_schema_name:
            continue

        model_file = schema_to_module.get(create_schema_name, "")

        entities.append(
            EntityInfo(
                collection=collection,
                tag=tag,
                api_path=api_path,
                archetype=archetype,
                service=service_name,
                create_schema_name=create_schema_name,
                model_file=model_file,
            )
        )

    return entities


def _extract_fields_from_model(model_path: Path, schema_name: str) -> list[FieldInfo]:
    """모델 파일에서 CreateSchema 클래스의 필드를 AST로 추출한다."""
    if not model_path.exists():
        return []

    source = model_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(model_path))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name != schema_name:
            continue

        fields: list[FieldInfo] = []
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign):
                continue
            if not isinstance(stmt.target, ast.Name):
                continue

            field_name = stmt.target.id
            python_type = _resolve_type_annotation(stmt.annotation)
            has_default = stmt.value is not None

            default_value = None
            if has_default and isinstance(stmt.value, ast.Constant):
                default_value = stmt.value.value

            fields.append(
                FieldInfo(
                    name=field_name,
                    python_type=python_type,
                    has_default=has_default,
                    default_value=default_value,
                )
            )

        return fields

    return []


def _resolve_type_annotation(node: ast.expr) -> str:
    """타입 어노테이션 노드에서 기본 타입명 추출."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        # 문자열 어노테이션
        return str(node.value)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        # Optional[X], list[X] 등 → 기본 타입만 추출
        if isinstance(node.value, ast.Name):
            wrapper = node.value.id
            if wrapper in ("Optional", "list", "List"):
                return _resolve_type_annotation(node.slice)
        return _resolve_type_annotation(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        # X | None → X 추출
        left_type = _resolve_type_annotation(node.left)
        if left_type != "None":
            return left_type
        return _resolve_type_annotation(node.right)
    return "str"


# --- TS 코드 생성 ---


def _collection_to_entity(collection: str) -> str:
    """컬렉션명을 FE entity(API 경로명)로 변환. underscore → hyphen."""
    return collection.replace("_", "-")


def _entity_to_filename(entity: str) -> str:
    """entity를 파일명으로 (이미 hyphen 구분이므로 그대로)."""
    return entity


def _entity_to_config_name(entity: str) -> str:
    """entity를 camelCase config 변수명으로 변환.

    예: "bank-accounts" → "bankAccountConfig"
    """
    parts = entity.split("-")
    camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
    return camel + "Config"


def _field_to_fe_type(python_type: str) -> str:
    """Python 타입을 FE FieldType으로 매핑."""
    return TYPE_MAP.get(python_type, "text")


def _field_to_format_type(python_type: str) -> str | None:
    """Python 타입을 FE FormatType으로 매핑 (컬럼용)."""
    return FORMAT_MAP.get(python_type)


def _field_to_label(field_name: str) -> str:
    """필드명에서 한국어 라벨 생성."""
    if field_name in FIELD_LABEL_MAP:
        return FIELD_LABEL_MAP[field_name]
    # snake_case → 공백 구분 (한국어 라벨이 없으면 영문 그대로)
    return field_name.replace("_", " ").title()


def _field_to_header(field_name: str) -> str:
    """필드명에서 컬럼 헤더 생성."""
    return _field_to_label(field_name)


def _get_service_key(service_name: str) -> str:
    """서비스 디렉토리명을 FE ServiceKey로 변환."""
    mapped = SERVICE_MAP.get(service_name, service_name)
    if mapped not in VALID_SERVICE_KEYS:
        # 기본값
        return "gateway"
    return mapped


def _generate_columns(fields: list[FieldInfo]) -> list[dict[str, str]]:
    """필드 목록에서 상위 5개 컬럼 정의 생성."""
    columns = [{"key": "_id", "header": "ID", "width": "180px"}]

    count = 1
    for f in fields:
        if count >= 5:
            break
        if f.name in SKIP_COLUMN_FIELDS:
            continue

        col: dict[str, str] = {"key": f.name, "header": _field_to_header(f.name)}
        fmt = _field_to_format_type(f.python_type)
        if fmt:
            col["formatType"] = fmt
            col["width"] = "120px"
        columns.append(col)
        count += 1

    return columns


def _generate_form_fields(fields: list[FieldInfo]) -> list[dict[str, Any]]:
    """필드 목록에서 formFields 정의 생성."""
    form_fields: list[dict[str, Any]] = []
    for f in fields:
        ff: dict[str, Any] = {
            "key": f.name,
            "label": _field_to_label(f.name),
            "type": _field_to_fe_type(f.python_type),
        }
        if not f.has_default:
            ff["required"] = True
        ff["colSpan"] = 6
        form_fields.append(ff)
    return form_fields


def _generate_ts_file(entity_info: EntityInfo) -> str:
    """엔티티 정보로 TypeScript EntityConfig 파일 내용 생성."""
    entity = _collection_to_entity(entity_info.collection)
    config_name = _entity_to_config_name(entity)
    service_key = _get_service_key(entity_info.service)

    tag = entity_info.tag
    label_singular = tag
    label_plural = f"{tag} 목록"

    columns = _generate_columns(entity_info.fields)
    form_fields = _generate_form_fields(entity_info.fields)

    # TS 문자열 조립
    lines: list[str] = []
    lines.append("// 자동 생성 — scripts/codegen/generate_fe_modules.py")
    lines.append('import type { EntityConfig } from "@/lib/crud/types";')
    lines.append("")
    lines.append(f"export const {config_name}: EntityConfig = {{")
    lines.append(f'  entity: "{entity}",')
    lines.append(f'  service: "{service_key}",')
    lines.append(f'  label: {{ singular: "{label_singular}", plural: "{label_plural}" }},')

    # columns
    lines.append("  columns: [")
    for col in columns:
        parts = [f'key: "{col["key"]}"', f'header: "{col["header"]}"']
        if "width" in col:
            parts.append(f'width: "{col["width"]}"')
        if "formatType" in col:
            parts.append(f'formatType: "{col["formatType"]}"')
        lines.append(f"    {{ {', '.join(parts)} }},")
    lines.append("  ],")

    # formFields
    lines.append("  formFields: [")
    for ff in form_fields:
        parts = [f'key: "{ff["key"]}"', f'label: "{ff["label"]}"', f'type: "{ff["type"]}"']
        if ff.get("required"):
            parts.append("required: true")
        parts.append(f"colSpan: {ff['colSpan']}")
        lines.append(f"    {{ {', '.join(parts)} }},")
    lines.append("  ],")

    # transaction 타입이면 docStatus + actions 추가
    if entity_info.archetype == "transaction":
        lines.append("  docStatus: {")
        lines.append('    field: "docstatus",')
        lines.append("    mapping: {")
        lines.append('      0: { label: "초안", variant: "secondary" },')
        lines.append('      1: { label: "제출됨", variant: "primary" },')
        lines.append('      2: { label: "취소됨", variant: "danger" },')
        lines.append("    },")
        lines.append("  },")
        lines.append("  actions: [")
        lines.append("    {")
        lines.append('      action: "submit",')
        lines.append('      label: "제출",')
        lines.append('      variant: "primary",')
        lines.append("      fromStatus: [0],")
        lines.append('      confirmMessage: "이 문서를 제출하시겠습니까?",')
        lines.append("    },")
        lines.append("    {")
        lines.append('      action: "cancel",')
        lines.append('      label: "취소",')
        lines.append('      variant: "danger",')
        lines.append("      fromStatus: [1],")
        lines.append('      confirmMessage: "이 문서를 취소하시겠습니까?",')
        lines.append("    },")
        lines.append("  ],")

    lines.append("};")
    lines.append("")

    return "\n".join(lines)


def _generate_index_ts(
    all_modules: list[tuple[str, str]],
) -> str:
    """전체 모듈 목록으로 index.ts 내용 생성.

    all_modules: (파일명(확장자 없음), config 변수명) 리스트
    """
    sorted_modules = sorted(all_modules, key=lambda x: x[0])

    lines: list[str] = []
    lines.append("// 자동 생성 — scripts/codegen/generate_fe_modules.py")
    lines.append("/**")
    lines.append(" * 엔티티 모듈 레지스트리 초기화 및 재수출.")
    lines.append(" * 이 파일을 import하면 모든 EntityConfig가 레지스트리에 등록된다.")
    lines.append(" */")
    lines.append("")

    lines.append('import { registerEntity } from "./registry";')
    for filename, config_name in sorted_modules:
        lines.append(f'import {{ {config_name} }} from "./{filename}";')

    lines.append("")
    lines.append(f"// --- 레지스트리 등록 ({len(sorted_modules)}개 엔티티) ---")

    # registerEntity 호출
    for _filename, config_name in sorted_modules:
        lines.append(f"registerEntity({config_name});")

    lines.append("")

    # 재수출
    lines.append("// --- 재수출 ---")
    for filename, config_name in sorted_modules:
        lines.append(f'export {{ {config_name} }} from "./{filename}";')

    lines.append(
        'export { registerEntity, getEntityConfig, getAllEntityConfigs } from "./registry";'
    )
    lines.append("")

    return "\n".join(lines)


# --- 메인 로직 ---


def collect_all_entities() -> list[EntityInfo]:
    """모든 서비스에서 EntityMeta 정보를 수집한다."""
    all_entities: list[EntityInfo] = []

    for service_dir in sorted(SERVICES_DIR.iterdir()):
        if not service_dir.is_dir():
            continue

        entities_path = service_dir / "app" / "entities.py"
        if not entities_path.exists():
            continue

        service_name = service_dir.name
        entities = _extract_entity_metas_from_file(entities_path, service_name)

        # 각 엔티티의 CreateSchema 필드 추출
        for entity in entities:
            if entity.model_file:
                model_path = service_dir / "app" / entity.model_file
                entity.fields = _extract_fields_from_model(model_path, entity.create_schema_name)

        all_entities.extend(entities)

    return all_entities


def get_existing_good_modules() -> set[str]:
    """수작업 모듈 파일명(확장자 없음) 집합을 반환한다.

    @ts-nocheck가 없고, 자동 생성 주석도 없는 파일만 보존 대상이다.
    """
    good: set[str] = set()
    for ts_file in MODULES_DIR.glob("*.ts"):
        if ts_file.name in ("index.ts", "registry.ts"):
            continue
        content = ts_file.read_text(encoding="utf-8", errors="replace")
        # @ts-nocheck 또는 자동 생성 주석이 있으면 재생성 대상
        if "@ts-nocheck" in content:
            continue
        if "자동 생성" in content:
            continue
        good.add(ts_file.stem)
    return good


def get_existing_module_configs() -> dict[str, str]:
    """기존 모듈 파일에서 (파일명, config 변수명) 매핑을 추출한다.

    정상 파일의 config 변수명을 보존하기 위함.
    """
    configs: dict[str, str] = {}
    for ts_file in MODULES_DIR.glob("*.ts"):
        if ts_file.name in ("index.ts", "registry.ts"):
            continue
        content = ts_file.read_text(encoding="utf-8", errors="replace")
        # export const xxxConfig: EntityConfig 패턴 추출
        match = re.search(r"export\s+const\s+(\w+Config)\s*:\s*EntityConfig", content)
        if match:
            configs[ts_file.stem] = match.group(1)
    return configs


def main() -> None:
    """메인 실행."""
    all_entities = collect_all_entities()
    print(f"수집된 엔티티: {len(all_entities)}개")

    good_modules = get_existing_good_modules()
    print(f"기존 정상 모듈 (보존): {len(good_modules)}개")

    existing_configs = get_existing_module_configs()

    # BE 엔티티 → FE 파일명 매핑
    generated_count = 0
    skipped_count = 0
    all_modules: list[tuple[str, str]] = []

    # 기존 정상 모듈을 먼저 등록
    for filename, config_name in existing_configs.items():
        all_modules.append((filename, config_name))

    generated_files: set[str] = set()

    for entity_info in all_entities:
        entity = _collection_to_entity(entity_info.collection)
        filename = _entity_to_filename(entity)

        if filename in good_modules:
            skipped_count += 1
            continue

        # 이미 처리된 파일 건너뛰기
        if filename in generated_files:
            continue

        config_name = _entity_to_config_name(entity)

        # TS 파일 생성
        ts_content = _generate_ts_file(entity_info)
        ts_path = MODULES_DIR / f"{filename}.ts"
        ts_path.write_text(ts_content, encoding="utf-8")

        generated_files.add(filename)
        generated_count += 1

        # all_modules에 추가 (기존 정상 모듈과 중복이면 교체)
        # 이미 good_modules에서 추가된 것은 건너뛰었으므로 여기서 추가
        existing_entry = next((i for i, (fn, _) in enumerate(all_modules) if fn == filename), None)
        if existing_entry is not None:
            all_modules[existing_entry] = (filename, config_name)
        else:
            all_modules.append((filename, config_name))

    # index.ts 재생성
    index_content = _generate_index_ts(all_modules)
    index_path = MODULES_DIR / "index.ts"
    index_path.write_text(index_content, encoding="utf-8")

    print(f"생성된 모듈: {generated_count}개")
    print(f"보존된 모듈: {skipped_count}개")
    print(f"index.ts 재생성: {len(all_modules)}개 엔티티 등록")

    # 잔여 @ts-nocheck 확인
    remaining = 0
    for ts_file in MODULES_DIR.glob("*.ts"):
        if ts_file.name in ("index.ts", "registry.ts"):
            continue
        content = ts_file.read_text(encoding="utf-8", errors="replace")
        if "@ts-nocheck" in content:
            remaining += 1

    if remaining > 0:
        print(f"경고: @ts-nocheck 잔여 {remaining}개 — BE entities.py에 없는 엔티티")
    else:
        print("완료: @ts-nocheck 잔여 0개")


if __name__ == "__main__":
    main()
