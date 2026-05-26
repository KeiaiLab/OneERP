# 공통 라이브러리 분리 기준(초안)

## 공통 커널 후보

- authn/authz (OIDC + RBAC)
- tenant (멀티테넌시 스코프)
- audit-log
- workflow
- notification
- files/storage
- i18n
- reporting primitives

## Phase 0 구현 (`packages/core/oneerp_core/`)

| 모듈 | 파일 | 상태 |
|------|------|------|
| authn/authz | `auth.py` | 스텁 (더미 사용자 반환) |
| tenant | `tenant.py` | 스텁 (X-Tenant-Id 헤더 추출) |
| audit-log | `audit.py` | 스텁 (이벤트 스키마 정의, no-op) |
| db | `db.py` | 구현 (MongoClient 싱글턴) |
| errors | `errors.py` | 구현 (ErrorResponse + OneERPError) |
| models | `models.py` | 구현 (TimestampMixin, TenantScopedMixin) |
| middleware | `middleware.py` | 구현 (RequestIdMiddleware) |

Phase 1 이후 추가 예정: workflow, notification, files/storage, i18n, reporting

## 분리 기준

- 여러 모듈이 공유하는 횡단 관심사
- 보안/감사 요구가 강한 영역
- 변경 시 영향 범위가 넓고 표준화가 필요한 영역

## 산출물(DoD)

- [x] 공통 커널 Phase 0 구현 완료 (7개 모듈)
- [ ] 공통 커널 경계가 ADR로 확정됨

