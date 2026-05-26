# ADR-0006: RBAC/ABAC 인가 모델과 권한 매트릭스 의무

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, 보안 리드 |
| 영향 범위 | 모든 BE 라우트, FE 화면 가시성, 감사 로깅 |
| 관련 ADR | ADR-0001(G3-1·G3-2 게이트), ADR-0005(테넌트 격리), ADR-0008(감사 로그) |
| 후속 phase | P-008 (인가 코어 구현), P-009 (모듈별 권한 매트릭스) |

## 1. 맥락(Context)

ADR-0001 G3-2는 "권한 매트릭스가 모듈별로 정의되고 권한 누락 라우트가
0건이어야 한다"고 명시한다. 현재(`docs/engineering/architecture/authz.md`):

- `CurrentUser(sub, tenant_id, roles)` 최소 스키마만 존재
- 인가 결정 로직 부재 (Phase 0 더미)
- 권한 모델 미확정 (RBAC vs ABAC 절충 미정)
- workflow state 기반 권한 미구현
- UI/BE 권한 판단 일관성 없음

ERPNext 동등성 목표를 위해서는:
- **역할(Role)**: HR Manager, Accounts User 등 직무 기반
- **리소스 스코프**: Company/Cost Center/Branch 단위 제한
- **워크플로 상태**: Draft/Submitted/Cancelled에 따른 가능 액션
- **필드 레벨 권한**: 일부 필드만 읽기/쓰기
- **공유**: 사용자별 개별 부여

이 모든 차원을 단일 결정 함수로 통합해야 한다.

근거 인벤토리:
- `packages/core/oneerp_core/auth.py`
- `docs/engineering/architecture/authz.md`
- `docs/engineering/data/audit-log-spec.md`
- ERPNext Permission System (참고)

## 2. 결정(Decision)

OneERP는 **RBAC 코어 + ABAC 보강** 의 단일 인가 모델을 채택한다.

- **결정 함수**: `authorize(user, action, resource, context) → Allow/Deny`
- **5개 입력**:
  1. `user`: `tenant_id`, `sub`, `roles`, `groups`, `attributes`
  2. `action`: `read`, `create`, `update`, `delete`, `submit`, `cancel`,
     `amend`, `approve`, `print`, `export`, `share`
  3. `resource`: `module`, `entity`, `record_id?`, `field?`
  4. `context`: `workflow_state?`, `record_attrs`, `time`, `ip?`
  5. `policy`: 모듈별 정책 번들
- **의무**: 모든 모듈은 권한 매트릭스 문서(`docs/governance/permissions/<module>.md`)
  를 발행한다. 라우트와 매트릭스 매핑은 자동 검증.
- **기본 거부**: 명시 허용이 없으면 거부.
- **테넌트 무관 액션 금지**: 모든 결정은 `tenant_id`를 입력으로 받음
  (ADR-0005 강제 유지).
- **UI/BE 일관**: FE는 BE의 결정 함수를 신뢰. UI 가시성은 같은 정책의
  `can(...)` 헬퍼로 판정.
- **감사 의무**: 모든 Deny + 모든 민감 액션(`submit`/`approve`/`export`/
  `share`)은 감사 로그.

- **범위 In**: 모든 BE 라우트, FE 화면, 백그라운드 작업.
- **범위 Out**: 인증(누구인가) — OIDC 별도 결정.

## 3. 대안(Alternatives Considered)

### 대안 A — 순수 RBAC (역할만)
- 단점: 워크플로 상태/회사별 분리 표현 불가.
- 채택하지 않은 이유: ERPNext 동등성 미달.

### 대안 B — 순수 ABAC (속성 정책)
- 단점: 정책 폭증, 설명 가능성 저하, 도메인 전문가 작성 곤란.
- 채택하지 않은 이유: 운영 부담.

### 대안 C — Open Policy Agent(OPA) + Rego
- 장점: 외부 정책 엔진, 표준.
- 단점: 사이드카·네트워크 호출, 도메인 컨텍스트 매번 푸시 필요.
- 채택하지 않은 이유: 본 ADR은 in-process 결정. OPA는 향후
  대규모 정책 분리가 필요할 때 별도 ADR로 검토.

### 대안 D — ERPNext 권한 매트릭스 그대로 차용
- 장점: 사용자 친숙.
- 단점: 라이선스(GPLv3) + 구현 결합 분리 필요.
- 채택하지 않은 이유: 모델은 차용하되 코드/스키마는 OneERP 자체.

### 대안 E — 현 상태 유지
- 채택하지 않은 이유: G3-2 통과 불가.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 4/5 | in-process 결정 = 단순 |
| 리스크 | 5/5 | 기본 거부 + 매트릭스 자동 검증 |
| 운영 | 4/5 | 모듈별 정책 분리 = 변경 격리 |
| 팀 역량 | 4/5 | 역할 기반은 친숙, ABAC 보강은 점진 |

## 5. 모델 상세

### 5.1 역할(Role)
- 시스템 정의: `System Manager`, `Tenant Owner`, `Module Admin`
- 모듈 정의: 각 모듈이 표준 역할 셋 발행 (`docs/governance/permissions/<module>.md`)
  - 예: HR — `HR Manager`, `HR User`, `Employee`
  - 예: Accounting — `Accounts Manager`, `Accounts User`, `Auditor`
- 사용자 정의: 테넌트가 추가 가능

### 5.2 권한 항목(Permission Entry)
모듈 매트릭스의 한 행 = 하나의 권한 항목.

