<div align="center">

# OneERP

**ERPNext 기능 동등성을 목표로 하는 오픈소스 ERP**

한국 비즈니스 환경에 최적화된 통합 비즈니스 앱

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[시작하기](docs/getting-started.md) · [문서](docs/) · [기여하기](CONTRIBUTING.md) · [로드맵](ROADMAP.md)

</div>

ERPNext 와 기능 동등성(feature parity)을 목표로 하는 오픈 ERP 구현. ADR-0014 이후 런타임은 **6 개 Runtime Plane** (api/realtime/worker/scheduler/edge/extension) 으로 수렴하며, 48 개 도메인은 `services/` 아래에서 각 plane 이 mount 하는 형태로 공존한다.

---

## 🧭 구조 한눈에

```
OneErp/
├── core/                              # 공통 커널 (uv workspace, git submodule)
│   ├── oneerp_core/                   #   설정·DI·이벤트·repository·document·auth·health…
│   └── tests/unit/                    #   core 단위 테스트
├── planes/                            # 6 Runtime Plane (ADR-0014)
│   ├── api_plane/                     #   P1: ERP 동기 CRUD (21 도메인 mount)
│   ├── realtime_plane/                #   P2: WebSocket/Presence (portal/calendar)
│   ├── worker_plane/                  #   P3: 이벤트 컨슈머 (7 도메인 events/)
│   ├── scheduler_plane/               #   P4: Cron/Batch (analytics/rpa/...)
│   ├── edge_plane/                    #   P5: Gateway/Auth (외부 진입 8080)
│   ├── extension_plane/        #   P6: 외부 커넥터 (iot/integration-hub/...)
│   └── _shared/                       #   plane 공통 (DomainMount, build_plane_app)
├── services/                          # 48 도메인 소스 (각 plane 이 import)
├── deploy/
│   └── catalog/
│       ├── planes.yaml                # compose 렌더링 SoT (6 plane)
│       ├── services.yaml              # Helm/ArgoCD 렌더링 SoT (48 도메인)
│       └── releases/current.yaml
├── docker-compose.yml                 # 생성 파일 — 수정 금지
├── scripts/
│   ├── deploy/                        # catalog.py, generator.py (산출물 렌더링)
│   └── dev/                           # compose-up.sh, compose-down.sh, stack-smoke.sh, init-nats-streams.sh, seed-data.sh
├── web/                               # Next.js 16 프론트엔드 (pnpm workspace, git submodule)
├── tests/                             # e2e 및 cross-service 테스트
├── docs/
│   ├── ARCHITECTURE-MAP.md            # 상세 구조 지도
│   ├── INDEX.md
│   ├── governance/adr/                # 아키텍처 결정 이력 (ADR-0014 포함)
│   ├── engineering/msa/CONSOLIDATION.md
│   ├── developer/, api/, security/, ops/, infra/, user-manual/, tutorials/, onboarding/
└── Makefile
```

**네트워크 모델**: plane 간 통신은 compose 네트워크 hostname 기반 (`http://api-plane:8000`). 외부 진입점은 **edge-plane:8080** 하나뿐. 나머지 plane 과 인프라(postgres/ferretdb/valkey/nats)는 host port 미노출.

---

## 🛠 요구 환경 (Prerequisites)

| 도구 | 버전 | 설치 |
|---|---|---|
| macOS/Linux | — | — |
| Docker + Buildx | 24+, buildx 0.12+ | Docker Desktop |
| Docker Compose | v2.20+ (depends_on.condition: service_healthy 필수) | Docker Desktop 포함 |
| uv | 0.11.1+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Python | 3.14 | `uv python install 3.14` |
| Node.js | 22.x | `nvm install 22` |
| pnpm | 10.30.3 | `corepack enable && corepack prepare pnpm@10.30.3 --activate` |
| git | 2.40+ (submodule 지원) | — |

**서브모듈 초기화** (필수):
```bash
git clone <repo-url> OneErp
cd OneErp
git submodule update --init --recursive
```

`core/` 와 `web/` 는 독립 git 서브모듈이며 루트에서 업데이트 시 반드시 함께 commit 된다.

**Python/Node 의존성 설치**:
```bash
uv sync                   # BE 전체 workspace (core + planes + services)
pnpm install              # FE (web/)
```

**Git hooks 설치** (lefthook 단일 — W1.2 2026-05-14):
```bash
lefthook install          # pre-commit + commit-msg hook 활성화
# 우회: LEFTHOOK=0 env 또는 commit msg 본문에 [skip-hooks] 트레일러
```

