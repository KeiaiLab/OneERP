# Docs Health Audit — Design Spec

- **일자**: 2026-04-13
- **상태**: Draft
- **배경**: 이번 세션에서 compose 통합(ADR-0014 + single compose), `.gitea` 제거, NATS recovery, worker subscription cleanup, 대청소 cleanup 을 순차 진행했다. 그 결과 `docs/` 전역에 걸쳐 삭제된 자산 참조, 버전 표 drift, API 문서 drift, 튜토리얼 노후화, 아키텍처 문서 drift 위험이 생겼다. 본 스펙은 다섯 축의 **문서 건강성** 을 독립 체커로 자동 검출·교정하는 기반을 구축한다.

## 1. 목표 / 비목표

### 1.1 목표

1. **5 개의 독립 체커 스크립트**(S1~S5) 를 `scripts/docs/` 에 신설하여, docs/ 건강성의 주요 축을 각각 측정 가능하게 한다.
2. **통합 러너 `scripts/docs/audit-all.sh`** 제공 — 5 체커를 순차 실행하고 요약.
3. 현재 detectable 한 docs drift 를 **초기 cleanup** 으로 정리하여, 구현 직후 `audit-all.sh` 가 exit 0 이 되도록 만든다.
4. CI 연결은 본 스펙 **범위 외**. 로컬/수동 실행이 전제이며, 체커는 `--json` 출력 옵션으로 후속 CI 연동 가능성을 열어 둔다.

### 1.2 비목표

- `.gitea/workflows/` 재구축 또는 CI 파이프라인 연결.
- S3 (API drift) 에서 감지된 drift 의 **실제 문서 교정**(보고서 발행까지만).
- S5 에서 감지된 아키텍처 drift 의 근본 재작성.
- 번역, 표현 교정, 스타일 가이드 준수.

## 2. 아키텍처

5 개 독립 체커 + 1 통합 러너:

```
scripts/docs/
├── check_integrity.py        (기존, 링크·인덱스 — 변경 없음)
├── render_versions.py        (기존, S2 — 대상 목록 축소)
├── check_stale_refs.py       (신규, S1 — 삭제된 자산 참조)
├── audit_api_drift.py        (신규, S3 — OpenAPI 대비 docs/api 비교)
├── audit_tutorials.py        (신규, S4 — 튜토리얼 단계의 syntax/endpoint 유효성)
├── audit_architecture.py     (신규, S5 — ARCHITECTURE-MAP/CONSOLIDATION 대비 현 구조)
└── audit-all.sh              (신규, 통합 러너)
```

공통 규약:
- 각 체커는 **standalone 실행** 가능. `uv run python scripts/docs/<checker>.py [--fix|--write|--mark] [--json]`.
- 이슈 없으면 `exit 0`, 있으면 `exit 1` + 상세 stdout.
- `--json` 옵션은 구조화 출력(후속 CI 용). 본 스펙에서는 옵션 존재만 보장, 스키마는 최소.
- 모든 체커는 `main(args: list[str]) -> int` 엔트리포인트를 제공하여 단위 테스트에서 직접 호출 가능.
- 경로 리터럴은 `Path(__file__).resolve().parents[2]` 기반 `ROOT` 상수로 통일.

트랙-체커 매핑:

| 트랙 | 체커 | 자동 교정 | 초기 cleanup 범위 |
|---|---|---|---|
| S1 stale-ref | `check_stale_refs.py` | `--fix-dead-links` 부분 | 검출된 참조 전수 수정 |
| S2 version-drift | `render_versions.py`(기존) | `--write` | 대상 목록 축소 + drift 교정 |
| S3 api-drift | `audit_api_drift.py` | 없음 | 초기 1회 보고서만 |
| S4 tutorial | `audit_tutorials.py` | `--mark`(배너 append) | 실패 튜토리얼 배너 달기 |
| S5 architecture | `audit_architecture.py` | 없음 | 초기 1회 보고서 + 명백한 drift 수정 |

## 3. 트랙 상세

### 3.1 S1 — `check_stale_refs.py`

**목적**: 삭제된 자산 참조 및 죽은 로컬 링크 검출.

