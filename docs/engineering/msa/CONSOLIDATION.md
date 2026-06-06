# MSA 간소화 캠페인 — 48→24 서비스 병합

> **상태**: 2026-04-12 P0 (기반 보강) 진행 중
> **소유**: backend + platform
> **근거 플랜**: `/Users/phil/.claude/plans/warm-wondering-jellyfish.md`

## 배경

OneERP 는 48 독립 FastAPI 서비스로 구성된 대규모 MSA 다. M1~M3 에서 공통 커널(`core/oneerp_core`) 이 통합돼 모든 서비스가 동일 ApprovalMixin · ErrorCatalog · Idempotency · DomainService 규약을 사용한다. 하지만 의미상 분리 불필요한 서비스가 많아 운영·개발 복잡성이 과중하다.

- 로컬 full 기동: **20+ 컨테이너**, M2 Mac 에서도 RAM 16GB+ 소비
- CI matrix: **48 병렬 job**
- 서비스 간 HTTP 호출: **~20 `ONEERP_*_URL`** 환경변수
- compose 미등재: 33개 서비스 (collab/logistics/marketing/portal 등)

## 목표

| 지표 | 현재 | 목표 | Δ |
|------|------|------|-----|
| FastAPI 앱 (services/) | 48 | 19 | **-60%** |
| compose 등록 서비스 | 19 (부분) | 24 (전수) | +실제 기동 범위 |
| uv workspace members | 48 | 19 | -60% |
| CI matrix job | 48 | 19 | -60% |
| 로컬 기동 시간 | 측정 | 측정 × 0.7 | -30% |
| RAM 사용량 | 측정 | 측정 × 0.7 | -30% |
| 내부 HTTP 호출 | ~20 URL | <10 URL | -50% (in-process 치환) |

## 병합 매핑

| # | 신규 클러스터 | 흡수 서비스 | 근거 |
|---|---|---|---|
| 1 | **gateway** | (유지) | 모든 요청 entry + 승인 엔진 |
| 2 | **sales** | selling + crm + rental + reservation | 공통 Customer |
| 3 | **commerce** | pos + subscriptions + ecommerce | 공통 Order 채널 |
| 4 | **scm-core** | stock + manufacturing + quality + maintenance | 공통 Item/BOM |
| 5 | **procurement** | buying + expenses | 공통 Supplier |
| 6 | **finance** | accounting + consolidation + esg | GL/차원 공유 |
| 7 | **hr** | hr + payroll | 직원 마스터 공유 |
| 8 | **learning** | lms + workreport | 직원 활동·교육 |
| 9 | **collab** | calendar + documents + projects + wiki + board + knowledge + survey | 그룹웨어 통합 |
| 10 | **portal** | portal + messenger + mail + directory | 커뮤니케이션 |
| 11 | **logistics** | tms + fleet + advanced-planning | 배송·운송 |
| 12 | **marketing** | marketing + marketing-automation + gtm | 마케팅 스택 |
| 13 | **compliance** | compliance + clm + ehs | 법무·안전·계약 |
| 14 | **assets** | assets + plm | 자산·제품수명 |
| 15 | **analytics** | (유지) | 독립 집계·리포팅 |
| 16 | **rpa** | (유지) | 자동화 로봇 |
| 17 | **iot** | (유지) | 센서·장비 |
| 18 | **integration-hub** | (유지) | 외부 시스템 연동 |
| 19 | **automation-orchestrator** | (유지) | 워크플로 실행 |

**인프라 5종**: ferretdb + postgres + valkey + nats + web → **총 24 compose 서비스**.

## 보존 원칙

**바꾸지 않는 것**:
- 라우트 prefix — `/api/v1/selling/*`, `/api/v1/crm/*` 등 **모두 유지**. FE 및 외부 클라이언트 BC 100%
- 이벤트 체인 — `emit_doc_event` → NATS → EventHandlerRegistry 흐름 유지. 핸들러 경로만 클러스터 내부로 재배치
- 공통 커널 — core/oneerp_core 무변경. 모든 클러스터가 동일 의존
- FE — 377 엔티티 모듈 CRUD 라우트 유지

**바꾸는 것**:
- `services/{domain}/{service}/` 디렉토리 구조 → `services/{domain}/{cluster}/app/{subdomain}/`
- uv workspace member 이름 — `oneerp-selling` → `oneerp-sales` (4 서비스가 한 패키지로)
- Dockerfile 1개/클러스터
- `ONEERP_{SERVICE}_URL` 중 같은 클러스터 내부 참조는 제거 (in-process 함수 호출)

## 단계별 PR 흐름

