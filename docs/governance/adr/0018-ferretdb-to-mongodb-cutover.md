# ADR-0018: FerretDB 폐기, native MongoDB(k8s) 로 완전 cut-over

> ADR(Architecture Decision Record)는 **불변 결정 기록**이다. 결정이 바뀌면 이 파일을 수정하지 말고, 새 번호의 ADR을 만들고 본 ADR의 상태를 `Superseded by ADR-MMMM`으로 갱신한다.

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | **Proposed** (Wave 4 PR 머지 시 Accepted 로 전환) |
| 채택일 | 2026-05-14 |
| 결정권자 | 사용자 (phil) — Wave 4 결정 세션 §①②③ 확정 |
| 영향 범위 | 전체 데이터 영속화, 모든 BE 서비스 (48 도메인), 운영 k8s 환경, docker-compose 로컬 dev, 백업·복구 |
| 관련 ADR | [ADR-0004](./0004-database-standard-ferretdb.md) (수퍼시드 후보), [ADR-0008](./0008-observability-baseline.md), [ADR-0009](./0009-backup-recovery-rpo-rto.md), [ADR-0011](./0011-runtime-cluster-decomposition.md), [ADR-0014](./0014-runtime-plane-decomposition.md) |
| 후속 phase | Wave 4 (W4.2 ~ W4.5) — `~/.claude/plans/woolly-doodling-tarjan.md` Wave 4 섹션 |

## 1. 맥락(Context)

### 1.1 기존 결정과 그 한계

[ADR-0004](./0004-database-standard-ferretdb.md) 는 *MongoDB 와이어 호환 + PostgreSQL 백엔드* 조합인 **FerretDB v2.7.0** 을 채택하고 출구 조건을 명시했다. 채택 동기는 ① 가변 스키마(다국가·산업별 확장 필드) ② PostgreSQL 운영 노하우 ③ MongoDB SSPL 라이선스 회피 ④ `mongo` 클라이언트 도구 활용 가능. 그러나 FerretDB 는 MongoDB 의 *부분 호환* 이며, 일부 집계 연산자, 트랜잭션 의미, 인덱스 옵션, 변경 스트림(change streams) 등에서 차이가 존재함을 ADR-0004 도 명시했다.

### 1.2 현재 운영 상태 (2026-05-14 라이브 검증)

- docker-compose `oneerp` project — 12 컨테이너 healthy (7일 + 신규):
  - `oneerp-ferretdb-1` (2.7.0, host:27018→27017) — 신규 (Wave 0 ferretdb 27017 충돌 회피)
  - `oneerp-postgres-1` (FerretDB backend store, 7일 healthy) — 데이터 영구 보존 의무
  - 6 plane (api/edge/extension/scheduler/realtime/worker) + nats/valkey/web/edge-router
- 외부 host port: 8080 (edge-router), 4222/8222 (nats), 6379 (valkey), 27018 (ferretdb)
- 운영 k8s 환경 (별도) — `mongodb-operator` 사용 가능 (사용자 MEMORY: `public/mongodb-operator` v1.5.0 upstream merged, artifacthub 정상)

### 1.3 트리거 — 본 ADR 작성 사유

대규모 리팩토링 plan (`~/.claude/plans/woolly-doodling-tarjan.md`) Wave 4 진입 시점에서 사용자 결정 D4 = "FerretDB → native MongoDB 전환, uv 기반". 이는 ADR-0004 의 *출구 조건 도달* 을 의미. 또한 부속 결정:

- §① **k8s 적용** — 운영은 k8s, dev 는 docker-compose 병행
- §② **Wave 4 끝 postgres 완전 축출** (full cut-over, dual-read 단계적 이전)
- §③ **pymongo.AsyncMongoClient** (motor 대신 pymongo v4.9+ 의 native async)

### 1.4 제약

