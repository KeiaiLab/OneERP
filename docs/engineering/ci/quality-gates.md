# CI 품질 게이트(강제)

## BE 필수 게이트

- ruff format — check (`ruff==0.15.0`)
- ruff lint (`ruff==0.15.0`)
- ty type check (`ty==0.0.15`) — Q2
  - core/oneerp_core: strict (fail)
  - 전체 저장소: 관측 모드 (`continue-on-error: true`) → Wave 3 strict 전환
  - 설정: `pyproject.toml` `[tool.ty]`
- unit tests + 커버리지 — Q6
  - `pytest -m "not integration and not e2e" core/ services/ --cov --cov-fail-under=50`
  - 임계치 정책: Wave 2 = 50, Wave 3 = 65, Wave 4 = 80
  - 설정: `pyproject.toml` `[tool.coverage.run]`, `[tool.coverage.report]`
  - 결과 artifact: `artifacts/coverage-{core,서비스명}.xml`
- 보안 정적 분석 (bandit) — Q5
  - `uv run bandit -c pyproject.toml -r services/ core/oneerp_core/ -ll -ii`
  - Wave 2: 관측 모드 → Wave 3 HIGH/CRITICAL fail → Wave 4 MEDIUM 이상 fail
  - 설정: `pyproject.toml` `[tool.bandit]`
- 의존성 CVE 스캔 (pip-audit) — Q5
  - `uv run pip-audit --strict --skip-editable`
  - Wave 2: 관측 모드 → Wave 3 KNOWN CVE fail
- OWASP / NoSQL 인젝션 PR 체크리스트 — Q5
  - `docs/security/OWASP-CHECKLIST.md`
- integration tests (FerretDB 포함, `pytest -m integration`)
- e2e tests — 핵심 업무 플로우(판매/구매/재고/회계) + 권한/감사 (→ `docs/engineering/ci/test-strategy.md`)
- migration/schema validation

## FE 필수 게이트

- biome ci (`@biomejs/biome>=2.0.0`)
- tsc --noEmit (TypeScript 타입체크)
- next build (빌드 검증, Turbopack)

## 로컬 실행

```bash
./scripts/ci/run.sh    # BE + FE 통합 품질 게이트
```

## Phase 0 현황

- BE 게이트: ruff format + ruff lint + ty check + pytest unit — **구현 완료**
- FE 게이트: biome ci + tsc --noEmit + next build — **구현 완료**
- integration/e2e: 별도 스크립트(`run_integration.sh`, `run_e2e.sh`)로 분리, docker-compose 전제

## 확인 필요(Phase 1)

- CI 제공자/Runner/Secret 주입 방식
- E2E 인프라(브라우저 실행 환경) 제공 방식
- CI Actions 워크플로우 구성

