# 클러스터 단위 서비스 병합 설계

> 작성일: 2026-04-14
> 관련 ADR(예정): `0015-cluster-merge-granularity.md`
> 후속 이니셔티브(별도): 보일러플레이트 공통화, plane 재할당, 도메인 바운디드 컨텍스트 재구성

## 1. 배경 · 문제 정의

OneERP 모노레포는 현재 13개 코드 클러스터 아래에 30+ 서브서비스가 존재하며, 각 서브서비스는 독립된 uv workspace 멤버 + `oneerp_*_app/` 디렉터리 + `pyproject.toml`을 보유한다. 이 구조는 다음 오버헤드를 야기한다.

- 신규 기능 추가 시 서비스 단위 스캐폴딩 반복
- `uv sync`·테스트 수집 범위 팽창
- 클러스터 공통 추상화 부재로 도메인 간 중복 로직 누적
- 서브서비스 경계가 도메인 경계와 무관하게 배포·실행 단위로만 존재

본 설계는 **클러스터를 배포 단위로 승격**해 서브서비스를 1차 병합하는 구조 재편을 제시한다. 도메인 재분해·보일러플레이트 공통화는 후속 이니셔티브로 분리한다.

## 2. 목표 · 비목표

### 목표
- 30+ 서브서비스 → 13개 클러스터-서비스 (1:1 병합)
- 파일럿 1개 클러스터(finance)에서 템플릿 확립 후 수평 확장
- 병합 후에도 기존 서브도메인 경계는 디렉터리 수준으로 보존 (하이브리드 D)
- 서브모듈 간 수평 의존을 감지하는 신규 경계 규칙 OE005 도입

### 비목표
- 도메인 재분해(DDD 바운디드 컨텍스트 재구성) — 별도 이니셔티브
- 보일러플레이트 추상화 / 공통 프레임워크 추출 — 후속 이니셔티브
- plane 재할당 / 배포 토폴로지 변경 — 별도 이니셔티브
- API 계약 변경 — 기존 엔드포인트는 그대로 유지

## 3. 병합 기준 (하이브리드)

1. **1차 기준**: 코드 클러스터(= 현재 `services/<cluster>/` 최상위 디렉터리)
2. **예외 처리**: 클러스터를 가로지르는 데이터 결합
   - 코드 병합은 하지 않음
   - 기존 이벤트 체인(NATS/Kafka 토픽) 유지로 경계 고수
   - 식별된 결합 쌍: `sales_order`↔`accounting/journal_entries`, `delivery_note`↔`stock/purchase_receipts` 등

## 4. 파일럿 범위

### 대상: `finance` 클러스터
- 서브서비스 4개: `accounting`, `expenses`, `finance_extra`, `payroll`
- 선정 이유: OTC 리팩토링에서 accounting 맥락 보유, 서브서비스 4개로 중간 규모

### 목표 레이아웃
```
services/finance/
├── pyproject.toml                  # 단일 uv 패키지 oneerp-finance
├── oneerp_finance_app/
│   ├── __init__.py                 # FastAPI app 조립
│   ├── main.py                     # uvicorn 엔트리
│   ├── dto.py                      # 클러스터 공통 DTO
│   ├── shared/                     # 공통 repo factory, 공통 타입
│   ├── accounting/                 # 서브모듈 (기존 서브서비스 평면 보존)
│   ├── expenses/
│   ├── finance_extra/
│   └── payroll/
└── tests/
    ├── unit/
    └── integration/
```

### 서브모듈 간 상호작용 규칙
- 서브모듈 간 직접 import 금지 (OE005)
- 공통 타입·Repository 팩토리는 `shared/`로 승격
- 서브모듈 간 교차 의존은 이벤트 체인 또는 `shared/`를 경유

## 5. 마이그레이션 메커니즘 (4단계)

### Step 1. 구조 이동
- 파일 이동만 수행 (import·로직 미변경)
- `services/finance/accounting/oneerp_accounting_app/` → `services/finance/oneerp_finance_app/accounting/`
- expenses/finance_extra/payroll 동일 패턴
- uv workspace 멤버 4개 제거, `services/finance` 1개 추가