- **BC 보존 hard constraint**: postgres_data + nats_data volume 영구 보존, 7일짜리 plane 컨테이너 rolling restart 만, 외부 publish 포트 유지 (Wave 4 ADR 동반 시 ferretdb 27018 host port 만 변경 가능)
- pymongo v4.9+ `AsyncMongoClient` API (context7 MCP 조회 완료, 2026-05-14): `from pymongo import AsyncMongoClient`, 모든 op 가 coroutine, `async for doc in collection.find(...)`, `async with client.start_session()` 패턴 지원
- 사용자 영역 mongodb-operator 진본은 `public/mongodb-operator` v1.5.0 stable (artifacthub.io published) — 본 cluster 적용 가능

## 2. 결정(Decision)

- **선택안**: **FerretDB 를 폐기하고, 운영(k8s)과 dev(docker-compose) 양 환경에서 native MongoDB 로 cut-over 한다. 데이터는 도메인 단위 dual-read → 완전 이전 → postgres+ferretdb 축출 순서로 진행한다.**
- **범위 In**:
  - 모든 48 도메인의 데이터 storage backend
  - 운영 k8s manifest (`deploy/infra/mongodb-*.yaml` 또는 `MongoDB` CR via mongodb-operator)
  - 로컬 dev docker-compose `oneerp-mongodb-1` 서비스 추가
  - BE 6 plane 의 DB connector — pymongo v4.9+ `AsyncMongoClient` 단일화
  - `core/oneerp_core/config.py` `CoreSettings` 의 `mongodb_uri` 신규 + `ferretdb_uri` Wave 4 단계적 제거
  - 마이그레이션 도구 (`migrations/tools/mongodump_pipeline.py` + `verify_collection_parity.py`, uv 기반)
- **범위 Out**:
  - PostgreSQL 의 *별 용도* 사용 — 없음 (현재 postgres-1 컨테이너 = FerretDB backend 단독 용도, FerretDB 폐기와 함께 postgres-1 도 축출)
  - 다른 NoSQL 도입 (DynamoDB / Cosmos / Cassandra 등) — 본 ADR 범위 외
  - 데이터 schema 변경 — collection 구조는 *현재 그대로*. FerretDB가 수용한 동일 BSON document
- **발효 시점**: Wave 4 의 W4.1 (본 ADR) 머지 후 Status: Accepted. W4.2 ~ W4.5 코드 변경 PR 머지로 점진 발효
- **유효 기간**: 무기한 (별 ADR로 superseded 될 때까지). 단 6개월 후 §5.4 측정 지표 회고 의무

## 3. 대안(Alternatives Considered)

### 대안 A — native MongoDB self-host (docker-compose + k8s)
- 설명: 운영 k8s 에 `mongodb-community-server` Deployment + StatefulSet (또는 `public/mongodb-operator` MongoDB CR). dev 는 `mongo:7` docker-compose 서비스. self-host 라 외부 의존성 0.
- 장점: ① 외부 SaaS 비용 0 ② 라이선스 SSPL 직접 적용 (자체 운영, 재배포 안 함) ③ `mongodb-operator` 가 백업/복구/HA 자동화 ④ 데이터 거버넌스 외부 노출 0 ⑤ 클러스터 내 latency 최소
- 단점: ① 운영 자체 부담 (replica set 관리, 백업 자동화 구성) ② mongodb-operator 학습 곡선 (단 본 cluster 가 이미 채택)
- **채택** ✅ — 사용자 §① 결정 + MEMORY의 mongodb-operator 가용성

### 대안 B — MongoDB Atlas (SaaS)
- 설명: Atlas dedicated tier (M10+) cluster, VPC peering 또는 PrivateLink.
- 장점: ① 관리형 — 백업/복구/HA 무관 ② Atlas Search 즉시 가용 ③ 인덱스 추천 등 advisor
- 단점: ① **데이터 외부 노출** (operational data exfiltration risk, 컴플라이언스 측면) ② 비용 (M10 ~$70/월 × 환경별, dev/staging/prod = $200+/월) ③ 네트워크 지연 (k8s cluster ↔ Atlas) ④ 사용자 *Contabo VPS 강제* 정책 (MEMORY `hetzner-rejection-final.md` 와 동일 정신) 과 배치 충돌
- 채택하지 않은 이유: 외부 클라우드 의존 회피 정책 + Self-host 가 운영 노하우 보유 (postgres-operator + valkey-operator 등 다수 operator 이미 운영 중)