> 본 저장소는 *lefthook 단일* 게이트를 사용한다. `.pre-commit-config.yaml` 은 *폐기됨* (W1.2, 2026-05-14). hook 집합: `py-format` (ruff format --check) + `py-lint` (ruff check) + `js-lint` (biome check) + `secrets` (gitleaks) + `artifacts-guard` + `commitlint`.

---

## 🚀 전체 스택 기동 (Docker Compose)

### 기본 경로 — 한 줄로 부팅

```bash
./scripts/dev/compose-up.sh
```

내부 동작:
1. `docker compose --profile plane up -d --build` — 6 plane + 인프라 4개 빌드·기동.
2. `scripts/dev/init-nats-streams.sh` — JetStream `ONEERP` 스트림 선행 생성 (worker-plane 컨테이너 내부에서 실행).
3. `scripts/dev/seed-data.sh` — 기본 테넌트·사용자(`demo/demo1234`) 주입.
4. 6 plane 전부 `/health 200` 검증.

로컬 `docker compose` 기본값은 `pull`이 아니라 `build`다.
즉 `docker compose --profile full up` 또는 `docker compose --profile plane up`를 직접 실행해도 plane/web 이미지는 각 소스 폴더에서 바로 빌드된다.
Harbor 이미지를 다시 쓰려면 아래처럼 `ONEERP_COMPOSE_PULL_POLICY`를 명시한다.

```bash
ONEERP_COMPOSE_PULL_POLICY=missing docker compose --profile full up
```

성공 시 최종 출력:
```
외부 진입: http://127.0.0.1:8080/   (edge-plane gateway)
기본 계정: demo / demo1234
```

### 종료

```bash
./scripts/dev/compose-down.sh                    # 컨테이너만 종료 (볼륨 보존)
docker compose --profile plane down -v           # 볼륨까지 삭제 (초기화)
```

### 스모크 테스트 (재기동 포함)

```bash
PROFILE=plane TIMEOUT=240 scripts/dev/stack-smoke.sh
```

- healthcheck → NATS 스트림 초기화 → 6 plane `/health` → worker-plane 재기동 후 금칙어 검사 (recovery/subject dedup 회귀 방지).
- `NOCLEAN=1` 를 환경변수로 주면 종료 시 `compose down` 을 생략하고 컨테이너를 살려둠 (디버그용).
- `6 pass / 0 fail` + exit 0 이 정상.

---

## 🧩 주요 서비스 엔드포인트

| 서비스 | 외부 | 내부(compose hostname) | 용도 |
|---|---|---|---|
| edge-plane (Gateway) | `http://127.0.0.1:8080` | `edge-plane:8000` | 외부 진입, 라우팅 |
| api-plane | (edge 경유) | `api-plane:8000` | ERP 동기 CRUD 21 도메인 |
| realtime-plane | (edge 경유) | `realtime-plane:8000` | WS/Presence |
| worker-plane | — | `worker-plane:8000` | 이벤트 컨슈머 |
| scheduler-plane | (edge 경유) | `scheduler-plane:8000` | Cron/Batch |
| extension-plane | (edge 경유) | `extension-plane:8000` | 외부 커넥터 |
| ferretdb | — | `ferretdb:27017` | MongoDB 프로토콜 DB |
| postgres | — | `postgres:5432` | FerretDB 백엔드 |
| valkey | — | `valkey:6379` | 캐시/세션 |
| nats | — | `nats:4222`, `nats:8222`(monitoring) | 이벤트 버스 (JetStream) |

도메인 API 호출은 모두 **edge-plane 경유** — `curl http://127.0.0.1:8080/api/selling/...`, `/api/stock/...` 등.

컨테이너 내부 직접 확인:
```bash
docker compose exec api-plane curl -s localhost:8000/health
docker compose exec worker-plane python -c \
  'import urllib.request; print(urllib.request.urlopen("http://localhost:8000/health").status)'
```

---

## 💻 로컬 개발 (compose 없이)

각 plane 은 uv + uvicorn 으로 직접 실행 가능. 인프라(NATS/Ferret/Valkey)는 compose 로 띄우고 plane 만 로컬 Python 으로.

```bash
# 1) 인프라만 기동
docker compose up -d postgres ferretdb valkey nats
EXEC_SERVICE=worker-plane ./scripts/dev/init-nats-streams.sh  # stream 생성

# 2) plane 로컬 실행 (선택)
uv run --package oneerp-plane-api --directory planes/api_plane \
  uvicorn plane_api.main:app --reload --port 8100
uv run --package oneerp-plane-worker --directory planes/worker_plane \
  uvicorn plane_worker.main:app --reload --port 8102
uv run --package oneerp-plane-edge --directory planes/edge_plane \
  uvicorn plane_edge.main:app --reload --port 8104
```

