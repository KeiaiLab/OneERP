# ADR-0005: 멀티테넌시 격리 등급 정책

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, 보안 리드 |
| 영향 범위 | 전체 데이터 액세스, 인증/인가, 쿼리 레이어, 청구 |
| 관련 ADR | ADR-0001(G3-3 격리), ADR-0004(DB 표준), ADR-0006(권한 모델), ADR-0009(백업) |
| 후속 phase | P-006 (Tier 1 격리 강제), P-007 (Tier 2 승급 절차) |

## 1. 맥락(Context)

OneERP는 SaaS로 다수 고객 테넌트를 호스팅하는 것을 목표로 한다.
현재(`docs/engineering/architecture/multitenancy.md`):

- 테넌트 추출: `X-Tenant-Id` 헤더 → 미설정 시 `"default"` (위험)
- 격리 수준: 필드 스코프(`tenant_id`) — 단일 DB 공유 — Phase 0 스텁
- 인증: 단일 사용자 풀, 더미 구현
- 모델: `TenantScopedMixin`만 존재, 강제력 없음

이 상태로 유료 고객을 받으면 **cross-tenant 데이터 누출**이 1순위
사고 시나리오다. 동시에 모든 고객을 즉시 DB 분리 격리로 운영하면
운영 비용이 폭증한다(50개 고객 × DB 인스턴스).

해법은 **격리 등급(tier)을 명시하고, 등급별 강제 메커니즘과 승급
조건을 정의**하는 것이다. 일반 고객은 강력한 필드 격리(Tier 1),
규제·민감 고객은 스키마 격리(Tier 2), 최고 보안 고객은 DB 격리(Tier 3)로
차등화한다.

근거 인벤토리:
- `docs/engineering/architecture/multitenancy.md`
- `packages/core/oneerp_core/tenant.py`
- `packages/core/oneerp_core/models.py` (`TenantScopedMixin`)
- ADR-0001 G3-3 (멀티테넌시 격리 강제)
- ADR-0004 §6 (PostgreSQL 백엔드의 스키마 분리 가능성)

## 2. 결정(Decision)

OneERP는 **3단 격리 등급(Tier 1/2/3)** 을 제공하고, 고객 계약 시점에
등급을 선택한다. 모든 모듈은 3개 등급 모두에 대해 동작 가능해야 한다.

- **Tier 1 (Shared, 기본)**: 단일 DB·단일 컬렉션 + `tenant_id` 필드 격리
- **Tier 2 (Schema, 옵션)**: 단일 DB · 테넌트별 컬렉션 prefix 또는
  PostgreSQL 스키마 분리
- **Tier 3 (Dedicated, 프리미엄)**: 테넌트별 별도 DB 인스턴스

핵심 결정 사항:

1. **등급 무관 강제**: 모든 쿼리는 리포지토리 레이어에서 `tenant_id`
   필터를 자동 주입한다. 누락 시 런타임 에러 + 감사 로그.
2. **테넌트 컨텍스트 유일 출처**: HTTP 요청은 OIDC 토큰의 `tid` claim에서
   테넌트를 도출한다. 헤더(`X-Tenant-Id`)는 **개발 환경 한정**, 프로덕션
   에서는 거부.
3. **`default` 테넌트 폐지**: 프로덕션에서 테넌트 미해결 요청은 401.
4. **승급 가능성**: Tier 1 → Tier 2 → Tier 3 무중단 승급 절차를 표준화
   (§7).
5. **격리 검증 게이트**: ADR-0001 G3-3은 본 ADR의 cross-tenant 침투
   테스트 슈트 통과를 의미한다.

- **범위 In**: 모든 데이터 액세스 코드, 인증 미들웨어, 청구 엔진.
- **범위 Out**:
  - 인가(권한) 모델 (ADR-0006)
  - 백업 격리 (ADR-0009 Tier별 정책)
  - UI 테넌트 브랜딩 (별도 결정)

## 3. 대안(Alternatives Considered)

### 대안 A — 모든 테넌트 Tier 1 단일
- 장점: 운영 단순.
- 단점: 규제·대형 고객 수용 불가.
- 채택하지 않은 이유: 시장 분기 수용 불능.

### 대안 B — 모든 테넌트 Tier 3 단일 (DB 분리)
- 장점: 격리 확실.
- 단점: 인스턴스 수 폭증, 저비용 고객 수익성 붕괴.
- 채택하지 않은 이유: 비용 구조 비현실.