### 대안 C — Azure Cosmos DB (MongoDB API)
- 설명: Azure Cosmos DB 의 MongoDB API. RU/s 기반 과금.
- 장점: ① 글로벌 분산 ② Azure 통합
- 단점: ① 부분 호환 (FerretDB 와 비슷한 함정 위험) ② RU/s 모델 학습 부담 ③ Azure 전체 종속
- 채택하지 않은 이유: 부분 호환의 *재발* 위험. 본 ADR 트리거가 바로 FerretDB 의 부분 호환 한계인데 동일 함정에 다시 빠질 가능성

### 대안 D — 현 상태 유지 (Do Nothing, FerretDB 계속 사용)
- 비용: ① 알려진 FerretDB 부분 호환 한계 (ADR-0004 §출구 조건) 계속 누적 ② Change Stream / 트랜잭션 의미 등 production-blocker 발생 시 별 우회 코드 산적 ③ FerretDB 자체의 *minor version 호환성* 책임이 외부 OSS 에 의존
- 리스크: ① 도메인 추가 시마다 *FerretDB 호환 검증* 반복 ② mongo client 도구 일부 명령 (e.g., `db.collection.watch()` change streams, 트랜잭션 retryable writes) 미지원 가능성 ③ 운영 노하우가 *FerretDB-specific* 으로 고립 (general MongoDB 인력 활용 못 함)
- 채택하지 않은 이유: ADR-0004 의 출구 조건 (사용자 가시 명령 미지원 발견 시) 이 사실상 누적된 상태. 사용자 명시 결정 D4 = 전환

## 4. 근거(Rationale)

| 평가 축 | 대안 A (self-host MongoDB) | 비고 |
|---------|------------|------|
| 비용(인력·시간·라이선스·인프라) | 7/10 | SSPL 자체 운영 OK, 인프라 비용 self-host (Contabo VPS 강제 정합), 인력 학습 곡선 1-2주 |
| 리스크(보안·가용성·데이터 손실) | 8/10 | mongodb-operator 가 replica set + HA 자동화. 데이터 외부 노출 0. cut-over 자체의 리스크는 마이그레이션 도구 (W4.4) 로 완화 |
| 운영(모니터링·롤백·일상 부담) | 7/10 | postgres-operator + valkey-operator 운영 패턴 그대로 적용. 모니터링 = Prometheus mongodb-exporter |
| 팀 역량(학습 곡선·운영 노하우) | 7/10 | MongoDB 일반 인력 활용 가능 (FerretDB 보다 광범위). pymongo asyncio API 신규 학습 (motor 와 거의 동일 — 거의 무비용) |

- **결정적 근거**:
  1. **사용자 명시 결정** (D4 + §①②③) — 본 ADR 의 *최상위 input*
  2. **mongodb-operator 운영 인프라 가용** — `public/mongodb-operator` v1.5.0 stable + artifacthub published. cluster 내 *이미 검증된* operator 패턴 (postgres-operator + valkey-operator 와 동일 구조)
- **수용한 트레이드오프**:
  - postgres-1 컨테이너 + ferretdb 의 *완전 축출* 으로 인한 *짧은 cut-over window* 동안의 dual-write 부담
  - pymongo `AsyncMongoClient` 가 motor 보다 *상대적으로 신생* (motor 는 14년 역사) — 단 motor 자체가 *2024 deprecated 방향* 으로 명시, pymongo asyncio 가 *공식 후속*

## 5. 영향(Consequences)

### 5.1 긍정적 영향

