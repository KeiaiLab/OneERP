# ADR-0004: 데이터베이스 표준 — FerretDB 채택과 출구 조건

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, 데이터 플랫폼 리드 |
| 영향 범위 | 전체 데이터 영속화, 모든 BE 서비스, 백업·복구 운영 |
| 관련 ADR | ADR-0005(멀티테넌시 격리), ADR-0008(관측성), ADR-0009(백업/복구), ADR-0011(plane 분해) |
| 후속 phase | P-004 (FerretDB 호환성 매트릭스), P-005 (출구 모니터링) |

## 1. 맥락(Context)

OneERP는 초기부터 **MongoDB 와이어 호환 + PostgreSQL 백엔드** 조합인
FerretDB v2.7.0을 채택해 왔다. 이는 다음 동기에서 비롯됐다:

- 도메인 모델이 가변 스키마(다국가·산업별 확장 필드)를 요구
- 내부 운영 노하우는 PostgreSQL이 두터움
- MongoDB 라이선스(SSPL) 회피
- 통합 환경에서 `mongo` 클라이언트 도구 활용 가능

그러나 FerretDB는 MongoDB의 부분 호환이며, 일부 집계 연산자, 트랜잭션
의미, 인덱스 옵션, 변경 스트림(change streams) 등에서 차이가 있다.
"호환성을 어디까지 가정해도 되는가"가 명시되지 않으면 모듈이
FerretDB 버그 또는 미지원 기능에 의존하는 사고가 반복된다.

또한 OneERP가 외부 고객 도입 단계에 진입할 때, **언제 FerretDB에서
이탈할 것인가**의 객관 기준이 없으면 운영 한계에 도달한 시점에
비계획 마이그레이션이 강제된다. 이는 데이터 손실/장기 다운타임의
1순위 원인이다.

근거 인벤토리:
- `docs/engineering/data/ferretdb.md` — 현재 사용 현황
- `docs/engineering/data/ferretdb-compat-matrix.md` — 호환성 매트릭스(작성 예정)
- `docs/engineering/data/indexing-strategy.md` — 인덱스 표준
- `docs/infra/inventory/data-storage.md`
- `packages/core/oneerp_core/db.py` — MongoClient 싱글턴
- `docker-compose.yml` — FerretDB v2.7.0 + DocumentDB(Postgres)

## 2. 결정(Decision)

OneERP의 유일한 1차 데이터 저장소는 **FerretDB v2.7.x (PostgreSQL
DocumentDB 백엔드)** 다. 다음 4개 항목을 동시에 결정한다.

1. **표준 채택**: 모든 신규 영속 데이터는 FerretDB에 저장한다.
   직접 PostgreSQL SQL 쿼리는 §6의 예외 외에는 금지.
2. **사용 부분집합**: §5의 화이트리스트 안의 MongoDB API만 사용한다.
   화이트리스트 외 기능 사용 시 PR 차단.
3. **운영 등급 구분**: §7의 데이터 등급(Class A/B/C)에 따라 백업·복제·
   가용성 정책 차등화.
4. **출구 조건(Exit Criteria)**: §8의 트리거 5종 중 하나라도 충족하면
   본 ADR을 supersede하고 마이그레이션 ADR을 신규 작성한다.

- **범위 In**: 모든 트랜잭션·마스터·운영 데이터.
- **범위 Out**:
  - 검색 인덱스 (별도 ADR — Meilisearch/OpenSearch 검토 예정)
  - 시계열/메트릭 (Prometheus, ADR-0008)
  - 객체 스토리지 (S3 호환, 별도 ADR)
  - 캐시 (Redis 등, 별도 ADR)
- **발효 시점**: 즉시.

## 3. 대안(Alternatives Considered)

### 대안 A — 순수 PostgreSQL (관계형)
- 설명: SQLAlchemy + Alembic, 가변 컬럼은 JSONB.
- 장점: 트랜잭션·집계·SQL 도구 풍부, 내부 노하우 일치.
- 단점: 가변 스키마가 JSONB로 흩어져 인덱스/유지보수 비용 상승.
  "MongoDB 호환"이라는 외부 인터페이스가 사라져 일부 도구 단절.
- 채택하지 않은 이유: 출구 ADR로 보존(§8 트리거 충족 시 1순위 후보).

### 대안 B — MongoDB Atlas
- 설명: 정식 MongoDB.
- 장점: 완전 호환, 운영 관리 가용.
- 단점: SSPL 라이선스 부담, 외부 SaaS 의존, 비용.
- 채택하지 않은 이유: 라이선스·의존성 회피.

