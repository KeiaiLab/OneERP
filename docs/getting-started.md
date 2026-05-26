# Getting Started

OneERP 로컬 개발 환경 셋업 가이드.

## 요구 환경

| 도구 | 버전 | 설치 |
|------|------|------|
| Docker + Compose | 24+ / v2.20+ | [Docker Desktop](https://docker.com/products/docker-desktop/) |
| uv | 0.11.1+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Python | 3.14 | `uv python install 3.14` |
| Node.js | 22.x | `nvm install 22` |
| pnpm | 10.30.3 | `corepack enable && corepack prepare pnpm@10.30.3 --activate` |
| git | 2.40+ | — |

## 빠른 시작 (10분)

### 1. 저장소 클론

```bash
git clone https://github.com/oneerp/oneerp.git
cd oneerp
git submodule update --init --recursive
```

### 2. 의존성 설치

```bash
uv sync           # Python (backend)
pnpm install      # Node.js (frontend)
```

### 3. 환경변수 설정

```bash
cp .env.example .env
```

로컬 개발에는 기본값으로 충분하다.

### 4. 인프라 시작

```bash
docker compose up -d
```

PostgreSQL, FerretDB, Valkey(Redis), NATS가 시작된다.

### 5. Backend 실행

```bash
./scripts/dev/compose-up.sh
```

또는 개별 서비스:

```bash
uv run --package oneerp-gateway --directory services/gateway uvicorn app.main:app --port 8000
```

### 6. Frontend 실행

```bash
pnpm --filter @oneerp/web dev
```

브라우저에서 http://localhost:3000 접속.

## 시크릿 설정

로컬 개발에는 `.env.example`의 기본값으로 충분하다.
프로덕션 배포 시에는 각 서비스별 시크릿을 별도 설정해야 한다.

## 테스트 실행

```bash
# 단위 테스트 (backend)
uv run pytest -m "not integration and not e2e" services/ packages/

# 린트 + 타입체크 (backend)
uv run ruff format --check .
uv run ruff check .
uv run ty check .

# 프론트엔드
pnpm --filter @oneerp/web lint
pnpm --filter @oneerp/web typecheck
```

## 아키텍처 개요

OneERP는 6개 Runtime Plane으로 구성된다:

| Plane | 역할 |
|-------|------|
| API Plane | ERP 동기 CRUD (21 도메인 mount) |
| Realtime Plane | WebSocket/Presence |
| Worker Plane | 이벤트 컨슈머 |
| Scheduler Plane | Cron/Batch |
| Edge Plane | Gateway/Auth (외부 진입점) |
| Extension Plane | 외부 커넥터 |

자세한 아키텍처는 [docs/ARCHITECTURE-MAP.md](ARCHITECTURE-MAP.md)를 참조한다.

## 다음 단계

- [기여 가이드](../CONTRIBUTING.md)
- [API 문서](api/)