- **MongoDB 완전 호환** — 트랜잭션 retryable writes, change streams, $merge/$out 집계, time-series collections, full-text Atlas Search 호환 query 모두 가용
- **운영 단순화** — postgres-1 컨테이너 축출 → 12 컨테이너 → 11 컨테이너. FerretDB 의 *wire protocol translation* 오버헤드 제거 (벤치마크 평균 latency 5~15% 감소 예상, 6개월 후 측정)
- **mongodb-operator 패턴 정합** — postgres-operator / valkey-operator 와 동일한 운영 자동화 구조
- **인력 시장 적합성** — MongoDB 인력 풀이 FerretDB 보다 광범위

### 5.2 부정적 영향 / 리스크

- **cut-over 자체의 데이터 손실 위험** — W4.4 의 `verify_collection_parity.py` 가 *모든 도메인 모든 collection* 의 양 DB read parity 검증 후만 cut-over 허용
- **dual-config 단계의 코드 분기** — Wave 4 진행 중 plane 코드에 *ferretdb fallback* 분기 일시 존재 → Wave 4 완료 시 제거
- **postgres-operator 의존 도메인 0건 확인 의무** — 만약 *어느 plane이 postgres direct connection 사용 중* (FerretDB 우회) 이면 본 ADR 영향 받음. 검증 명령: `grep -rn "psycopg\|asyncpg\|postgresql://" core/ planes/ services/` (W4.1 머지 시 필수 실행)
- **rollback 복잡도** — postgres 축출 후 rollback 시 *backup 으로부터 복구* 필요 (RPO 24h 기준 ADR-0009)
- **pymongo asyncio 의 신규 API** — motor 와 *거의 동일* 하지만 *완전 동일은 아님*. plane 코드 마이그레이션 시 thin wrapper 권장

### 5.3 마이그레이션 / 호환성

#### 단계 1 (Wave 4.1 — 본 ADR): Foundation
- 본 ADR 머지 + Status: Accepted
- `grep` 으로 postgres direct connection 도메인 0건 확인

#### 단계 2 (Wave 4.2): MongoDB 인프라 추가 — *dual* 단계
- k8s: `MongoDB` CR (mongodb-operator) 또는 raw Deployment + replica set. `deploy/infra/mongodb-statefulset.yaml` 신규
- docker-compose: `mongodb` service 추가 (image `mongo:7`, host port 27019 — 기존 27018 ferretdb 와 *공존*)
- 시점 외부 publish 포트: 27018 (ferretdb, 보존) + **27019 (mongodb, 신규)**

#### 단계 3 (Wave 4.3): CoreSettings dual-config
- `CoreSettings.mongodb_uri` 신규 (env: `ONEERP_MONGODB_URI`)
- `CoreSettings.ferretdb_uri` *보존* (env: `ONEERP_FERRETDB_URI`)
- plane 코드는 *우선 ferretdb 사용*, 환경변수 `ONEERP_USE_MONGODB=true` 시점 mongodb 사용 (feature flag)
- `@lru_cache + Depends` 패턴 그대로

#### 단계 4 (Wave 4.4): 마이그레이션 도구
- `migrations/tools/mongodump_pipeline.py` — uv 기반 (`uv run`). mongodump (FerretDB) → mongorestore (MongoDB)
- `migrations/tools/verify_collection_parity.py` — read-only 양 DB 비교 (count + sample sha256). pass / fail report
- 첫 도메인 selling PoC

#### 단계 5 (Wave 4.5 — 조건부): 도메인별 cut-over
- 각 도메인 cut-over 절차: ① ferretdb 마지막 snapshot ② mongorestore 적용 ③ `verify_collection_parity.py` PASS ④ `ONEERP_USE_MONGODB=true` (도메인별) ⑤ 1주 dual-read 안정성 관찰 (read 는 mongodb, write 는 양쪽) ⑥ ferretdb 측 write 차단 (read-only) ⑦ 다음 도메인
- 모든 48 도메인 cut-over 완료 후만 postgres+ferretdb 축출

#### 단계 6 (Wave 4 종료): 축출
- `oneerp-ferretdb-1` 컨테이너 + `oneerp-postgres-1` 컨테이너 stop & remove
- `postgres_data` volume → archive (S3 또는 로컬 cold storage) → 30일 후 삭제 (ADR-0009 RPO 30일 정합)
- docker-compose.yml 에서 ferretdb + postgres + seed-data service block 제거
- `CoreSettings.ferretdb_uri` 필드 제거
- 본 ADR Status: Accepted 유지 (실행 완료 markers 는 §6 Action Items 체크)