### 대안 C — CockroachDB / YugabyteDB (분산 SQL)
- 설명: 수평 확장 SQL.
- 장점: 향후 글로벌 확장.
- 단점: 운영 복잡도, 내부 노하우 부족, 가변 스키마 처리는 여전히 JSONB.
- 채택하지 않은 이유: 현 단계 over-engineering.

### 대안 D — DuckDB / SQLite (임베디드)
- 설명: 단일 노드 임베디드.
- 단점: 50K 사용자/100만 트랜잭션 SLO 충족 불가.
- 채택하지 않은 이유: 규모 부적합.

### 대안 E — 현 상태 유지 (문서화 없음)
- 비용: FerretDB 미지원 기능 사용으로 인한 비계획 사고.
- 채택하지 않은 이유: 본 ADR이 그 비용을 제거.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 4/5 | OSS, 내부 PostgreSQL 운영 위에 얹기 |
| 리스크 | 3/5 | 호환성 부분집합·운영 사례 적음 → §5/§8로 완화 |
| 운영 | 4/5 | PostgreSQL 백엔드라 백업/복구 도구 재사용 |
| 팀 역량 | 4/5 | MongoDB API 친숙 + PostgreSQL 운영 친숙 |

- **결정적 근거**: 가변 스키마 친화성 + 라이선스 회피 + PostgreSQL
  백엔드 운영 노하우 재사용.
- **수용한 트레이드오프**: MongoDB 부분 호환의 한계 → §5 화이트리스트로
  제한, §8 출구 조건으로 종료 시점 객관화.

## 5. 사용 화이트리스트 (MongoDB API 부분집합)

다음만 사용 가능. PR은 ruff/biome 사용자 정의 룰 또는 코드 리뷰로
검증.

### 5.1 CRUD
- `insertOne`, `insertMany`
- `find`, `findOne`, 표준 비교/논리 연산자(`$eq`, `$in`, `$gt`, `$and`, `$or`, `$not`, `$exists`)
- `updateOne`, `updateMany` (`$set`, `$unset`, `$inc`, `$push`, `$pull`)
- `deleteOne`, `deleteMany`
- `countDocuments`, `estimatedDocumentCount`
- `aggregate` 단, §5.4 부분집합

### 5.2 인덱스
- 단일 키, 복합 키, 유니크
- TTL 인덱스 (세션·임시 데이터 한정)
- 부분 인덱스 (`partialFilterExpression`)
- **금지**: 텍스트 인덱스(`text`), geo 인덱스 (검색·지리는 별도 ADR)

### 5.3 트랜잭션
- 단일 컬렉션 내 read-modify-write는 `findOneAndUpdate` 사용
- **다중 문서 트랜잭션은 §6 예외 항목에서만**
- 대안: 이벤트 소싱 + outbox 패턴 (모듈별 결정)

### 5.4 집계 연산자
허용: `$match`, `$project`, `$group`, `$sort`, `$limit`, `$skip`,
`$unwind`, `$lookup` (단순), `$count`, `$facet` (소규모)

금지: `$graphLookup`, `$bucketAuto`, `$indexStats`, `$function` (JS),
`$accumulator`, `$merge`, `$out` (FerretDB 미지원/불안정)

리포팅 집계가 위 부분집합으로 표현 불가 시 → §6 예외 또는 캐시 테이블
(materialized view 패턴) 사용.

### 5.5 변경 스트림 (Change Streams)
- **사용 금지**. 이벤트 발신은 outbox 테이블 + 폴러 또는 NATS publish.
- 사유: FerretDB 변경 스트림은 미지원/불안정.

## 6. 직접 SQL 예외

다음 4가지 한정으로 PostgreSQL 직접 SQL 허용. 모듈 README에 사용
사실 및 사유 명시 의무.

1. **장기 보관 분석**: read replica에서 OLAP 쿼리
2. **마이그레이션 스크립트**: `migrations/sql/*.sql`
3. **운영 도구**: 데이터 정합성 점검·복구 스크립트(`scripts/ops/sql/`)
4. **다중 문서 트랜잭션**: 회계 전표·재고 이동 등 ACID 필수 영역
   (도메인 합의로 모듈별 화이트리스트 유지)

직접 SQL 사용은 회귀 테스트 의무화(스키마 변경 시 마이그레이션 + 테스트).

## 7. 데이터 등급과 운영 정책

ADR-0009와 정합. 모듈은 자기 컬렉션을 등급으로 분류한다.

