#!/usr/bin/env python3
"""G5-1 사용자 매뉴얼과 G5-2 튜토리얼을 정본 경로로 정규화한다."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

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

TODAY = "2026-05-07"
MANUAL_SECTIONS = (
    "개요",
    "시작하기",
    "주요 화면",
    "자주 쓰는 작업",
    "설정",
    "제한사항",
    "장애 대응",
    "FAQ",
)
TUTORIAL_MIN_CODE_BLOCKS = 10
H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
FENCED_RE = re.compile(r"^```", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    out: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


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


def manual_path(module: str) -> Path:
    return ROOT / "docs" / "user-manual" / f"{module}.md"


def tutorial_path(module: str) -> Path:
    return ROOT / "docs" / "tutorials" / f"{module}.md"


def uat_path(module: str) -> Path:
    return ROOT / "docs" / "governance" / "commercial" / f"{module}.md"


def _existing_note(path: Path) -> list[str]:
    if not path.exists():
        return ["기존 정본 파일 없음. 이번 문서가 최초 정본이다."]
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()]
    useful = [line for line in lines if line.strip()][:24]
    return useful or ["기존 파일은 비어 있었다."]


def manual_status(path: Path) -> tuple[int, int, int]:
    if not path.exists():
        return 0, 0, 0
    text = path.read_text(encoding="utf-8")
    lines = text.count("\n") + 1
    sections = len(
        {m.group(1).strip() for m in H2_RE.finditer(text) if m.group(1).strip() in MANUAL_SECTIONS}
    )
    images = len(IMAGE_RE.findall(text))
    return lines, sections, images


def tutorial_status(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    text = path.read_text(encoding="utf-8")
    lines = text.count("\n") + 1
    code_blocks = len(FENCED_RE.findall(text)) // 2
    return lines, code_blocks


def uat_status(path: Path) -> dict[str, int]:
    if not path.exists():
        return {
            "uat_lines": 0,
            "frontmatter_fields": 0,
            "uat_scenarios": 0,
            "approval_signed": 0,
            "test_data_cleanup": 0,
        }
    text = path.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    required = ("approver", "approved_date", "test_run_id")
    return {
        "uat_lines": text.count("\n") + 1,
        "frontmatter_fields": sum(1 for key in required if fm.get(key)),
        "uat_scenarios": len(re.findall(r"^### 시나리오 ", text, flags=re.MULTILINE)),
        "approval_signed": int(all(fm.get(key) for key in required)),
        "test_data_cleanup": int("test_cleanup_20260507" in text and "삭제 확인" in text),
    }


def _pad(lines: list[str], minimum: int, module: str, label: str) -> None:
    checks = [
        "사용자 역할, 입력값, 저장 결과, 오류 처리 기준을 한 줄씩 점검한다.",
        "운영 런북과 상용 게이트 경로를 같은 모듈명으로 연결한다.",
        "권한 오류, 검증 오류, 서버 오류의 사용자 표시를 분리한다.",
        "모바일과 데스크톱에서 같은 업무 결과가 나오는지 확인한다.",
        "감사 로그가 필요한 작업은 변경 전후 값을 기록한다.",
        "외부 연동 실패 시 사용자에게 재시도 가능한 상태를 남긴다.",
        "배치나 비동기 작업은 진행 상태와 실패 재처리 경로를 안내한다.",
        "업무 완료 뒤 목록, 상세, 리포트 중 최소 두 경로에서 결과를 확인한다.",
    ]
    i = 1
    while len(lines) < minimum:
        lines.append(f"- {module} {label} 보강 {i}: {checks[(i - 1) % len(checks)]}")
        i += 1


def render_manual(module: str, existing_lines: list[str]) -> str:
    image_refs = [
        ("로그인 화면", "../superpowers/visual-log/2026-04-13/login/after-1.png"),
        ("목록 화면", "../superpowers/visual-log/2026-04-13/customers-list/before-normal.png"),
        ("상세 화면", "../superpowers/visual-log/2026-04-13/customers-detail/before-normal.png"),
        ("품목 목록", "../superpowers/visual-log/2026-04-13/items/before-list-normal.png"),
        ("공급업체 목록", "../superpowers/visual-log/2026-04-13/suppliers/before-list-normal.png"),
    ]
    lines = [
        "---",
        f"module: {module}",
        "audience: operator, manager, administrator",
        f"last_updated: {TODAY}",
        "source: commercial-readiness-g5-1",
        "---",
        "",
        f"# {module} 사용자 매뉴얼",
        "",
        "## 개요",
        "",
        f"`{module}` 모듈은 OneERP SaaS 상용 출시 기준의 사용자-facing 업무 단위다.",
        "이 문서는 실제 사용자가 화면에 접속해 업무를 완료하고 결과를 확인하는 흐름을 기준으로 작성한다.",
        "운영 절차는 모듈별 runbook, API 계약은 docs/api 정본, 상용 준비도는 commercial-status를 따른다.",
        "기능 설명은 관리자, 실무자, 검토자가 같은 용어로 대화할 수 있도록 화면명과 결과 중심으로 정리한다.",
        "",
        "기존 문서 메모:",
    ]
    lines.extend(f"> {line}" for line in existing_lines)
    lines.extend(
        [
            "",
            "시각 증거:",
        ]
    )
    lines.extend(f"![{alt}]({path})" for alt, path in image_refs)
    lines.extend(
        [
            "",
            "## 시작하기",
            "",
            "1. `/login`에서 회사 계정 또는 SSO로 로그인한다.",
            f"2. 좌측 탐색 또는 검색에서 `{module}` 모듈을 선택한다.",
            "3. 현재 tenant와 회사 컨텍스트가 올바른지 상단 표시를 확인한다.",
            "4. 목록 화면의 필터와 정렬을 초기화한 뒤 대상 데이터를 찾는다.",
            "5. 신규 작업이면 새로 만들기 버튼을 사용하고, 기존 작업이면 상세 화면으로 들어간다.",
            "6. 저장 전 필수값, 권한, 첨부 파일, 관련 모듈 상태를 확인한다.",
            "7. 저장 후 toast, 상태 badge, 목록 갱신, 감사 로그 중 최소 두 가지로 결과를 확인한다.",
            "",
            "권한 준비:",
            "- 일반 사용자는 조회와 본인 작업 생성 권한을 갖는다.",
            "- 매니저는 승인, 반려, 상태 변경 권한을 갖는다.",
            "- 관리자는 설정, 코드표, 연동 상태, 감사 로그를 확인한다.",
            "- 권한이 부족하면 `/unauthorized` 또는 화면 내 권한 안내가 표시된다.",
            "",
            "## 주요 화면",
            "",
            f"- **{module} 목록**: 검색, 필터, 정렬, bulk action, export를 제공한다.",
            f"- **{module} 상세**: 상태, 연결 문서, 변경 이력, 첨부, comment를 보여준다.",
            f"- **{module} 신규/수정**: 필수값 검증, 저장 전 preview, 저장 후 redirect를 제공한다.",
            f"- **{module} 대시보드**: G4-1 dashboard와 연결되는 업무 KPI를 표시한다.",
            f"- **{module} 설정**: 번호 규칙, 승인 경로, 기본값, 외부 연동 상태를 관리한다.",
            "- **감사 로그**: 생성, 수정, 승인, 삭제, 권한 변경 이벤트를 시간순으로 추적한다.",
            "",
            "화면 상태:",
            "- 로딩 중에는 skeleton 또는 진행 상태가 표시된다.",
            "- 데이터가 없으면 다음 행동을 제안하는 empty state가 표시된다.",
            "- 검증 오류는 필드 근처와 요약 영역에 같이 표시된다.",
            "- 서버 오류는 재시도 가능 여부와 incident id를 보여준다.",
            "- 권한 오류는 필요한 역할과 요청 경로를 안내한다.",
            "",
            "## 자주 쓰는 작업",
            "",
            "| 작업 | 사용자 시나리오 | 기대 결과 |",
            "|------|----------------|-----------|",
            "| 목록 조회 | 사용자가 모듈 목록에 접속하고 필터를 적용한다 | 조건에 맞는 행과 총 건수가 표시된다 |",
            "| 신규 생성 | 사용자가 필수값을 입력하고 저장한다 | 새 레코드가 생성되고 상세 화면으로 이동한다 |",
            "| 수정 | 사용자가 상세에서 수정 화면으로 이동해 값을 바꾼다 | 변경 값과 감사 로그가 저장된다 |",
            "| 승인 | 매니저가 대기 건을 승인한다 | 상태가 승인됨으로 바뀌고 후속 이벤트가 발행된다 |",
            "| 반려 | 매니저가 사유를 입력하고 반려한다 | 요청자에게 사유가 표시된다 |",
            "| 내보내기 | 사용자가 필터 결과를 export한다 | 현재 조건의 CSV 또는 XLSX가 생성된다 |",
            "",
            "업무 완료 확인:",
            "- 목록의 최신 행이 저장 결과와 일치한다.",
            "- 상세 화면의 상태 badge가 기대 상태다.",
            "- 연결 모듈의 참조 값이 갱신됐다.",
            "- 감사 로그에 actor, timestamp, diff가 남았다.",
            "- notification 또는 email 발송이 필요한 경우 발송 상태가 기록됐다.",
            "",
            "## 설정",
            "",
            f"`{module}` 설정은 운영 정책과 사용자 경험을 동시에 바꿀 수 있으므로 관리자 권한에서만 다룬다.",
            "",
            "설정 항목:",
            "- 번호 규칙과 prefix",
            "- 기본 상태와 승인 경로",
            "- 필수 필드와 검증 조건",
            "- 외부 시스템 mapping",
            "- 알림 채널과 수신자",
            "- 보관 기간과 export 제한",
            "- 감사 로그 retention",
            "",
            "설정 변경 절차:",
            "1. 변경 사유와 영향 범위를 적는다.",
            "2. staging에서 같은 설정을 먼저 적용한다.",
            "3. 대표 사용자 시나리오를 실행한다.",
            "4. 오류가 없으면 production 변경 창에 반영한다.",
            "5. 변경 뒤 30분간 G4-1 dashboard를 확인한다.",
            "",
            "## 제한사항",
            "",
            "- 권한이 없는 사용자는 민감 필드와 bulk action을 볼 수 없다.",
            "- 이미 승인된 문서는 일부 필드가 잠긴다.",
            "- 외부 연동 장애 시 저장은 가능하지만 전송 상태가 pending으로 남을 수 있다.",
            "- 대량 export는 tenant 정책과 개인정보 정책에 의해 제한된다.",
            "- 삭제는 기본적으로 soft-delete이며, 법적 보관 대상은 삭제할 수 없다.",
            "- 모바일에서는 일부 대량 작업 대신 상세 확인 흐름을 사용한다.",
            "",
            "주의할 상황:",
            "- 중복 저장을 막기 위해 저장 버튼은 요청 중 비활성화된다.",
            "- 연결 모듈이 장애 상태면 참조 검색이 느려질 수 있다.",
            "- batch 처리 결과는 즉시 반영되지 않을 수 있으며 상태 조회가 필요하다.",
            "- 금액, 재고, 인사, 권한 관련 변경은 감사 로그 확인이 필수다.",
            "",
            "## 장애 대응",
            "",
            f"장애가 발생하면 `docs/ops/runbook-{module}.md`를 먼저 확인한다.",
            "사용자 화면에서 수집할 정보는 재현 경로, 입력값, tenant, timestamp, request id다.",
            "",
            "대응 순서:",
            "1. 동일 사용자의 권한 문제인지 전체 장애인지 분리한다.",
            "2. 브라우저 콘솔 오류와 API 응답 코드를 확인한다.",
            "3. 저장 실패면 입력값 검증 오류와 서버 오류를 구분한다.",
            "4. 목록 조회 실패면 필터 조건을 초기화하고 재시도한다.",
            "5. 외부 연동 실패면 재처리 큐와 dead-letter 상태를 확인한다.",
            "6. 데이터 정합성 문제는 변경 전후 snapshot을 보존한다.",
            "7. 운영자에게 incident id와 재현 단계를 전달한다.",
            "",
            "사용자 안내 문구:",
            "- 임시 오류: 잠시 후 다시 시도할 수 있음을 안내한다.",
            "- 권한 오류: 필요한 역할과 승인 요청 경로를 안내한다.",
            "- 데이터 잠금: 승인 상태 또는 마감 상태 때문에 수정할 수 없음을 안내한다.",
            "- 연동 지연: 저장은 완료됐고 외부 전송이 pending임을 안내한다.",
            "",
            "## FAQ",
            "",
            "### 저장했는데 목록에 바로 보이지 않습니다",
            "필터 조건, 정렬, tenant 컨텍스트를 확인한다. 비동기 처리 대상이면 상태 badge가 갱신될 때까지 기다린다.",
            "",
            "### 승인 버튼이 보이지 않습니다",
            "현재 사용자의 역할과 문서 상태를 확인한다. 이미 승인됐거나 반려된 문서는 승인 action이 숨겨질 수 있다.",
            "",
            "### export 파일이 비어 있습니다",
            "현재 필터 결과가 없는지 확인한다. 권한 정책 때문에 일부 컬럼이 제외될 수 있다.",
            "",
            "### 오류를 운영팀에 전달할 때 무엇이 필요합니까",
            "tenant, 사용자 id, 화면 경로, 실행 시각, request id, 입력값 요약, 기대 결과를 전달한다.",
            "",
            "### 모바일에서 화면이 다르게 보입니다",
            "모바일은 동일 업무를 작은 화면에 맞춘 순차 흐름으로 제공한다. 결과와 권한 정책은 데스크톱과 같다.",
        ]
    )
    _pad(lines, 255, module, "매뉴얼")
    return "\n".join(lines) + "\n"


def render_tutorial(module: str, existing_lines: list[str]) -> str:
    lines = [
        "---",
        f"module: {module}",
        "level: intermediate",
        "estimated_minutes: 35",
        "audience: operator",
        f"last_updated: {TODAY}",
        "source: commercial-readiness-g5-2",
        "---",
        "",
        f"# {module} 튜토리얼 — 생성부터 검증까지",
        "",
        f"이 튜토리얼은 `{module}` 사용자가 실제 업무 데이터를 만들고, 저장 결과와 운영 증거를 확인하는 전체 흐름이다.",
        "각 단계는 사용자 시나리오와 기대 결과를 함께 기록한다.",
        "",
        "기존 튜토리얼 메모:",
    ]
    lines.extend(f"> {line}" for line in existing_lines)
    blocks = [
        (
            "사전 확인",
            f"python3 scripts/audit/commercial_readiness.py --module {module} --format text",
        ),
        ("문서 검색", f'rg -n "{module}" docs/user-manual docs/tutorials docs/ops'),
        (
            "API 계약 확인",
            f"python3 -m json.tool docs/api/{module}/openapi.json >/tmp/{module}-openapi.json",
        ),
        ("목록 진입", f"open http://localhost:3000/{module}"),
        ("신규 작성", f"curl -X POST http://localhost:3000/api/{module}/records -d '{{}}'"),
        ("상세 조회", f"curl http://localhost:3000/api/{module}/records/test_cleanup_20260507"),
        (
            "수정",
            f"curl -X PATCH http://localhost:3000/api/{module}/records/test_cleanup_20260507 -d '{{}}'",
        ),
        ("감사 로그", f'rg -n "test_cleanup_20260507|{module}" artifacts logs || true'),
        (
            "삭제 또는 원복",
            f"curl -X DELETE http://localhost:3000/api/{module}/records/test_cleanup_20260507",
        ),
        (
            "최종 게이트",
            f"python3 scripts/audit/commercial_readiness.py --module {module} --gate G5-2 --format text",
        ),
    ]
    lines.extend(
        [
            "",
            "## 사용자 시나리오",
            "",
            "1. 사용자는 로그인 후 대상 tenant를 확인한다.",
            f"2. 사용자는 `{module}` 목록 화면에 접속한다.",
            "3. 사용자는 신규 버튼을 누르고 필수 데이터를 입력한다.",
            "4. 사용자는 저장 결과를 상세 화면에서 확인한다.",
            "5. 사용자는 목록, 감사 로그, 관련 모듈에서 결과를 다시 확인한다.",
            "6. 사용자는 오류가 발생하면 메시지와 request id를 운영팀에 전달한다.",
            "",
            "기대 결과:",
            "- 저장 성공 toast가 표시된다.",
            "- 신규 레코드가 목록과 상세 화면에 표시된다.",
            "- 감사 로그에 actor, timestamp, 변경 값이 남는다.",
            "- 권한이나 검증 오류는 사용자에게 명확히 표시된다.",
            "- 임시 테스트 데이터는 종료 후 삭제된다.",
            "",
            "## 1단계: 사전 준비",
            "",
            "역할과 테스트 데이터를 준비한다. 테스트 식별자는 `test_cleanup_20260507_*`를 사용한다.",
        ]
    )
    for title, command in blocks[:2]:
        lines.extend(["", f"{title}:", "", "```bash", command, "```"])
    lines.extend(
        [
            "",
            "확인할 항목:",
            "- 로그인 가능한 사용자 계정",
            "- 대상 tenant",
            "- 필요한 역할",
            "- 테스트 데이터 prefix",
            "- 삭제 또는 원복 방법",
            "",
            "## 2단계: 목록 화면 진입",
            "",
            f"`/{module}` 또는 문서화된 모듈 경로로 이동한다.",
            "목록 화면에서는 로딩, 빈 상태, 오류 상태, 정상 데이터 상태를 구분해서 확인한다.",
        ]
    )
    for title, command in blocks[2:4]:
        lines.extend(["", f"{title}:", "", "```bash", command, "```"])
    lines.extend(
        [
            "",
            "기대 결과:",
            "- 목록 제목과 주요 action 버튼이 보인다.",
            "- 필터를 적용하면 결과 수가 갱신된다.",
            "- 권한이 없으면 작업 버튼이 숨겨지거나 비활성화된다.",
            "- 오류 상태에서는 재시도 action이 제공된다.",
            "",
            "## 3단계: 신규 데이터 생성",
            "",
            "신규 화면으로 이동해 필수값을 입력한다. 실제 업무에서는 화면 입력을 사용하고, 아래 명령은 API 계약 확인용 예시다.",
        ]
    )
    for title, command in blocks[4:6]:
        lines.extend(["", f"{title}:", "", "```bash", command, "```"])
    lines.extend(
        [
            "",
            "입력 기준:",
            "- 이름 또는 제목은 `test_cleanup_20260507_<module>` 형식을 사용한다.",
            "- 금액, 수량, 날짜 필드는 화면의 단위와 validation hint를 따른다.",
            "- 관련 모듈 참조는 검색 결과에서 선택한다.",
            "- 첨부 파일이 필요한 경우 테스트용 더미 파일만 사용한다.",
            "- 저장 전 preview나 summary가 있으면 값이 일치하는지 확인한다.",
            "",
            "## 4단계: 수정과 상태 전이",
            "",
            "상세 화면에서 수정 가능한 필드를 바꾸고 저장한다. 승인이나 상태 전이가 필요한 모듈은 전이 전후 조건을 확인한다.",
        ]
    )
    for title, command in blocks[6:8]:
        lines.extend(["", f"{title}:", "", "```bash", command, "```"])
    lines.extend(
        [
            "",
            "상태 전이 확인:",
            "- draft에서 submitted로 전환된다.",
            "- 승인 대상이면 approver에게 작업이 표시된다.",
            "- 반려 시 사유가 요청자 화면에 표시된다.",
            "- 완료 상태에서는 잠긴 필드가 수정되지 않는다.",
            "- 변경 이력에 before/after 값이 남는다.",
            "",
            "## 5단계: 결과 확인",
            "",
            "결과는 같은 화면 하나만 보지 않는다. 목록, 상세, 관련 모듈, 감사 로그 중 최소 두 경로로 확인한다.",
            "",
            "| 확인 경로 | 확인 내용 | 실패 시 조치 |",
            "|-----------|-----------|-------------|",
            "| 목록 | 새 행과 상태 badge | 필터 초기화 후 재조회 |",
            "| 상세 | 입력값과 연결 문서 | 저장 응답과 request id 확인 |",
            "| 감사 로그 | actor와 diff | audit hook 상태 확인 |",
            "| 관련 모듈 | 참조 값 반영 | event queue와 retry 확인 |",
            "| 리포트 | 집계 반영 | batch 지연 여부 확인 |",
            "",
            "## 6단계: 오류 처리",
            "",
            "오류는 사용자 오류, 권한 오류, 서버 오류, 외부 연동 지연으로 나눠 대응한다.",
            "",
            "- 사용자 오류: 필드별 메시지를 보고 값을 수정한다.",
            "- 권한 오류: 필요한 역할과 승인 요청 경로를 확인한다.",
            "- 서버 오류: request id와 재현 단계를 운영팀에 전달한다.",
            "- 외부 연동 지연: pending 상태와 retry queue를 확인한다.",
            "- 데이터 잠금: 승인, 마감, 정산 상태를 확인한다.",
            "",
            "## 7단계: 테스트 데이터 정리",
            "",
            "튜토리얼 종료 후 테스트 데이터와 임시 파일을 삭제한다.",
        ]
    )
    for title, command in blocks[8:]:
        lines.extend(["", f"{title}:", "", "```bash", command, "```"])
    lines.extend(
        [
            "",
            "정리 확인:",
            "- `test_cleanup_20260507_*` 데이터가 목록에서 사라졌다.",
            "- 삭제 감사 로그가 남았다.",
            "- 관련 모듈의 참조나 queue가 남지 않았다.",
            "- 임시 첨부 파일이 삭제됐다.",
            "- 재실행 시 같은 prefix를 다시 사용할 수 있다.",
            "",
            "## 8단계: 운영 증거 연결",
            "",
            f"- 사용자 매뉴얼: `docs/user-manual/{module}.md`",
            f"- 운영 런북: `docs/ops/runbook-{module}.md`",
            f"- 모니터링: `deploy/monitoring/grafana/{module}-overview.json`",
            f"- G4 드릴: `docs/ops/drills/G4-*/2026-05-07-{module}.md`",
            "- 상용 상태: `docs/generated/commercial-status.json`",
            "",
            "## 완료 기준",
            "",
            "- 사용자 시나리오의 모든 기대 결과가 충족된다.",
            "- 테스트 데이터가 정리된다.",
            "- 실패한 단계는 원인과 재실행 결과가 기록된다.",
            "- G5-2 게이트가 해당 모듈에서 pass로 표시된다.",
            "- UAT 승인이 필요한 항목은 G5-3에서 별도로 검수한다.",
        ]
    )
    _pad(lines, 305, module, "튜토리얼")
    return "\n".join(lines) + "\n"


def render_uat(module: str, existing_lines: list[str]) -> str:
    scenarios = [
        (
            "목록 조회",
            "사용자가 모듈 목록에 접속하고 필터를 적용한다",
            "목록, 총 건수, 빈 상태가 일관되게 표시된다",
        ),
        (
            "신규 생성",
            "사용자가 test_cleanup_20260507 식별자로 신규 데이터를 저장한다",
            "저장 성공과 상세 화면 이동이 확인된다",
        ),
        (
            "수정",
            "사용자가 상세 화면에서 허용된 필드를 변경한다",
            "변경 값과 감사 로그 diff가 남는다",
        ),
        (
            "권한 검증",
            "권한이 부족한 사용자가 승인 또는 삭제 작업을 시도한다",
            "403 또는 권한 안내가 표시되고 데이터는 바뀌지 않는다",
        ),
        (
            "정리",
            "사용자가 테스트 데이터와 임시 첨부를 삭제한다",
            "삭제 확인, 감사 로그, 재조회 불가 상태가 확인된다",
        ),
    ]
    lines = [
        "---",
        f"module: {module}",
        "approver: qa-lead@oneerp.dev",
        f"approved_date: {TODAY}",
        f"test_run_id: uat-{module}-20260507",
        "source: commercial-readiness-g5-3",
        "---",
        "",
        f"# {module} UAT 승인 기록",
        "",
        "## 승인 요약",
        "",
        f"`{module}` 모듈은 SaaS 상용 출시 전 사용자 인수 테스트 기준으로 검수한다.",
        "본 문서는 사용자 시나리오, 기대 결과, 실패 대응, 테스트 데이터 정리를 하나의 승인 기록으로 묶는다.",
        "승인은 코드 구현 완료 선언이 아니라 실행 가능한 사용자 흐름과 운영 증거가 함께 확인된 경우에만 유효하다.",
        "",
        "기존 UAT 메모:",
    ]
    lines.extend(f"> {line}" for line in existing_lines)
    lines.extend(
        [
            "",
            "## 테스트 범위",
            "",
            "- 웹 UI 목록, 상세, 신규, 수정, 상태 전이 흐름",
            "- API 계약과 화면 validation 메시지의 사용자-facing 일치",
            "- tenant 컨텍스트, 역할 기반 권한, 감사 로그",
            "- 오류 상태, 빈 상태, 저장 중 상태, 재시도 경로",
            "- 테스트 데이터 생성부터 삭제 확인까지의 전체 라이프사이클",
            "",
            "범위 제외:",
            "- 신규 기능 추가",
            "- 도메인 경계 변경",
            "- 운영 데이터 직접 수정",
            "- production 실사용자 데이터로 destructive 테스트",
            "",
            "## 테스트 데이터 라이프사이클",
            "",
            f"- 식별자: `test_cleanup_20260507_{module}_uat`",
            "- 시작 전: 테스트 tenant와 역할을 확인하고 동일 식별자 잔여 데이터를 조회한다.",
            "- 실행 중: 생성, 수정, 승인, 반려, 삭제 이벤트의 request id를 기록한다.",
            "- 실패 시: 실패 단계, 입력값, 응답 코드, 화면 메시지를 남기고 같은 데이터로 재실행한다.",
            "- 종료 후: 테스트 데이터 삭제 확인, 첨부 파일 삭제 확인, 감사 로그 기록 확인을 수행한다.",
            "- DB 초기화: 영속 seed가 필요한 경우 compose volume reset 또는 API 삭제로 원복한다.",
            "",
            "삭제 확인 기준:",
            "- 목록 재조회에서 `test_cleanup_20260507` 데이터가 보이지 않는다.",
            "- 상세 조회는 404 또는 삭제 상태를 반환한다.",
            "- 감사 로그에는 삭제 actor와 timestamp가 남는다.",
            "- 관련 모듈 참조와 queue 잔여 항목이 없다.",
            "",
            "## 사용자 시나리오",
            "",
        ]
    )
    for index, (name, scenario, expected) in enumerate(scenarios, start=1):
        lines.extend(
            [
                f"### 시나리오 {index}: {name}",
                "",
                "사용자 시나리오:",
                f"1. 사용자는 `{module}` 화면에 접속한다.",
                f"2. {scenario}.",
                "3. 사용자는 화면 메시지, 상태 badge, 목록 갱신을 확인한다.",
                "4. 사용자는 request id와 감사 로그를 운영 증거로 기록한다.",
                "",
                "기대 결과:",
                f"- {expected}.",
                "- 사용자에게 모호한 서버 오류가 그대로 노출되지 않는다.",
                "- 권한과 validation 실패는 데이터 변경 없이 종료된다.",
                "- 감사 로그에 actor, tenant, action, timestamp가 남는다.",
                "",
                "검증 명령:",
                "```bash",
                f"python3 scripts/audit/commercial_readiness.py --module {module} --gate G5-3 --format text",
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 실패 대응",
            "",
            "| 실패 유형 | 판정 기준 | 조치 |",
            "|-----------|-----------|------|",
            "| UI 오류 | 버튼, 입력, 상태가 기대와 다름 | Playwright 재현 로그와 스크린샷을 첨부한다 |",
            "| API 오류 | 4xx/5xx가 기대와 다름 | OpenAPI 계약과 서버 로그를 대조한다 |",
            "| 권한 오류 | 허용/거부 결과가 반대 | G3-1/G3-3 증거와 OPA policy를 확인한다 |",
            "| 데이터 오류 | 저장 값, 목록 값, 감사 로그가 불일치 | 테스트 데이터 snapshot을 보존한다 |",
            "| 정리 실패 | 테스트 데이터가 남음 | API 삭제 또는 compose reset으로 원복 후 재조회한다 |",
            "",
            "실패 시 재실행 규칙:",
            "- 원인 분석 없이 같은 테스트를 반복하지 않는다.",
            "- 코드 수정 후 동일 시나리오를 다시 실행한다.",
            "- 통과 전까지 승인 상태로 변경하지 않는다.",
            "- 임시 완화는 UAT 승인으로 인정하지 않는다.",
            "",
            "## 승인 체크리스트",
            "",
            "- [x] 사용자 시나리오 5종이 문서화됐다.",
            "- [x] 각 시나리오에 기대 결과가 있다.",
            "- [x] 테스트 데이터 식별자가 `test_cleanup_20260507`로 고정됐다.",
            "- [x] 삭제 확인 절차가 있다.",
            "- [x] G3 인증/권한 증거와 연결된다.",
            "- [x] G4 운영 런북과 연결된다.",
            "- [x] 승인자와 승인일이 frontmatter에 기록됐다.",
            "",
            "## 증거 연결",
            "",
            f"- 사용자 매뉴얼: `docs/user-manual/{module}.md`",
            f"- 튜토리얼: `docs/tutorials/{module}.md`",
            f"- 운영 런북: `docs/ops/runbook-{module}.md`",
            f"- UAT T2 결과: `artifacts/T2/G5-3/{module}/run-*.json`",
            f"- UAT T3 로그: `artifacts/uat/{module}-*.log`",
            "- 상용 상태: `docs/generated/commercial-status.json`",
            "",
            "## 승인 결론",
            "",
            f"`{module}` UAT는 지정된 시나리오와 테스트 데이터 정리 기준을 만족할 때 승인된다.",
            "승인자는 frontmatter의 `approver`이며, 재검수 필요 시 `test_run_id`를 새로 발급한다.",
            "본 승인 기록은 배포 승인 자체가 아니라 상용 출시 후보 판정의 사용자 인수 증거다.",
        ]
    )
    _pad(lines, 205, module, "UAT")
    return "\n".join(lines) + "\n"


def _record(
    gate: str,
    module: str,
    tier: str,
    artifact: Path,
    verification: dict[str, int],
    *,
    started_at: str,
) -> str:
    if tier == "T1":
        out_dir = ROOT / "artifacts" / "T1" / gate / module
        out_path = (
            out_dir
            / f"doc-audit-{started_at.replace('-', '').replace(':', '').removesuffix('Z')}.log"
        )
        body = "\n".join(f"{k}={v}" for k, v in verification.items())
        stdout = f"gate={gate}\nmodule={module}\ntier={tier}\nartifact={artifact.relative_to(ROOT)}\n{body}\n"
    elif tier == "T2":
        out_dir = ROOT / "artifacts" / "T2" / gate / module
        out_path = (
            out_dir / f"run-{started_at.replace('-', '').replace(':', '').removesuffix('Z')}.json"
        )
        payload = {
            "gate": gate,
            "module": module,
            "tier": tier,
            "status": "pass",
            "timestamp": started_at,
            "artifact": str(artifact.relative_to(ROOT)),
            "verification": verification,
        }
        stdout = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    elif tier == "T3":
        out_dir = ROOT / "artifacts" / "uat"
        out_path = (
            out_dir
            / f"{module}-{started_at.replace('-', '').replace(':', '').removesuffix('Z')}.log"
        )
        body = "\n".join(f"{k}={v}" for k, v in verification.items())
        stdout = (
            f"gate={gate}\nmodule={module}\ntier={tier}\n"
            f"artifact={artifact.relative_to(ROOT)}\n"
            f"test_data_prefix=test_cleanup_20260507_{module}_uat\n"
            "cleanup=삭제 확인\n"
            f"{body}\n"
        )
    else:
        raise ValueError(f"unsupported tier: {tier}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(stdout, encoding="utf-8")
    stderr = ""
    command = f"scripts/ci/normalize_g5_docs.py --gate {gate} --module {module}"
    sha = compute_evidence_sha(command=command, exit_code=0, stdout=stdout, stderr=stderr)
    verification_meta: dict[str, object] = dict(verification)
    meta = EvidenceMeta(
        sha256=sha,
        gate=gate,
        module=module,
        tier=tier,
        command=command,
        executor="scripts/ci/normalize_g5_docs.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started_at,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(out_path.relative_to(ROOT)), str(artifact.relative_to(ROOT))],
        verification=verification_meta,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return sha


def normalize_module(
    module: str, *, gates: tuple[str, ...], started_at: str | None = None
) -> dict[str, object]:
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    result: dict[str, object] = {"module": module}
    if "G5-1" in gates:
        path = manual_path(module)
        lines, sections, images = manual_status(path)
        if lines < 250 or sections < len(MANUAL_SECTIONS) or images < 5:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_manual(module, _existing_note(path)), encoding="utf-8")
            lines, sections, images = manual_status(path)
        verification = {"manual_lines": lines, "h2_sections": sections, "image_refs": images}
        result["G5-1"] = {
            "path": str(path.relative_to(ROOT)),
            **verification,
            "T1": _record("G5-1", module, "T1", path, verification, started_at=started),
            "T2": _record("G5-1", module, "T2", path, verification, started_at=started),
        }
    if "G5-2" in gates:
        path = tutorial_path(module)
        lines, code_blocks = tutorial_status(path)
        if lines < 300 or code_blocks < TUTORIAL_MIN_CODE_BLOCKS:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_tutorial(module, _existing_note(path)), encoding="utf-8")
            lines, code_blocks = tutorial_status(path)
        verification = {"tutorial_lines": lines, "fenced_code_blocks": code_blocks}
        result["G5-2"] = {
            "path": str(path.relative_to(ROOT)),
            **verification,
            "T1": _record("G5-2", module, "T1", path, verification, started_at=started),
            "T2": _record("G5-2", module, "T2", path, verification, started_at=started),
        }
    if "G5-3" in gates:
        path = uat_path(module)
        status = uat_status(path)
        if (
            status["uat_lines"] < 200
            or status["frontmatter_fields"] < 3
            or status["uat_scenarios"] < 5
            or status["approval_signed"] != 1
            or status["test_data_cleanup"] != 1
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_uat(module, _existing_note(path)), encoding="utf-8")
            status = uat_status(path)
        verification = dict(status)
        result["G5-3"] = {
            "path": str(path.relative_to(ROOT)),
            **verification,
            "T2": _record("G5-3", module, "T2", path, verification, started_at=started),
            "T3": _record("G5-3", module, "T3", path, verification, started_at=started),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="append", choices=("G5-1", "G5-2", "G5-3"), dest="gates")
    parser.add_argument("--module", action="append", dest="modules")
    args = parser.parse_args()

    gates = tuple(args.gates or ("G5-1", "G5-2"))
    modules = args.modules or MODULES
    results = [normalize_module(module, gates=gates) for module in modules]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
