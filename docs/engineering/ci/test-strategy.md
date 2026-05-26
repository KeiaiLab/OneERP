# 테스트 전략(초안)

## 목표

- 기능 동등성(Must)의 자동 검증을 “유닛 + 통합 + E2E”로 고정한다.
- 회귀(regression) 방지를 위해 E2E 시나리오를 단일 소스 오브 트루스로 유지한다.

## 계층

- 유닛 테스트: 도메인 규칙/권한 판정/검증 로직
- 통합 테스트: DB(FerretDB) + API + 스키마/인덱스
- E2E 테스트: 핵심 업무 플로우(판매/구매/재고/회계) + 권한/감사

## Phase 0 현황

### pytest 구성

- **importmode**: `importlib` (모노레포 동일 모듈명 충돌 방지)
- **마커**: `integration` (FerretDB 필요), `e2e` (배포 환경 필요)
- **testpaths**: `tests`, `services`, `packages`

### 실행 방법

```bash
# 유닛 테스트 (CI 기본)
uv run pytest -m “not integration and not e2e” services/ packages/

# 통합 테스트 (docker-compose up -d 필요)
./scripts/ci/run_integration.sh

# E2E 테스트 (배포 환경 필요)
./scripts/ci/run_e2e.sh
```

### Phase 0 테스트 현황

| 서비스/패키지 | 테스트 | 상태 |
|---------------|--------|------|
| packages/core | test_errors.py (3건) | 통과 |
| services/gateway | test_health.py (1건) | 통과 |
| services/selling | test_health.py (1건) | 통과 |
| services/stock | test_health.py (1건) | 통과 |
| services/accounting | test_health.py (1건) | 통과 |
| packages/core (integration) | test_ferretdb_smoke.py | FerretDB 필요 |

## 테스트 데이터

- 테스트용 테넌트/회사/회계연도/마스터 데이터 세트 정의(Phase 1)