```
feat/msa-consolidation-p0   — 기반 보강 (generator, .env, stack-smoke, Makefile, CONSOLIDATION.md)
feat/msa-consolidation-p1   — sales 파일럿 (4 서비스 병합)
feat/msa-consolidation-p2a  — scm-core
feat/msa-consolidation-p2b  — finance + hr + procurement
feat/msa-consolidation-p2c  — learning + commerce
feat/msa-consolidation-p2d  — collab + portal
feat/msa-consolidation-p2e  — logistics + marketing + compliance + assets
feat/msa-consolidation-p3   — docker-compose 최종 재설계 (7 profile)
feat/msa-consolidation-p4   — Helm 차트 재정비
feat/msa-consolidation-p5   — CI + 문서 동기화
feat/msa-consolidation-p6   — before/after 지표 리포트
```

각 PR 은 `make stack-smoke` 게이트 통과 필수.

## 롤백 절차

1. 문제 발생 PR 의 merge commit 식별
2. `git revert -m 1 <merge-sha>` → 원복 PR 생성
3. Helm 차트 재정비(P4) 이후 원복은 Flux reconcile 에도 영향 — 반드시 **인프라 팀 alert** 및 staging 우선 확인
4. 롤백 PR 의 `make stack-smoke` 통과 확인

## 관련 문서

- 실행 플랜: `/Users/phil/.claude/plans/warm-wondering-jellyfish.md`
- 서비스 인벤토리: `docs/ARCHITECTURE-MAP.md`
- 상태 SoT: `STATUS 문서(제거됨)`
- 릴리즈 기준: `.planning/program/releases/RELEASE-CRITERIA.md`

---

## 2026-04-12 캠페인 세션 완료 상태

### 해소된 갭 (PR #62 병합)

- `deploy/catalog/services.yaml` 15 → 48 app + web 전수 등록 완료
- `docker-compose.yml` 53 서비스 정의 (48 app + 4 infra + web)
- (ADR-0014 이후 통합: 별도 local compose 파일 없음) 포트 매핑 8001~8052
- `deploy/charts/` 신규 33 Helm 차트 자동 스캐폴드
- `services/*/Dockerfile` 48 전수 커버
- 7 profile 체계 (infra/minimal/starter/business/advanced/platform/full)

### 실측 검증 (2026-04-12 15:56 KST)

```
gateway (port=8001): 200        accounting (8005): 200
selling (8002): 200              buying (8003): 200
stock (8004): 200                expenses (8008): 200
hr (8006): 200                   payroll (8007): 200
crm (8009): 200                  projects (8011): 200
quality (8012): 200              assets (8010): 200
manufacturing (8014): 200        analytics (8013): 200
rpa (8015): 200
```

**15/15 /health 200** — business profile 실제 기동 상태 확인.

### 남은 갭 (후속 세션/Ralph 하네스 이양)

| 갭 | 상태 | 비고 |
|-----|------|------|
| 13 클러스터 physical code merge (48→19 app) | **prereq 필요** | RUNBOOK S6.5 — conftest.py 테스트 격리 리팩터 선행 |
| CI matrix path filter (ci-be.yml) | 대기 | physical merge 완료 후 |
| 이벤트 체인 통합 검증 | 대기 | cluster 병합과 동반 |
| before/after 지표 (RAM/기동 시간) | 대기 | 병합 완료 후 |

### 권장 후속 진입

1. 별도 PR: 48 서비스 `conftest.py` 를 module-level `_client` 에서 pytest fixture 로 리팩터. 이는 48 개 소규모 파일 변경으로 단일 세션 가능.
2. Ralph 하네스 세션 (`.claude/ralph-loop.msa-consolidation.md`) 로 13 클러스터 순차 physical merge 실행.
3. P5 (CI 동기화) + P6 (지표 리포트) 최종 정리.

---

## 최종 실측 스냅샷 (2026-04-12 session-end)

PR #67 까지 병합 후 `minimal` profile 전체 실행 증거.

### 실측 명령

```fish
# (ADR-0014 이전 예시 — 현재는 단일 compose + --profile plane)
docker compose --profile plane up -d
curl -s -o /dev/null -w "edge: %{http_code}\n" http://localhost:8080/health
```

### 결과

```
gateway: 200
web: 307
```

- `gateway:8001/health` → `200 {"status":"ok","service":"gateway","version":"0.1.0"}`
- `web:3000/` → `307 /login` (Next.js 로그인 게이트 정상)
- 인프라 4종(ferretdb, postgres, valkey, nats) healthy

### 빌드 검증

```
ghcr.io/oneerp/gateway:latest  Built (#65)
oneerp-local/web:dev                         Built (#67)
```

### 13 PR 체인 요약 (2026-04-12 단일 세션)