#### 롤백 가능성 및 절차

| 시점 | 롤백 가능성 | 절차 |
|------|------------|------|
| 단계 2 이전 (W4.1 ADR 머지 후, mongodb 인프라 추가 전) | ✅ 단순 | git revert W4.1 PR |
| 단계 3-4 (dual-config 단계) | ✅ 환경변수 flip | `ONEERP_USE_MONGODB=false` + plane restart |
| 단계 5 (도메인별 cut-over 진행 중) | ⚠️ 도메인 단위 가능 | 해당 도메인 만 `ONEERP_USE_MONGODB=false` + mongodb→ferretdb 역방향 dump (`verify_collection_parity.py` reverse mode) |
| 단계 6 이후 (postgres 축출 후) | ❌ 백업 복구 필요 | postgres archive 에서 복구 (RPO 24h~30일). 모든 도메인 영향. 본 시나리오 *발생 시 INC* 작성 의무 |

### 5.4 측정 지표(Success Metrics)

> 6개월 후 (2026-11-14) 본 ADR 회고 시 평가.

| 지표 | 현재 (2026-05-14) | 목표 | 측정 시점 |
|------|------|------|-----------|
| BE plane 평균 query latency (p50, ms) | (Wave 4 시작 시 baseline 측정) | -5% 또는 변화 없음 | Wave 4 완료 후 1개월 |
| BE plane 평균 query latency (p99, ms) | (baseline) | -10% (FerretDB wire-translation 제거 효과) | 동일 |
| Change Stream 사용 도메인 수 | 0 (FerretDB 미지원) | 1 이상 (realtime-plane 의 portal-core 후보) | Wave 4 완료 후 3개월 |
| 컨테이너 수 (oneerp project) | 12 | 11 | Wave 4 종료 직후 |
| 운영 DB incident 수 (월 평균) | (현재 baseline) | 동일 또는 감소 | Wave 4 완료 후 3개월 |
| MongoDB 인력 채용 가능 시간 | N/A | 평균 < 2주 | 12개월 후 |

## 6. 실행 항목(Action Items)

> ADR 자체는 결정만 기록. 실행은 plan 의 Wave 4 PR 로 위임.

- [ ] (W4.1 본 ADR) — 머지 + Status: Accepted 전환 — 다음 세션
- [ ] (W4.2) — `deploy/infra/mongodb-*.yaml` + `docker-compose.yml` mongodb service 추가 — 다음 세션
- [ ] (W4.3) — `core/oneerp_core/config.py` `CoreSettings.mongodb_uri` 추가 + `@lru_cache + Depends` 팩토리 — 다음 세션
- [ ] (W4.4) — `migrations/tools/mongodump_pipeline.py` + `verify_collection_parity.py` 신규 (uv 기반) — 다음 세션
- [ ] (W4.5) — 도메인별 cut-over (48 도메인) — 별 plan 분할 또는 Wave 4 후속
- [ ] (W4 종료) — postgres + ferretdb 컨테이너 stop & remove + volume archive — 모든 도메인 cut-over 완료 후만
- [ ] (W4 종료) — ADR-0004 Status: `Superseded by ADR-0018` 갱신 — Wave 4 완료 시점
- [ ] (W4 종료) — `docker-compose.yml` ferretdb + postgres + seed-data 블록 제거 + `CoreSettings.ferretdb_uri` 필드 제거 — 동일 시점

## 7. 검증(Verification)