### 대안 C — RLS(Row-Level Security)에 의존
- 설명: PostgreSQL RLS로 격리.
- 장점: DB 레이어 강제.
- 단점: FerretDB 추상화 우회 필요(§ADR-0004 §6 예외 의존), 디버깅 난해.
- 채택하지 않은 이유: 본 ADR의 리포지토리 강제 + 테스트 슈트가 동등
  보장을 더 단순하게 제공.

### 대안 D — 현 상태 유지 (`default` 테넌트)
- 비용: cross-tenant 사고 1순위.
- 채택하지 않은 이유: 보안.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 4/5 | Tier 1 기본 = 단일 DB로 비용 최소 |
| 리스크 | 5/5 | 등급별 강제 + 침투 테스트로 누출 차단 |
| 운영 | 3/5 | Tier 2/3은 운영 부담 증가 → 청구로 보전 |
| 팀 역량 | 4/5 | 리포지토리 패턴 기반, 학습 부담 낮음 |

## 5. Tier 정의 상세

### 5.1 Tier 1 — Shared (기본)

- **데이터 위치**: 단일 FerretDB DB(`oneerp`) · 모듈별 단일 컬렉션
- **격리 수단**: `tenant_id` 필드 + 자동 필터 + 유니크 인덱스에
  `tenant_id` 포함
- **인증**: 공통 OIDC 발급자 + `tid` claim
- **백업**: 등급 A/B/C 일괄 백업, 복원은 테넌트별 추출 도구
- **적용 대상**: 표준 SMB 고객 (default), 평가판
- **한계**: 컴플라이언스 별도 요구 시 부적합

### 5.2 Tier 2 — Schema (옵션)

- **데이터 위치**: 단일 FerretDB DB · 테넌트별 컬렉션 prefix
  (`t<tid>__<collection>`) 또는 PostgreSQL 스키마 분리
- **격리 수단**: 컬렉션 네이밍 + 리포지토리 자동 라우팅 + 세션별 search_path
- **인증**: 공통 OIDC 또는 테넌트별 IdP federation
- **백업**: 테넌트 단위 부분 백업/복원 가능
- **적용 대상**: 중견·규제 고객
- **추가 비용**: 인덱스 수 증가 → 인스턴스 메모리 +30% 예산

### 5.3 Tier 3 — Dedicated (프리미엄)

- **데이터 위치**: 테넌트 전용 DB 인스턴스 (FerretDB + DocumentDB 클러스터)
- **격리 수단**: DB 인스턴스 분리 + 네트워크 정책 + 별도 keyring
- **인증**: 테넌트 전용 OIDC 또는 SAML federation
- **백업**: 테넌트 전용 백업 일정·보존
- **적용 대상**: 금융·공공·대형 엔터프라이즈
- **운영**: 테넌트당 인스턴스 비용·운영 인건비 청구에 반영

## 6. 강제 메커니즘

### 6.1 리포지토리 레이어 (필수)

- 베이스 클래스 `TenantScopedRepository`가 모든 쿼리에 `tenant_id`를
  자동 주입.
- 우회(`raw=True`) 호출은 `@requires_audit` 데코레이터로 감사 로그 기록.
- 정적 분석: `pymongo.collection.Collection.find` 등의 직접 호출 금지
  (ruff custom rule 또는 import linter).

### 6.2 인증 미들웨어 (필수)

- OIDC `tid` claim → 요청 컨텍스트(`request.state.tenant`) 설정.
- 누락 또는 불일치 시 401 + 알림.
- 헤더 오버라이드는 `ENV != prod` 한정.

### 6.3 침투 테스트 슈트 (G3-3 게이트)

- `tests/security/test_tenant_isolation.py`가 모든 모듈에 대해:
  - 테넌트 A 토큰으로 테넌트 B 리소스 접근 → 403/404
  - 테넌트 A 사용자가 B의 ID를 PATH/BODY로 위조 → 차단
  - 집계/리포트 결과에 cross-tenant 행 0건
- 슈트 통과 없이는 모듈 라벨이 `pre-commercial` 이상으로 승급 불가.

### 6.4 감사 로그 (필수)

- 모든 cross-tenant 시도(차단 포함) 기록 → ADR-0008 표준 로그
- `tenant_id_mismatch` 이벤트는 Critical 알림

## 7. 승급 절차 (Tier 1 → 2 → 3)

### 7.1 Tier 1 → Tier 2