필요한 환경변수 (최소):
```bash
export ONEERP_FERRETDB_URI="mongodb://localhost:27017"   # compose exec 경로로 바꿔야 함
export ONEERP_VALKEY_URL="redis://localhost:6379/0"
export ONEERP_NATS_URL="nats://localhost:4222"
export ONEERP_JWT_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')
export ONEERP_DEBUG=true
```

**주의**: compose 통합 후 NATS/FerretDB 는 host port 를 노출하지 않는다. 로컬 plane 에서 접근하려면 일시적으로 `docker compose port nats 4222` 로 확인하거나, plane 자체를 compose 로 돌리는 기본 경로를 사용하라.

---

## 🎨 프론트엔드 (Next.js 16)

```bash
cd web
pnpm install
pnpm dev                              # http://localhost:3000
```

백엔드 주소는 `.env.local` 의 `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8080` 형태.

프로덕션 빌드:
```bash
pnpm --filter @oneerp/web build
pnpm --filter @oneerp/web typecheck
pnpm --filter @oneerp/web lint
```

---

## ✅ 품질 게이트

- 루트 모노레포 품질 게이트의 정본은 `./scripts/ci/run.sh` 이다. 이 스크립트가 `.gitea/workflows/quality-gates.yml` 에서 호출되며 architecture / boundary / OpenAPI drift / contract+deploy / web gate를 순차 실행한다.