| 등급 | 정의 | 백업 | 복제 | RPO | RTO |
|------|------|------|------|-----|-----|
| A (Critical) | 회계·급여·계약·감사 | 1시간 + WAL 연속 | 동기 2복제 | ≤ 5분 | ≤ 30분 |
| B (Operational) | 판매·구매·재고·HR·CRM | 6시간 + WAL | 비동기 1복제 | ≤ 1시간 | ≤ 2시간 |
| C (Auxiliary) | 캘린더·위키·검색 캐시 | 일 1회 | 없음 | ≤ 24시간 | ≤ 8시간 |

등급은 컬렉션 메타데이터(`__meta.dataClass`)와 모듈 README에 명시.

## 8. 출구 조건 (Exit Criteria)

다음 5개 트리거 중 하나가 발생하면, 본 ADR을 supersede하고
**마이그레이션 ADR을 90일 이내 신규 채택**한다.

### T-1 호환성 한계
- 화이트리스트(§5)로 표현 불가능한 쿼리/집계가 분기 연속 3회 이상
  발생 (인시던트 또는 phase 차단)

### T-2 성능 한계
- ADR-0001 G2-1(API p95 < 200ms) 또는 G2-2(부하 시험) 실패의 근본
  원인이 FerretDB 레이어로 식별된 사례가 분기 2회 이상

### T-3 가용성 한계
- FerretDB 또는 DocumentDB 자체 결함으로 인한 사고가 반기 1회 이상
  (RTO 위반 동반)

### T-4 운영 한계
- 백업/복구 RPO 위반이 반기 1회 이상
- 또는 백엔드 PostgreSQL의 단일 인스턴스 한계(예: 디스크 I/O 포화)에
  도달했고 FerretDB로는 샤딩 불가

### T-5 생태계 변화
- FerretDB 프로젝트 unmaintained 선언 (90일 무릴리즈 + 보안 패치 부재)
- 또는 DocumentDB 라이선스/방향성 변경

출구 트리거 발동 시 후보 목적지: **순수 PostgreSQL(JSONB) → CockroachDB
→ 정식 MongoDB**의 우선순위로 평가한다.

## 9. 영향(Consequences)

### 9.1 긍정적
- 사용 가능한 API를 명시해 미지원 기능 우발 사용 차단.
- 데이터 등급으로 백업·복제 비용을 합리화.
- 출구 조건으로 비계획 마이그레이션 리스크 제거.

### 9.2 부정적
- 화이트리스트가 일부 모듈의 표현력 제한 → §6 예외와 outbox로 완화.
- 등급 분류 작업이 모듈 오너의 신규 부담.

### 9.3 호환성/마이그레이션
- 기존 코드 그대로 유지. 화이트리스트 위반은 점진 식별·교정.
- 출구 시 1차 후보(PostgreSQL JSONB)는 백엔드 동일 → 데이터 손실 없는
  전환 경로 존재.

### 9.4 측정 지표

| 지표 | 현재 | 목표(6개월) |
|------|------|-------------|
| 화이트리스트 위반 PR | n/a | 0건 (자동 차단) |
| 등급 미분류 컬렉션 | n/a | 0건 |
| 출구 트리거 누적 점수 | 0 | 0 (안정 운영) |
| 호환성 매트릭스 항목 검증율 | 0% | 100% |

## 10. 실행 항목

- [ ] 데이터 플랫폼 — `docs/engineering/data/ferretdb-compat-matrix.md` 채움 — 2026-04-30 — phase: P-004
- [ ] 인프라팀 — 화이트리스트 위반 정적 분석 룰(`scripts/lint/db_whitelist.py`) — 2026-05-15
- [ ] 모든 모듈 오너 — 컬렉션 등급 분류 — 2026-04-30
- [ ] 운영팀 — 출구 트리거 모니터링 대시보드 — 2026-05-31 — phase: P-005
- [ ] 운영팀 — 등급별 백업 정책 적용(ADR-0009 연계) — 2026-06-15

## 11. 검증

- [ ] CI에 화이트리스트 룰 활성화
- [ ] 분기 회고에서 출구 트리거 점수 점검
- [ ] 컬렉션 등급 메타데이터 자동 추출 보고서

## 12. 참고 자료

- `docs/engineering/data/ferretdb.md`
- `docs/engineering/data/ferretdb-compat-matrix.md`
- `docs/engineering/data/indexing-strategy.md`
- `docs/infra/inventory/data-storage.md`
- FerretDB: <https://www.ferretdb.com>
- DocumentDB: <https://www.documentdb.com>
- ADR-0001 (성능 게이트), ADR-0009 (백업/복구)
