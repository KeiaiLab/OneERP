# OneERP 프로젝트 지침

## 기술 스택

<!-- BEGIN VERSIONS -->
| 영역 | 기술 | 버전 |
|------|------|------|
| BE 프레임워크 | FastAPI + Pydantic v2 | fastapi>=0.115.0, pydantic>=2.11.0 |
| BE 린트/포맷 | ruff | 0.15.0 |
| BE 타입체크 | ty | 0.0.15 |
| BE 패키지 | uv workspace | 0.11.1 |
| FE 프레임워크 | Next.js 16 (App Router, Turbopack) | ^16.0.0 |
| FE 스타일 | Tailwind CSS 4 (CSS-first) | ^4.1.0 |
| FE 린트/포맷 | Biome | ^2.0.0 |
| FE 패키지 | pnpm workspace | 10.30.3 |
| DB | FerretDB (MongoDB 프로토콜) | 2.7.0 |
| Python | 3.14 | 3.14.3 |
| Node.js | 22 | 22.x |

<sub>자동 생성 — `versions.toml` 수정 후 `render_versions.py --write`.</sub>
<!-- END VERSIONS -->

## 모노레포 구조

- `services/` — BE 마이크로서비스 (uv workspace members)
- `packages/core/` — 공통 커널 (uv workspace member)
- `apps/web/` — FE Next.js 앱 (pnpm workspace member)
- `docs/` — 문서
- `tests/e2e/` — E2E 테스트

## 품질 게이트

### BE

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check .
uv run pytest -m "not integration and not e2e" services/ packages/
```

### FE

```bash
pnpm --filter @oneerp/web lint
pnpm --filter @oneerp/web typecheck
pnpm --filter @oneerp/web build
```

## 서비스 실행 (--directory 필수)

모노레포에서 `app` 패키지명이 4개 서비스에서 충돌하므로, `--directory`로 올바른 서비스 디렉토리를 지정해야 한다.

```bash
uv run --package oneerp-{서비스명} --directory services/{서비스명} uvicorn app.main:app --port {포트}
```

## 설정 규칙

- 하드코딩 금지 — 모든 설정은 환경변수(`ONEERP_` 접두사)로 주입
- `CoreSettings`(packages/core) → 서비스별 `Settings`(상속)으로 중앙 관리
- `@lru_cache` + `Depends`로 설정 DI

## 코딩 규칙

- 모든 코드/주석은 한국어로 작성
- 테스트 없는 기능은 존재할 수 없다
- 외부 라이브러리 사용 전 context7 MCP로 최신 문서 조회
- 배포 이미지는 `docker buildx`로 linux/amd64만 빌드
- `Annotated[T, Depends()]` 타입 별칭으로 DI
- `from __future__ import annotations` 필수 (FA 규칙)
- `print()` 사용 금지 (T20 규칙) — 로깅 사용