1. 사전 점검: 컬렉션 prefix 또는 스키마 분리 가능 모듈 확인
2. 신규 테넌트 식별자 발급 + 빈 prefix/스키마 생성
3. 데이터 마이그레이션: 기존 `tenant_id` 필터로 추출 → prefix 컬렉션 적재
4. 듀얼 라이트 기간(N일): 새/기존 모두에 기록
5. 검증: 침투 테스트 + 정합성 비교
6. 컷오버: 라우팅 전환
7. 회귀 모니터링 7일 후 기존 데이터 폐기

### 7.2 Tier 2 → Tier 3

1. 신규 DB 인스턴스 프로비저닝 + 네트워크 격리
2. 백업 → 복원으로 초기 데이터 이전
3. 듀얼 라이트 또는 계획 중지(테넌트 동의)
4. 라우팅 전환 + 인증 federation 분리
5. 회귀 모니터링 7일

### 7.3 무중단 보장

- 모든 승급 단계에서 RTO ≤ 5분, 데이터 손실 0건이 목표.
- 실패 시 자동 롤백(이전 라우팅 복귀).

## 8. 영향(Consequences)

### 8.1 긍정적
- cross-tenant 누출 자동 차단.
- Tier 차등으로 시장 분기 모두 수용.
- 승급 절차 표준화로 영업·운영 일관성.

### 8.2 부정적
- Tier 2/3 운영 부담 → 청구 모델로 보전.
- 리포지토리 기반 코드 강제로 직접 쿼리 빌드 일부 금지.

### 8.3 마이그레이션
- 기존 `default` 테넌트 데이터는 마이그레이션 phase에서 식별·이전.
- 헤더 기반 테넌트 추출은 dev 한정으로 제한.

### 8.4 측정 지표

| 지표 | 현재 | 목표(6개월) |
|------|------|-------------|
| `default` 테넌트 사용 요청 | 측정 시작 | 0건 (prod) |
| 리포지토리 우회 호출 | 측정 시작 | 0건 (prod) |
| cross-tenant 시도 차단율 | n/a | 100% |
| Tier 2/3 채택 테넌트 수 | 0 | 사업 목표에 따름 |

## 9. 실행 항목

- [ ] 보안 리드 — `TenantScopedRepository` 베이스 + 강제 적용 — 2026-04-30 — phase: P-006
- [ ] 인프라팀 — 정적 분석 룰(직접 컬렉션 호출 금지) — 2026-05-15
- [ ] 보안 리드 — `tests/security/test_tenant_isolation.py` 모든 모듈 적용 — 2026-05-31
- [ ] 인증팀 — `default` 테넌트 prod 거부 + 헤더 오버라이드 dev 한정 — 2026-04-30
- [ ] 인프라팀 — Tier 2 마이그레이션 도구 — 2026-06-30 — phase: P-007
- [ ] 인프라팀 — Tier 3 프로비저닝 자동화 — 2026-07-31

## 10. 검증

- [ ] CI에 침투 테스트 슈트 통과 의무화
- [ ] 프로덕션 트래픽에서 `tenant_id` 누락 모니터
- [ ] 분기마다 무작위 테넌트 격리 감사

## 11. 부록 A — Tier 결정 트리

```text
고객 요구사항?
├─ 규제 없음, 표준 SaaS → Tier 1
├─ 규제(GDPR/HIPAA/SOX) 또는 백업 분리 요구 → Tier 2
├─ 네트워크/물리 격리 요구 또는 전용 키 관리 → Tier 3
└─ 데이터 주권(특정 리전) → Tier 2 또는 Tier 3 + 리전 라우팅
```

## 12. 부록 B — 청구 시그널

| Tier | 기본 요금 | 추가 |
|------|----------|------|
| 1 | 기본 | 사용량 기반 |
| 2 | 기본 × 1.5 | 백업 보존 옵션 |
| 3 | 기본 × 3+ | 인스턴스 + 네트워크 + 운영 시간 |

(구체 가격은 영업 정책으로 분리)

## 13. 참고 자료

- `docs/engineering/architecture/multitenancy.md`
- `packages/core/oneerp_core/tenant.py`
- `packages/core/oneerp_core/models.py`
- ADR-0001 G3-3
- ADR-0004 §6 (DB 직접 SQL 예외)
- ADR-0006 (권한 모델 — 본 ADR과 함께 cross-tenant 차단 보장)
- OWASP — Multi-tenancy security cheat sheet