**입력**:
- 대상 파일 집합(glob): `docs/**/*.md`, `README.md`, `AGENTS.md`, `.claude/*.md` 단 `docs/generated/**` 은 생성물이므로 제외.
- 스테일 패턴(상수 `STALE_PATTERNS`, 정규식 리스트):
  - `r"docker-compose\.(local|plane)\.yml"`
  - `r"\.gitea/"`
  - `r"services/[^/\s]+/[^/\s]+/Dockerfile"`
  - `r"scripts/migration/"`
  - `r"devspace\.yaml"`
  - `r"docs/HANDOFF-NEXT-SESSION\.md"`, `r"docs/STATUS\.md"`, `r"docs/gap-analysis-[\w-]+\.md"`
  - `r"RALPH-LOOP-PROMPT\.md"`, `r"AUDIT-REPORT-[\d-]+\.md"`
- 죽은 markdown 링크: `\[[^\]]+\]\(([^)]+)\)` 에서 scheme 없는 상대 경로가 repo 안에 존재하지 않는 경우.

**출력**(stdout):
```
[stale-ref] docs/developer/01-add-new-service.md:42 → "docker-compose.local.yml" (삭제됨)
[dead-link] docs/onboarding/QUICKSTART.md:18 → "00-quickstart.md" (파일 없음)
...
총 N 건 감지 (stale-ref N1, dead-link N2).
```

**교정 옵션**:
- `--fix-dead-links`: 죽은 링크를 plain 텍스트로 변환(링크 텍스트 보존). 스테일 참조는 대화형 판단 없이 안전 치환 불가이므로 수동.
- `--fix` 는 `--fix-dead-links` 의 alias.

**Exit code**: 검출 0건=0, 1건 이상=1. `--fix-dead-links` 로 모두 교정하면 재실행 시 0.

### 3.2 S2 — `render_versions.py` (기존 체커 수정)

**변경점**:
- 내부 상수 `TARGETS` 에서 삭제된 대상 제거:
  - 제거: `docs/onboarding/00-quickstart.md`, `docs/engineering/standards.md` (파일 없음)
  - 유지: `README.md`, `.claude/CLAUDE.md`
- 파일 존재 여부 사전 체크 → 없으면 WARNING 후 skip (기존은 에러 전파).
- `--write` 동작은 기존 그대로 유지.

**초기 cleanup**: `--write` 로 현 drift 교정.

### 3.3 S3 — `audit_api_drift.py`

**목적**: `docs/api/**/*.md` 에 문서화된 엔드포인트·스키마와 현 plane 라우터의 OpenAPI schema 차이를 검출.

**알고리즘**:
1. 대상 plane(`api_plane`, `edge_plane`, `realtime_plane`, `scheduler_plane`, `platform_adapter_plane`, `worker_plane`) 을 **in-process import**.
   - 각 plane 의 `main` 모듈 로드 시 `CoreSettings` 가 env 를 요구하므로, 체커 시작 시 dummy env 주입:
     ```python
     os.environ.setdefault("ONEERP_JWT_SECRET", "x" * 32)
     os.environ.setdefault("ONEERP_DEBUG", "true")
     os.environ.setdefault("ONEERP_FERRETDB_URI", "mongodb://localhost:27017")
     os.environ.setdefault("ONEERP_NATS_URL", "nats://localhost:4222")
     os.environ.setdefault("ONEERP_VALKEY_URL", "redis://localhost:6379/0")
     ```
   - import 실패 시 해당 plane WARNING + skip, 보고서에 명시.
2. 각 FastAPI app 의 `app.openapi()` → `{(method, path): {request_fields, response_fields}}` 세트.
3. `docs/api/**/*.md` 를 정규식으로 파싱:
   - HTTP 라인: `^(GET|POST|PUT|DELETE|PATCH)\s+(\S+)` 추출.
   - 스키마 필드 언급: `^-\s+\`(\w+)\`` 형태의 bullet 이 HTTP 블록 이후 일정 섹션 안에 나오면 필드로 간주(최선 효과 파싱).
4. 양측 diff:
   - `[doc-orphan]` docs 에만 존재하는 엔드포인트.
   - `[doc-missing]` 코드에만 존재하는 엔드포인트(docs 누락).
   - `[doc-skew]` path+method 일치하나 필드 집합 차이.