| 컬럼 | 의미 |
|------|------|
| Role | 대상 역할 |
| Entity | 도메인 엔티티 (예: `Sales Invoice`) |
| Action | 액션 (`read` 등 11개) |
| Permission Level | 0~9 (필드 레벨 권한, ERPNext 호환) |
| Conditions | ABAC 조건 (예: `record.company in user.companies`) |
| Sharing | 공유 가능 여부 |

### 5.3 워크플로 권한
- 엔티티별 상태 머신 정의 (`docs/governance/workflows/<module>.md`)
- 상태별 가능 액션 + 가능 역할

예: Sales Invoice
| State | Action | Allowed Role |
|-------|--------|--------------|
| Draft | edit, submit, delete | Accounts User |
| Submitted | print, cancel | Accounts Manager |
| Cancelled | amend | Accounts Manager |

### 5.4 리소스 스코프
- 사용자 속성: `companies[]`, `cost_centers[]`, `branches[]`, `warehouses[]`
- 정책 조건: `record.company in user.companies` 등
- 누락 시 = 모든 스코프 (System Manager 한정)

### 5.5 필드 레벨
- Permission Level: 엔티티 필드에 0~9 부여
- 사용자 역할의 최대 레벨 미만 필드는 hide/readonly

## 6. 결정 함수 인터페이스

```python
# packages/core/oneerp_core/authz.py (예정)

class AuthzDecision:
    allow: bool
    reason: str
    obligations: list[str]  # 예: "audit", "mask:ssn"

def authorize(
    user: CurrentUser,
    action: Action,
    resource: ResourceRef,
    context: AuthzContext | None = None,
) -> AuthzDecision: ...

def can(user, action, resource, context=None) -> bool:
    return authorize(user, action, resource, context).allow
```

FE는 `/api/authz/check` 또는 사전 발급 capability 토큰으로 동일 결과
획득.

## 7. 권한 매트릭스 의무 (G3-2 게이트)

각 모듈은 다음을 발행:

1. `docs/governance/permissions/<module>.md`
   - 표준 역할 목록
   - 엔티티 × 역할 × 액션 매트릭스
   - 워크플로 상태 머신
   - ABAC 조건 카탈로그

2. `services/<svc>/permissions.py`
   - 코드로 표현된 정책
   - 매트릭스와 1:1 매핑

3. `tests/security/test_permissions_<module>.py`
   - 역할 × 액션 조합별 Allow/Deny 케이스
   - 워크플로 상태 전이별 권한 검증
   - cross-tenant 시도 거부

4. **자동 검증**:
   - 모든 BE 라우트가 `@requires(action, entity)` 데코레이터 적용
   - 미적용 라우트는 CI에서 차단
   - 매트릭스에 없는 (역할,액션,엔티티) 조합 호출 시 Deny + 경고

## 8. 영향(Consequences)

### 8.1 긍정적
- 권한 누락 라우트 자동 차단.
- 모듈 정책 분리 → 변경 영향 최소.
- 매트릭스 문서 → 도메인 전문가/감사자 직접 검토 가능.

### 8.2 부정적
- 매트릭스 작성·유지 부담 → 템플릿 + 자동 점검으로 완화.
- 결정 함수 호출 빈도 → 캐시(`@functools.lru_cache` per request) 적용.

### 8.3 호환성
- 기존 더미 인증은 그대로 유지하되 결정 함수 도입과 동시에 교체.

### 8.4 측정 지표

| 지표 | 현재 | 목표(6개월) |
|------|------|-------------|
| `@requires` 미적용 라우트 | 측정 시작 | 0건 |
| 권한 매트릭스 발행 모듈 | 0 | Wave 1+2 모듈 100% |
| 권한 테스트 케이스 | ~0 | ≥ 3000건 |
| 권한 미스매치 인시던트 | n/a | 0건 |

## 9. 실행 항목

- [ ] 보안 리드 — `authorize()` 코어 구현 — 2026-05-15 — phase: P-008
- [ ] 보안 리드 — `@requires` 데코레이터 + 라우트 정적 분석 — 2026-05-31
- [ ] 모든 모듈 오너 — `docs/governance/permissions/<module>.md` 발행 — Wave 진입 시
- [ ] 인프라팀 — `/api/authz/check` 엔드포인트 — 2026-05-31
- [ ] FE팀 — `useCan(action, resource)` 훅 — 2026-06-15

## 10. 검증

- [ ] CI에 라우트 권한 적용 검사
- [ ] 권한 매트릭스 ↔ 코드 정합 자동 비교
- [ ] 분기마다 무작위 권한 침투 테스트

## 11. 부록 — Action 카탈로그

| Action | 의미 | 감사 의무 |
|--------|------|-----------|
| read | 조회 | 민감 엔티티만 |
| create | 신규 | 예 |
| update | 수정 | 예 |
| delete | 삭제 | 예 |
| submit | 제출(워크플로 진입) | 예 |
| cancel | 취소 | 예 |
| amend | 수정본 생성 | 예 |
| approve | 승인 | 예 |
| print | 출력 | 선택 |
| export | 외부 반출 | 예 (Critical) |
| share | 공유 부여 | 예 |

## 12. 참고 자료

- `docs/engineering/architecture/authz.md`
- `packages/core/oneerp_core/auth.py`
- ERPNext Permission System (모델 참고만)
- NIST SP 800-162 ABAC
- ADR-0001 G3-2, ADR-0005 격리
