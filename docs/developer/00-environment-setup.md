# 개발 환경 설정 (Development Environment Setup)

OneERP 로컬 개발 환경을 처음부터 구축하는 절차를 안내한다.
This guide walks through setting up a OneERP local development environment from scratch.

---

## 필수 도구 (Required Tools)

| 도구 (Tool) | 버전 (Version) | 설치 방법 (Installation) |
|------|------|------|
| macOS | Apple Silicon (M1+) | - |
| Python | 3.14.x | `brew install python@3.14` |
| uv | 0.11.x | `brew install astral-sh/tap/uv` |
| Node.js | 22.x | `brew install node@22` |
| pnpm | 10.30.3 | `corepack enable && corepack prepare pnpm@latest --activate` |
| apple/container | 최신 (latest) | [apple/container CLI](https://github.com/apple/container) |

> **Docker Desktop 사용 금지 (Do NOT use Docker Desktop).**
> 모든 컨테이너 빌드/실행은 `apple/container`를 사용한다.
> All container builds must use `apple/container`.

---

## 저장소 클론 (Clone Repository)

```bash
git clone <저장소_URL> OneERP
cd OneERP
```

---

## 의존성 설치 (Install Dependencies)

### BE 의존성 (Backend Dependencies)

uv workspace가 모노레포 (monorepo) 전체 Python 의존성을 한 번에 설치한다.

```bash
uv sync --all-groups --managed-python --python 3.14
```

설치 확인 (Verify):

```bash
uv run python --version
# Python 3.14.x
```

### FE 의존성 (Frontend Dependencies)

```bash
pnpm install
```

설치 확인 (Verify):

```bash
pnpm --filter @oneerp/web exec next --version
# Next.js 16.x.x
```

---

## 로컬 DB 실행 (Start Local Database)

프로젝트 루트의 `docker-compose.yml`로 FerretDB + PostgreSQL을 기동한다.
Start FerretDB + PostgreSQL using the `docker-compose.yml` at project root.

```bash
docker compose up -d
```

> FerretDB는 MongoDB 프로토콜 (MongoDB wire protocol)을 제공한다.
> 연결 URI: `mongodb://localhost:27017`

기동 확인 (Verify):

```bash
docker compose ps
curl -s http://localhost:8088/debug/serverStatus | python -m json.tool
```

---

## BE 서비스 실행 (Run Backend Services)

모노레포에서 모든 서비스가 `app/` 패키지명을 사용하므로, `--package`와 `--directory`를 반드시 지정해야 한다.
In the monorepo, all services use the `app/` package name, so `--package` and `--directory` are required.

```bash
# Gateway (필수 / required)
uv run --package oneerp-gateway --directory services/gateway uvicorn app.main:app --port 8000 --reload

# Selling
uv run --package oneerp-selling --directory services/selling uvicorn app.main:app --port 8001 --reload

# Buying
uv run --package oneerp-buying --directory services/buying uvicorn app.main:app --port 8002 --reload

# Stock
uv run --package oneerp-stock --directory services/stock uvicorn app.main:app --port 8003 --reload

# Accounting
uv run --package oneerp-accounting --directory services/accounting uvicorn app.main:app --port 8004 --reload

# Payroll
uv run --package oneerp-payroll --directory services/payroll uvicorn app.main:app --port 8006 --reload

# Expenses
uv run --package oneerp-expenses --directory services/expenses uvicorn app.main:app --port 8007 --reload
```

> 개발 시에는 작업 중인 서비스만 기동하면 된다.
> During development, only start the services you are working on.

Swagger UI 확인 (Check Swagger UI): `http://localhost:{포트}/docs`

---

## FE 앱 실행 (Run Frontend App)

```bash
pnpm --filter @oneerp/web dev
```

기본적으로 `http://localhost:3000`에서 접근한다.
By default, the app is available at `http://localhost:3000`.

---

## 품질 게이트 실행 (Run Quality Gates)

### 전체 실행 (Run All)

```bash
./scripts/ci/run.sh
```

### BE 개별 실행 (Backend — Individual)

```bash
# 포맷 검사 (Format check)
uv run ruff format --check .

# 린트 (Lint)
uv run ruff check .

# 타입 검사 (Type check)
uv run ty check .

# 단위 테스트 (Unit tests)
uv run pytest -m "not integration and not e2e" packages/

# 서비스별 테스트 (Per-service tests)
uv run --directory services/selling pytest tests/ -m "not integration and not e2e" -q
```

### FE 개별 실행 (Frontend — Individual)

```bash
# Biome 린트/포맷 (Biome lint/format)
pnpm --filter @oneerp/web lint

# TypeScript 타입 검사 (TypeScript type check)
pnpm --filter @oneerp/web typecheck

# Next.js 빌드 (Next.js build)
pnpm --filter @oneerp/web build
```

> **린트 에러 또는 테스트 실패가 1건이라도 있으면 커밋/병합/푸시 불가.**
> **Even a single lint error or test failure blocks commit/merge/push.**

---

## 환경변수 (Environment Variables)

모든 설정은 `ONEERP_` 접두사 환경변수로 주입한다.
All config is injected via `ONEERP_`-prefixed environment variables.

프로젝트 루트에 `.env` 파일을 생성하면 자동으로 로드된다.
Create a `.env` file at project root for auto-loading.

| 변수 (Variable) | 기본값 (Default) | 설명 (Description) |
|------|--------|------|
| `ONEERP_FERRETDB_URI` | `mongodb://localhost:27017` | FerretDB 연결 URI (Connection URI) |
| `ONEERP_DATABASE_NAME` | `oneerp` | 데이터베이스명 (Database name) |
| `ONEERP_DEFAULT_TENANT` | `default` | 기본 테넌트 ID (Default tenant ID) |
| `ONEERP_SERVICE_NAME` | 서비스별 상이 (varies) | 서비스 식별자 (Service identifier) |
| `ONEERP_DEBUG` | `false` | 디버그 모드 (Debug mode) |