### 백엔드 (BE)

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check .
uv run pytest -m "not integration and not e2e" services/ packages/ core/tests/unit/
uv run python -m scripts.deploy validate     # compose/ArgoCD 산출물 drift 검사
```

### 프론트엔드 (FE)

```bash
pnpm --filter @oneerp/web lint
pnpm --filter @oneerp/web typecheck
pnpm --filter @oneerp/web build
```

### 통합 스모크

```bash
PROFILE=plane TIMEOUT=240 scripts/dev/stack-smoke.sh
```

### 📝 문서 건강성 검사

```bash
./scripts/docs/audit-all.sh
```

5 트랙(S1~S5) 의 체커를 순차 실행하여 `docs/` 건강성을 검증한다.

- **S1** `check_stale_refs.py` — 삭제된 자산 참조·죽은 로컬 링크 (`--fix-dead-links` 로 자동 교정).
- **S2** `render_versions.py` — 버전 표 drift (`--write` 로 교정).
- **S3** `audit_api_drift.py` — OpenAPI schema vs `docs/api/` 비교. 보고서: `docs/generated/api-drift-report.md`.
- **S4** `audit_tutorials.py` — 튜토리얼 bash/json fence 블록 syntax 검증.
- **S5** `audit_architecture.py` — `planes.yaml`/`services.yaml` 실측 집합 vs 구조 문서. 보고서: `docs/generated/architecture-audit-<date>.md`.

설계 문서: `docs/superpowers/specs/2026-04-13-docs-health-audit-design.md`.

---

## 🧪 테스트 전략

| 계층 | 위치 | 실행 |
|---|---|---|
| core 단위 | `core/tests/unit/` | `uv run pytest core/tests/unit/ -q` |
| 도메인 단위 | `services/<domain>/<svc>/tests/unit/` | `uv run pytest services/ -q -m "not integration and not e2e"` |
| plane 부팅 | `tests/` | `uv run pytest tests/ -q` |
| 통합(infra 필요) | `-m integration` 마커 | `uv run pytest -m integration` (인프라 선행 기동) |
| E2E | `tests/e2e/` (Playwright) | `pnpm --filter @oneerp/web test:e2e` |

---

## 🚢 배포 & 산출물 생성

docker-compose.yml / ArgoCD ApplicationSet / Helm chart values 는 **전부 생성 파일**. `deploy/catalog/` 를 수정 후 아래 명령으로 재생성.

```bash
uv run python -m scripts.deploy sync           # 산출물 재생성
uv run python -m scripts.deploy validate       # drift 검증
uv run python -m scripts.deploy scaffold       # 누락된 Helm chart 뼈대 생성
```

**생성물**:
- `docker-compose.yml` (6 plane + 인프라, hostname 기반)
- `deploy/apps/applicationset.yaml` (ArgoCD, 48 도메인 단위)
- `deploy/charts/<service>/values-release.yaml`

이미지 빌드 규칙 (ADR): `docker buildx` + `masblue-builder` 기본 빌더 사용, linux/amd64 단일 플랫폼.

---

## 🗺 이벤트 체인

- **발행**: 각 도메인 routes/service 가 `Outbox` 컬렉션에 기록 → 발행측 plane 의 `OutboxPoller` 가 NATS JetStream 으로 5초 주기 발행.
- **구독**: worker-plane 이 `ONEERP` stream 에서 subject 별로 구독 (durable name: `plane-worker_<subject>`). Task 3 이후 같은 subject 에 다수 핸들러 등록 시 **subject 당 1회 subscribe + composite fan-out** 구조로 운영.
- **Idempotency**: `ProcessedEventStore` (event-level ledger) — 중복 event_id 는 스킵 + ack.
- **Recovery**: worker 재기동 시 stale durable 재사용은 `_is_already_bound` 감지 → `bind=True` 재시도로 자동 복구 (WARNING: `"기존 durable consumer 재사용"` 로그 관측 가능).

자세한 이벤트 사양은 `core/oneerp_core/events/schemas.py` 의 `EventType` 및 각 도메인 `events/handlers.py` 참조.

---

## 🐞 트러블슈팅

### "exec: uvicorn executable not found"
plane 의 `pyproject.toml` dependencies 에 `uvicorn[standard]>=0.34.0` 누락. 추가 후 `uv lock` 재생성 → `docker compose build <plane>`.

### "consumer is already bound to a subscription"
정상 경로 (recovery). `bind=True` 재시도로 자동 복구됨. WARNING 로그만 발생하고 구독은 정상 등록된다. 로그: `기존 durable consumer 재사용: durable=... (bind=True 로 재시도) — 이전 비정상 종료 가능성`.

### "nats: NotFoundError: find_stream_name_by_subject"
NATS JetStream `ONEERP` stream 미생성. `EXEC_SERVICE=worker-plane ./scripts/dev/init-nats-streams.sh` 실행.

### "부분 구독 상태" 로그 등장
Task 3/4 이후에는 구조적으로 발생하지 않는다. 등장 시 회귀 가능성 — `stack-smoke.sh` strict 모드에서 fail 처리됨. `worker-plane` 의 `_EVENT_DOMAINS` 에 events/ 모듈 없는 도메인이 추가되지 않았는지 확인(`core/tests/unit/test_worker_plane_domains.py` 가드).

### compose 버전 문제
`depends_on: condition: service_healthy` 는 compose v2.20+ 필요. 구버전에서는 `docker compose version` 확인 후 업그레이드.

### 볼륨 초기화 (완전 리셋)
```bash
docker compose --profile plane down -v
docker volume prune -f
```

### 서비스명 충돌 (로컬 uvicorn 실행 시)
모노레포에 `app` 패키지명이 4개 서비스에서 충돌. `--directory` 를 반드시 지정.
```bash
uv run --package <oneerp-package> --directory <svc-dir> uvicorn app.main:app --port <port>
```

---

## 📚 더 읽을거리

- `docs/ARCHITECTURE-MAP.md` — 48 서비스·이벤트·릴리스 entry-point
- `docs/engineering/architecture/repo-structure-rules.md` — 저장소 구조/네이밍/소유권 정본
- `docs/infra/ops/rollback.md` — wave 종료/forward-only 롤백 전략
- `docs/ops/runbook-service-deploy.md` — 배포/롤백/검증 Runbook
- `docs/governance/adr/0014-runtime-plane-decomposition.md` — 6 plane 아키텍처 결정
- `docs/engineering/msa/CONSOLIDATION.md` — compose 통합 원칙
- `docs/onboarding/QUICKSTART.md` — 15분 온보딩
- `docs/tutorials/` — 10 개 도메인 업무 흐름 (order-to-cash, procure-to-pay, payroll, …)
- `docs/api/`, `docs/developer/`, `docs/security/`, `docs/ops/` — 영역별 상세

---

## ⚖️ 규약

- 모든 코드/주석/문서는 한국어.
- 테스트 없는 기능 금지.
- 외부 라이브러리 사용 전 `context7` MCP 로 최신 공식 문서 조회.
- 배포 이미지는 `docker buildx` + `masblue-builder` 로 linux/amd64 단일 플랫폼.
- `docker-compose.yml` / `deploy/apps/applicationset.yaml` / `deploy/charts/**/values-release.yaml` 은 **생성 파일** — `deploy/catalog/` 를 수정 후 `uv run python -m scripts.deploy sync` 로 재생성.
- 저장소 구조/네이밍/소유권 정본은 `docs/engineering/architecture/repo-structure-rules.md` 를 따른다.
- 운영 롤백/배포 절차는 `docs/infra/ops/rollback.md` 와 `docs/ops/runbook-service-deploy.md` 를 우선 참조한다.

세부 규약은 `.claude/CLAUDE.md` (프로젝트 지침) 참조.

---

## 🤝 기여하기

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 참조해 주세요.

## 📄 라이선스

이 프로젝트는 [AGPL-3.0](LICENSE) 라이선스 하에 배포됩니다.

Copyright 2024-2026 [Keiailab Co., Ltd.](https://keiailab.com)