| PR | 주요 성과 |
|----|---------|
| #55 | UI Executive Refined 4계층 완결, 1508 CRUD 상속 |
| #57 | MSA P0 토대 (stack-smoke, CONSOLIDATION, .env) |
| #58 | P1~P6 Runbook + Ralph 프로필 |
| #59 | 제약 A 실측 (packages=[app]) |
| #60 | 세션 artifacts 정리 |
| #61 | 제약 B 실측 (batch 오염) |
| #62 | compose + Helm 48 전수 등록 |
| #63 | STATUS + CONSOLIDATION 종결 |
| #64 | register_service_path + 제약 C |
| #65 | Dockerfile 경로 + smoke script fix |
| #66 | web pnpm-lock 의존 제거 (1차) |
| #67 | web 단일 stage Dockerfile + 실측 빌드 |
| #68 | 최종 실측 스냅샷 문서화 (이 PR) |

### 다음 진입점 (Ralph 하네스 또는 후속 세션)

1. `bash scripts/dev/stack-smoke.sh minimal` — 자동 smoke
2. `make stack-up PROFILE=starter` — 핵심 ERP 흐름 기동
3. `.claude/ralph-loop.msa-consolidation.md` 프로필 로드 → 13 클러스터 병합 iteration
4. `make stack-smoke PROFILE=full` — 48 서비스 전수 실측 (CI)

---

## 2026-04-12: 도메인 병합 동결 — Runtime-Plane 전환 (ADR-0014, 활성)

제약 A~D가 3-domain 병합을 지속적으로 차단하고, 19-cluster 목표 달성 시에도
로컬 RAM 10GB+, replicas 19+ 이 유지되어 **도메인 축의 추가 감축 여지가 고갈**됐다.

이에 따라 **신규 도메인 병합 파일럿을 동결**하고, 대신 **Runtime-Plane 분해**
(ADR-0014)로 방향을 전환한다. 도메인 패키지 구조는 그대로 유지하되, 런타임
프로세스를 6개 Plane(API / Realtime / Worker / Scheduler / Edge / Platform-
Adapter)으로 재조립하여 인스턴스 수를 48 → 6으로 축소한다.

> 2026-04-13 보강: ADR-0011(코드 클러스터)와 ADR-0014(런타임 plane)는
> N:M 직교 축으로 공존한다. 본 섹션은 ADR-0014의 런타임 모델을 다룬다.

- 진행 중 병합 PR (#69~#80): 그대로 merge 허용 (sunk cost, 추가 안 함)
- 신규 도메인 병합 파일럿: **중단**
- M1 스캐폴딩: `planes/api_plane/`, `planes/_shared/`, (ADR-0014 이후 통합: 별도 plane compose 파일 없음)
- M1.5 선결: 도메인 패키지명 리네임 (`packages = ["oneerp_{domain}_app"]`)
  — `sys.modules["app"]` 단일 점유 문제 해결 (selling 39건, stock 25건의
  `from app.*` 절대 import 리라이트 필요)

자세한 근거는 `docs/governance/adr/0014-runtime-plane-decomposition.md`(런타임)
및 `docs/governance/adr/0011-runtime-cluster-decomposition.md`(코드 조직),
`plans/enchanted-snacking-star.md` 참조.

## 2026-04-12 (16:30): M3 + 전 plane 스캐폴딩 완료

ADR-0014 Runtime-Plane 분해가 6개 plane 모두 부팅 가능한 상태에 도달.

### 완료 현황

| Plane | 도메인 수 | 부팅 검증 |
|---|---|---|
| P1 API (ERP 트랜잭션) | 21 | ✅ 21/21 health=200 |
| P2 Realtime | 3 | ✅ 부팅 OK |
| P3 Worker | 11 예정 | ⚠️ 스캐폴드만 (이벤트 구독 로직 M2+ 에서) |
| P4 Scheduler | 4 | ✅ 부팅 OK |
| P5 Edge | 1 (gateway) | ✅ 부팅 OK |
| P6 Platform-Adapter | 10 | ✅ 부팅 OK |

### 패키지 리네임 (M3 전면 적용)

- 39개 서비스 전체를 `oneerp_{service}_app` 으로 리네임 완료
- `sys.modules["app"]` 단일 점유 제약(제약 A) 전면 해소
- 회귀: selling/stock 356 tests pass, 타 서비스 per-service pytest pass.
  pre-existing 실패 2건(platform/rpa 401 auth, collab/survey make_cursor) 제외 신규 회귀 0

### 다음 작업

- M2: Worker Plane 의 이벤트 핸들러 수집 + NATS 구독 등록 구현
- M4: Realtime Plane WebSocket 세션 지속성 E2E 테스트
- Helm values 재구성 (plane 단위 Deployment/HPA)
- CI 시스템 CI 에 plane 부팅 스모크 잡 추가
- legacy 48서비스 (ADR-0014 이후 통합: 별도 local compose 파일 없음) profile deprecation 플래그
