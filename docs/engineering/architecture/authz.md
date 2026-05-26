# 인증/권한(초안)

## Phase 0 현황

Phase 0에서는 인증/권한/감사의 인터페이스만 스텁으로 구현했다. 실제 로직은 Phase 1에서 구현한다.

- **인증**: `packages/core/oneerp_core/auth.py` — 더미 사용자 반환 (`sub=”dev-user”`)
- **권한**: `CurrentUser(sub, tenant_id, roles)` — 최소 스키마, Phase 1에서 resource_scope/workflow_state 추가
- **감사**: `packages/core/oneerp_core/audit.py` — `AuditEvent` 스키마 정의, `emit_audit_event()` no-op
- **에러 처리**: `packages/core/oneerp_core/errors.py` — `ErrorResponse(error, detail, request_id)`

## 인증(Authentication)

- 1순위: OIDC (확정)
- 후보 IdP: Keycloak (클러스터에 배포 존재) — 실제 issuer/정책은 `docs/infra/inventory/auth-oidc.md`로 확정
- Phase 0: 더미 구현, Phase 1: Keycloak OIDC 연계

## 권한(Authorization)

> ERPNext 수준의 동등성을 위해, “Role/Permission/Workflow state”를 일관되게 모델링한다.

- RBAC: 기본
- ABAC: 예외/조건부 접근(필요 시)
- 권한 결정을 위한 표준 입력:
  - tenant_id
  - user_id
  - roles (from OIDC claims)
  - resource scope (Phase 1)
  - workflow state (Phase 1)

## 감사(Audit)

- 누가/언제/무엇을 변경했는지(필수)
- 민감 데이터 접근 로그(필수)
- Phase 0: no-op 스텁, Phase 1: FerretDB `audit_events` 컬렉션에 저장

## 확인 필요(Phase 1)

- 멀티테넌시(테넌트 경계/분리 수준)
- OIDC 클레임/그룹 매핑(roles 스키마)
- 감사 로그 보존/내보내기 규정

## 산출물(DoD)

- [x] 인증/권한/감사 인터페이스 스텁 구현 완료
- [ ] 권한 모델이 “정책 + 테스트”로 고정됨
- [ ] UI/BE가 동일한 권한 판단 규칙을 공유함