- [ ] **W4.1 직후 검증**: postgres direct connection 도메인 0건 확인 — `grep -rn "psycopg\|asyncpg\|postgresql://" core/ planes/ services/` 결과가 비어 있음 (또는 발견 시 본 ADR §5.2 부정적 영향 갱신 + W4.2 진입 전 처리 plan 별도 작성)
- [ ] **W4.2 직후 검증**: mongodb-operator CR healthy + replica set primary 1 + secondary 2 (or single-node, dev 환경에서). docker-compose `mongodb` healthy. host port 27019 응답.
- [ ] **W4.3 직후 검증**: `uv run python -c "from oneerp_core.config import get_core_settings; s = get_core_settings(); print(s.mongodb_uri, s.ferretdb_uri)"` 양 필드 모두 출력
- [ ] **W4.4 직후 검증**: selling 도메인 PoC `mongodump_pipeline.py` PASS + `verify_collection_parity.py` PASS (count + sample sha256 동일)
- [ ] **W4.5 진행 중 검증**: 각 도메인 cut-over 후 1주 dual-read 동안 *zero 데이터 불일치 alert* (Prometheus mongodb-exporter + ferretdb exporter)
- [ ] **Wave 4 종료 검증**: §5.4 측정 지표 baseline 캡처 후 6개월 회고 일정 등록
- [ ] **회고 일정** — 3개월 (2026-08-14) + 6개월 (2026-11-14) — `docs/governance/adr/INDEX.md` 변경 이력 표에 회고 결과 row 추가

## 8. 참고 자료

### 외부 문헌
- pymongo 공식 문서 — `AsyncMongoClient` API (context7 MCP 조회 2026-05-14, `/mongodb/mongo-python-driver`): `from pymongo import AsyncMongoClient`, async cursor (`async for doc in collection.find(...)`), async session (`async with client.start_session()`)
- MongoDB Server licensing — SSPL (Server-Side Public License) 자체 운영 시 적용 가능 조항
- mongodb-operator (사용자 영역 `public/mongodb-operator` v1.5.0, artifacthub.io published)

### 관련 사내 문서
- 리팩토링 마스터 plan: `~/.claude/plans/woolly-doodling-tarjan.md` Wave 4 섹션
- 본 ADR 의 *parent* ADR: [ADR-0004 데이터베이스 표준 — FerretDB 채택과 출구 조건](./0004-database-standard-ferretdb.md)
- 백업·복구 RPO/RTO: [ADR-0009](./0009-backup-recovery-rpo-rto.md)
- 관찰 가능성 베이스라인: [ADR-0008](./0008-observability-baseline.md)
- 런타임 plane 분해: [ADR-0014](./0014-runtime-plane-decomposition.md)

### 관련 코드 위치
- `core/oneerp_core/config.py:L17-62` (`CoreSettings` 본체, W4.3 변경 대상)
- `planes/_shared/plane_shared/db.py` (예상 위치, dual-config hook)
- `core/` submodule (`keiailab/oneerp-core` 별 GitHub repo, W4.3 변경은 submodule PR 워크플로 의무 — HANDOFF.md 참조)
- `docker-compose.yml` (W4.2)
- `deploy/infra/` (k8s manifest, W4.2 신규)
- `migrations/` + `migrations/README.md` (W4.4 신규 tools/ 추가)

---

## 작성 가이드(체크리스트)

- [x] 제목이 결정 결과를 한 줄로 단정 — "FerretDB 폐기, native MongoDB(k8s) 로 완전 cut-over"
- [x] "현 상태 유지" 대안(D)을 평가
- [x] 측정 지표가 정량 + 6개월 후 검증 가능
- [x] 후속 phase 명시 — Wave 4 (W4.2 ~ W4.5)
- [x] 다른 ADR 관계 메타데이터 기재 (ADR-0004 supersede 후보, ADR-0008/0009/0011/0014 참조)
- [x] 인용 사내 문서 경로 *모두 실제 존재 확인* — `0000-template.md`, `0004-database-standard-ferretdb.md`, `0008-*`, `0009-*`, `0011-*`, `0014-*` 모두 본 PR 의 ADR INDEX 에 등재 (W1.3 갱신)
- [x] 결정 영향 코드 경로 인용 — `core/oneerp_core/config.py`, `planes/_shared/plane_shared/db.py`, `docker-compose.yml`, `deploy/infra/`, `migrations/`