### Step 2. Import 재작성 (codemod)
- `from oneerp_accounting_app.X` → `from oneerp_finance_app.accounting.X`
- 상대 import (`from ..models ...`)는 가능한 한 유지
- 서브모듈 간 직접 import 탐지 → 기본 차단, 승격 필요 시 `shared/`로 이동

### Step 3. FastAPI 조립 통합
- 각 서브모듈 `router`를 `oneerp_finance_app/__init__.py`에서 수집·마운트
- 기존 4개 `main.py` → 통합 1개

### Step 4. 테스트 마이그레이션
- `services/finance/tests/`로 단일 수집 루트 통합
- pytest `conftest.py` 재작성
- 서브모듈별 pytest marker 부여 (`@pytest.mark.accounting` 등)

## 6. 품질 게이트

### 신규 · 기존 규칙
- **OE005 (신규)**: 서브모듈 간 직접 import 금지 — `check_cluster_boundaries.py` 추가
- **OE002 / OE004**: 기존 baseline 유지, 파일럿 커밋 직전·직후 재측정
- **ruff / ty**: 0 에러 유지

### 파일럿 수용 기준
| 항목 | 기준 |
|---|---|
| 기존 unit 테스트 | 신규 실패 0 |
| OTC E2E | 3회 연속 통과 |
| boundary checker | OE002/OE004 비증가, OE005 통과 |
| uv sync | 4 멤버 삭제 + 1 멤버 추가 성공 |
| 컨테이너 빌드 | `uvicorn oneerp_finance_app.main:app` 기동 성공 |

## 7. 롤백 전략

- 단일 브랜치 `refactor/finance-cluster-merge`에서 4단계를 독립 커밋으로 보존 → 부분 롤백 가능
- 기존 4개 서비스의 컨테이너 이미지 태그 보존 → Helm rollback 경로 확보
- 파일럿 실패 시 브랜치 폐기로 main 영향 0

## 8. 롤아웃 계획 (파일럿 이후)

### 순서
1. 파일럿 완료 + ADR-0015 확정
2. 클러스터당 1 PR
3. 병렬 가능 (OTC Phase 2-4에서 검증된 agent 격리 패턴 재사용)

### 우선순위 (서브서비스 수 기준 내림차순)
| 클러스터 | 서브서비스 수 |
|---|---|
| collab | 7 |
| platform | 5+ |
| deploy | 5 |
| finance (파일럿) | 4 |
| marketing | 3 |
| logistics | 2 |
| assets | 2 |
| hr | 2 |
| sales | 2 |
| scm | 1+ |
| compliance | 1 |
| ehs | 1 |
| portal | 1 |

단일 서비스 클러스터(compliance / ehs / portal)는 uv 패키지 이름 정규화만 수행.

## 9. 리스크 · 완화

| 리스크 | 완화 |
|---|---|
| codemod 누락으로 import 깨짐 | 단계별 `uv run ruff check` + `pytest --collect-only`로 즉시 감지 |
| 테스트 수집 경로 변경으로 CI 누락 | 파일럿에서 `pytest --collect-only` 전후 개수 비교 |
| 서브모듈 간 숨은 결합 발견 | Step 2에서 발견 즉시 `shared/` 승격 또는 이벤트 체인 전환 |
| 파일럿 일정 초과 | 파일럿 단독 브랜치로 main 영향 격리, 일정 초과 시 스코프 축소(서브서비스 2개 먼저) |
| 롤아웃 중 클러스터별 충돌 | 클러스터 = 에이전트 = 격리된 디렉터리 원칙 유지 |

## 10. 수용 기준 · 완료 정의

### 파일럿 완료 (finance)
- 레이아웃 §4 달성
- 수용 기준 §6 모두 통과
- ADR-0015 머지
- 본 설계 문서가 ADR에 링크됨

### 이니셔티브 완료
- 13개 클러스터 모두 단일 uv 패키지로 병합
- `check_cluster_boundaries.py` baseline=0
- 서브서비스 수준 `pyproject.toml`·`oneerp_*_app/` 잔존 0
- 후속 이니셔티브(보일러플레이트 공통화)의 진입 조건 충족

## 11. 참고

- OTC 리팩토링 파일럿 (`docs/plans/2026-04-14-otc-boundary-refactoring-implementation.md`) — 병렬 에이전트 격리 패턴 실증
- ADR-0011 런타임 클러스터 분해
- ADR-0014 런타임 plane 분해
