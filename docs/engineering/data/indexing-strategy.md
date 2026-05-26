# 인덱스 전략

## 원칙

- "조회 패턴"에서 출발해 인덱스를 정의한다.
- 인덱스/쿼리 표준은 모듈별로 분산하지 않고 중앙 문서로 고정한다.
- **모든 컬렉션의 첫 번째 인덱스 필드는 반드시 `tenant_id`** — 멀티테넌트 격리의 핵심이다.
- **엔티티 1개 = 컬렉션 1개** — NoSQL 모범사례에 따라 컬렉션별 완전 분리, 격리 최우선.
- 임베딩은 1:소수(변경 빈도가 낮은) 관계에만 허용하고, 1:다 관계는 별도 컬렉션으로 분리한다.

## 데이터 규모 가정

| 항목 | 값 |
|------|-----|
| ERP 사용자 | ~50,000명 |
| 동시 접속(일반) | 10,000명 |
| 동시 접속(피크: 월말/급여) | 30,000명 |
| 일일 트랜잭션 | 1,000,000건+ |
| 연간 문서 증가 | 10억 건 |
| p95 API 응답 | < 200ms |
| p95 리스트 조회 | < 300ms |

## 복합 인덱스 패턴

### 기본 패턴: 테넌트 + 상태 + 시간

모든 리스트 뷰, 대시보드, 필터 조회에 적용되는 기본 패턴:

```javascript
// 패턴 1: 상태별 최신순 조회 (가장 빈번)
{ tenant_id: 1, status: 1, created_at: -1 }

// 패턴 2: 특정 기간 범위 조회 (회계/급여)
{ tenant_id: 1, posting_date: -1, status: 1 }

// 패턴 3: 담당자별 조회
{ tenant_id: 1, owner: 1, status: 1, created_at: -1 }
```

### 유니크 인덱스: 문서 번호 고유성

모든 트랜잭션 문서(견적서, 주문서, 전표 등)에 적용:

```javascript
// 테넌트 내 문서 번호 고유성 보장
{ tenant_id: 1, naming_series: 1 }   // unique: true

// 사업자등록번호 고유성
{ tenant_id: 1, tax_id: 1 }          // unique: true, sparse: true
```

### 텍스트 검색 인덱스

이름/설명 등 자유 텍스트 검색이 필요한 필드:

```javascript
// 고객/공급업체/품목 검색
{ tenant_id: 1, "$**": "text" }       // FerretDB 호환 여부 확인 필요

// 대안: 이름/코드 prefix 검색 (FerretDB 안전)
{ tenant_id: 1, name: 1 }
{ tenant_id: 1, item_code: 1 }
```

### 리스트 뷰 Covered Index

자주 사용되는 필터+정렬 조합을 커버하여 컬렉션 스캔 없이 인덱스만으로 결과를 반환:

```javascript
// 판매 주문 리스트 (필터: status, 정렬: date, 표시: name/total)
{ tenant_id: 1, status: 1, transaction_date: -1, name: 1, grand_total: 1 }

// 재고 조회 (필터: warehouse, 정렬: item)
{ tenant_id: 1, warehouse: 1, item_code: 1, actual_qty: 1 }

// 회계 원장 (필터: account+기간)
{ tenant_id: 1, account: 1, posting_date: -1, debit: 1, credit: 1 }
```

## 컬렉션별 인덱스 매트릭스

| 컬렉션 | 인덱스 | 용도 |
|---------|--------|------|
| sales_order | `{tenant_id, status, transaction_date}` | 주문 리스트 |
| sales_order | `{tenant_id, naming_series}` unique | 문서 번호 |
| sales_order | `{tenant_id, customer, status}` | 고객별 주문 |
| purchase_order | `{tenant_id, status, transaction_date}` | 발주 리스트 |
| purchase_order | `{tenant_id, supplier, status}` | 공급업체별 발주 |
| journal_entry | `{tenant_id, posting_date, status}` | 전표 리스트 |
| journal_entry | `{tenant_id, account, posting_date}` | 계정별 원장 |
| stock_ledger | `{tenant_id, item_code, warehouse, posting_date}` | 재고 원장 |
| employee | `{tenant_id, department, status}` | 직원 리스트 |
| employee | `{tenant_id, employee_id}` unique | 사번 |
| item | `{tenant_id, item_group, name}` | 품목 리스트 |
| item | `{tenant_id, item_code}` unique | 품목 코드 |

## FerretDB 호환성 제약

FerretDB(PostgreSQL 기반 MongoDB 호환 레이어)에서 주의할 사항:

| 기능 | 지원 여부 | 대안 |
|------|----------|------|
| 복합 인덱스 | 지원 | — |
| 유니크 인덱스 | 지원 | — |
| TTL 인덱스 | 미지원 | 배치 삭제 스케줄러 |
| 텍스트 인덱스 ($text) | 부분 지원 | PostgreSQL FTS 또는 prefix 매칭 |
| 와일드카드 인덱스 | 미지원 | 명시적 필드 인덱스 |
| 부분 인덱스 (partialFilterExpression) | 미지원 | 전체 인덱스 + 쿼리 필터 |
| Collation (로케일 정렬) | 미지원 | 애플리케이션 레벨 정렬 |
| Change Streams | 미지원 | PostgreSQL LISTEN/NOTIFY |

> **참고**: FerretDB 버전 업데이트 시 호환성 변경 사항을 반드시 확인한다. 위 표는 FerretDB v1.x 기준이며, 최신 공식 문서를 context7 MCP로 조회하여 갱신한다.

## 인덱스 관리 규칙

1. **인덱스 추가는 코드 리뷰 필수** — 불필요한 인덱스는 쓰기 성능을 저하시킨다.
2. **컬렉션당 인덱스 최대 10개** — 초과 시 쿼리 패턴 재설계를 검토한다.
3. **explain() 기반 검증** — 모든 인덱스는 explain()으로 실제 사용 여부를 확인한다.
4. **미사용 인덱스 월간 점검** — 30일간 사용되지 않은 인덱스는 삭제 후보로 등록한다.

## 산출물(DoD)

- [x] 주요 리스트/리포트 쿼리의 인덱스 커버리지가 정의됨
- [ ] FerretDB 호환성 실측 테스트 완료
- [ ] 통합 테스트에서 인덱스 존재/성능이 검증됨
- [ ] 데이터 10억 건 규모 인덱스 성능 부하 테스트 완료
