# 멀티테넌시(초안)

## Phase 0 현황

Phase 0에서는 최소 멀티테넌시 기반을 스텁으로 구현했다. 실제 격리 로직은 Phase 1에서 구현한다.

- **테넌트 추출**: `X-Tenant-Id` 요청 헤더에서 추출 (`packages/core/oneerp_core/tenant.py`)
- **기본값**: 헤더 없으면 `"default"` 테넌트로 처리
- **격리 수준**: 필드 스코프(tenant_id) — 단일 DB 공유 (`packages/core/oneerp_core/db.py`)
- **인증 경계**: 단일 사용자 풀 (`packages/core/oneerp_core/auth.py` — 더미 구현)
- **모델 지원**: `TenantScopedMixin` (`packages/core/oneerp_core/models.py`)

## 결정 포인트(Phase 1 ADR로 확정)

- 테넌트 경계: 고객/법인/사업부 중 무엇인가?
- 격리 수준 확정:
  - DB 분리
  - 컬렉션 분리
  - 필드 스코프(tenant_id) ← Phase 0 기본 선택
- 인증 경계:
  - 테넌트별 사용자 풀 분리 vs 단일 풀
  - OIDC claim으로 tenant 스코프 전달 방식

## 산출물(DoD)

- [x] 멀티테넌시 기본 스텁 구현 (tenant_id 헤더 추출, TenantScopedMixin)
- [ ] 테넌트 경계/격리/운영 모델이 ADR로 확정됨