**출력**:
- stdout 요약.
- `docs/generated/api-drift-report.md` — 상세 표(파일·라인·차이). `git add` 대상.

**교정**: 없음. 보고서만.

**한계**:
- 스키마 비교는 필드 이름 집합 수준. 타입, nullable, example 은 대상 외.
- markdown 파싱이 heuristic — false positive 가능. 보고서에 "수동 검토 필요" 표기.

### 3.4 S4 — `audit_tutorials.py`

**목적**: `docs/tutorials/*.md` 10 개의 코드블록 무결성 검증.

**알고리즘**:
1. 각 파일에서 fenced code block 추출(language tag 포함).
2. 언어별 검증:
   - `bash`/`sh`: 임시 파일에 쓴 뒤 `bash -n` 실행. 오류는 stderr 캡처하여 보고.
   - `json`: `json.loads` 구문 검증.
   - `http`: `^(GET|POST|PUT|DELETE|PATCH)\s+(\S+)` 라인의 path 가 S3 에서 얻은 **모든 plane 전체 path 세트** 중 하나에 prefix-match 되는지(엄밀 일치 아님) 확인.
   - 그 외(`python`/`typescript`/`yaml`): syntax 검증 없이 skip.
3. 파일 단위 결과 집계.

**출력**:
- stdout 요약.
- `--mark` 옵션: 실패 파일 상단에 `> **⚠️ 검증 실패 — 2026-04-13**` 경고 배너 append(idempotent — 이미 있으면 skip).

**Exit code**: 실패 파일 0 = 0, 1 이상 = 1.

### 3.5 S5 — `audit_architecture.py`

**목적**: `docs/ARCHITECTURE-MAP.md`, `docs/engineering/msa/CONSOLIDATION.md`, `docs/governance/adr/*.md` 의 구조 설명과 현 코드 기반 실측 집합의 일치성 체크리스트 생성.

**알고리즘**:
1. 실측 집합 추출:
   - 6 plane: `deploy/catalog/planes.yaml` 의 `planes` key 집합.
   - 48 도메인: `deploy/catalog/services.yaml` 의 `services` key 집합 (web 제외).
   - 7 worker 구독 도메인: `planes/worker_plane/plane_worker/main.py` 의 `_EVENT_DOMAINS` 이름 집합.
2. 문서 집합 추출(heuristic):
   - 각 문서에서 백틱 둘러싸인 소문자+하이픈 토큰(`\`([a-z][a-z0-9-]+)\``) 중 위 실측 집합 원소와 매칭되는 것 수집.
3. 문서별 차이 보고:
   - `[missing]` 실측에는 있으나 문서에 언급 없음.
   - `[orphan]` 문서에는 있으나 실측 집합에 없음(오래된 이름).

**출력**:
- stdout 요약.
- `docs/generated/architecture-audit-<YYYYMMDD>.md` — 문서별 체크리스트.

**한계**: 완전한 자연어 이해 아님. 체커는 실측 가이드를 제공하고 인간이 최종 판단.

## 4. 통합 러너 `scripts/docs/audit-all.sh`

```bash
#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

run() {
  local name="$1"; shift
  echo "=== ${name} ==="
  "$@"
  local rc=$?
  echo "exit=${rc}"
  return $rc
}

fail=0
run "S1 stale-refs" uv run python scripts/docs/check_stale_refs.py || fail=$((fail+1))
run "S2 version-drift" uv run python scripts/docs/render_versions.py || fail=$((fail+1))
run "S3 api-drift" uv run python scripts/docs/audit_api_drift.py || fail=$((fail+1))
run "S4 tutorials" uv run python scripts/docs/audit_tutorials.py || fail=$((fail+1))
run "S5 architecture" uv run python scripts/docs/audit_architecture.py || fail=$((fail+1))

echo
echo "총 실패 트랙: ${fail}"
[[ "$fail" -gt 0 ]] && exit 1
exit 0
```

## 5. 초기 cleanup 범위

구현 직후(spec 마지막 단계에서) 다음을 **이 스펙의 구현 범위 안**에서 수정한다:

- **S1 교정**:
  - `docs/developer/01-add-new-service.md` — `docker-compose.local/plane` 참조를 단일 compose + `--profile plane` 로 갱신.
  - `docs/security/OWASP-CHECKLIST.md` — 동일.
  - `docs/engineering/msa/CONSOLIDATION.md` — compose 통합 반영.
  - `docs/onboarding/QUICKSTART.md` — `00-quickstart.md` 죽은 링크 제거, `docker compose up` 에 `--profile plane` 명시.
  - `docs/engineering/msa/RUNBOOK-cluster-merge.md` — Ralph Harness 전용 문서, 삭제.
- **S2 교정**: `render_versions.py` 의 `TARGETS` 에서 삭제된 파일 제거 후 `--write` 로 drift 교정.
- **S3 초기 실행**: 보고서 `docs/generated/api-drift-report.md` 생성·커밋. 실제 docs/api 교정은 follow-up.
- **S4 초기 실행**: 실패 튜토리얼에 `⚠️ 검증 실패` 배너 달기(`--mark`).
- **S5 초기 실행**: 보고서 `docs/generated/architecture-audit-2026-04-13.md` 생성·커밋. 명백한 drift(예: `ARCHITECTURE-MAP.md` 의 설명이 plane 없이 쓰였다면) 는 구현 중 직접 수정, 판단 필요한 drift 는 follow-up.

**README.md** 하단 "더 읽을거리" 섹션 아래에 "문서 건강성 검사" 문단 추가 — `./scripts/docs/audit-all.sh` 실행법 1단락.

## 6. 테스트 계획

`core/tests/unit/docs/` 신규 디렉토리. 픽스처는 `core/tests/fixtures/docs/<track>-sample/`.

| 체커 | 단위 테스트 케이스 |
|---|---|
| S1 | (a) 스테일 패턴 검출 — 샘플에 `docker-compose.local.yml` 참조 → exit 1. (b) 죽은 링크 검출 — 존재하지 않는 상대 경로 → exit 1. (c) `--fix-dead-links` 적용 후 재실행 → exit 0. |
| S2 | (a) `TARGETS` 에 없는 파일이 있어도 skip WARNING 후 0. (b) drift 있는 target → exit 1. (c) `--write` 후 exit 0. |
| S3 | (a) mocked FastAPI app 과 샘플 docs 비교 — doc-orphan/missing/skew 각각 1건 검출. (b) plane import 실패 시 WARNING 후 다른 plane 은 처리. |
| S4 | (a) bash syntax 에러 → fail. (b) 알 수 없는 http path → fail. (c) 유효 파일 → pass. (d) `--mark` 후 배너 append 멱등성. |
| S5 | (a) 실측 집합과 문서 집합 차이 → `[missing]`/`[orphan]` 각각 1건. (b) 완전 일치 → exit 0. |

**통합 테스트**: `scripts/docs/audit-all.sh` 실제 실행 → 초기 cleanup 후 exit 0.

## 7. 성공 기준

- 5 체커 전부 단위 테스트 PASS.
- 초기 cleanup 반영 상태에서 `./scripts/docs/audit-all.sh` exit 0.
- `docs/generated/api-drift-report.md`, `docs/generated/architecture-audit-2026-04-13.md` 커밋 존재.
- `uv run ruff check scripts/docs/ core/tests/unit/docs/` + `uv run ty check scripts/docs/` 통과.

## 8. 오픈 이슈 (follow-up)

- CI 연결: `.gitea/workflows/` 복원 또는 대체 플랫폼 선택. 본 스펙 범위 외.
- S3 drift 보고서가 보여주는 실제 문서 교정(누락 엔드포인트 문서화, orphan 삭제). 분량이 크면 별도 스펙.
- `audit_api_drift` 의 in-process import 가 인프라 의존 커질 경우(예: startup lifespan 에서 실제 연결 시도) 컨테이너 내부 실행 모드 추가 필요.
- S4 에서 `curl` 실제 실행까지 확장하려면 e2e 파이프라인과 통합 필요.
- S5 의 heuristic 정밀화: 도메인 이름 alias(예: `qm-merged` vs `qm_merged`) 처리.
