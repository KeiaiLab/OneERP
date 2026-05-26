# 감사로그 스펙(초안)

## 목표

- 누가/언제/무엇을/어떻게 변경했는지 추적 가능해야 한다.
- 멀티테넌시 환경에서 테넌트 경계가 명확해야 한다.

## 최소 이벤트(후보)

- 생성/수정/삭제
- 상태 변경(워크플로우)
- 권한/역할 변경
- 로그인/토큰 발급/권한 오류
- 민감 데이터 접근(조회 포함)

## Phase 0 현황

`packages/core/oneerp_core/audit.py`에 감사 이벤트 스키마를 정의했다.

```python
@dataclass(frozen=True)
class AuditEvent:
    actor: str       # 행위자 ID
    action: str      # 행위 (create/update/delete 등)
    resource: str    # 대상 리소스
    tenant_id: str   # 테넌트
    timestamp: datetime
    details: dict | None  # 추가 정보
```

- **저장소**: Phase 0에서는 no-op (`emit_audit_event()` 호출만 가능)
- **Phase 1**: FerretDB `audit_events` 컬렉션에 저장

## 확인 필요(Phase 1)

- 로그 보존/내보내기(컴플라이언스)
- Observability 연계(로그/트레이싱): `docs/infra/ops/observability.md`
- 구조화된 JSON 로깅 + 중앙 집계

## 책임 구분

- **비즈니스 감사 이벤트 스키마**: 이 문서가 정의한다(누가/무엇을/왜 변경했는지).
- **시스템 로그 구조화**(요청 ID/테넌트/유저/리소스 등 운영 로그): `docs/infra/ops/observability.md`가 정의한다.

## 산출물(DoD)

- [x] 감사 이벤트 스키마 정의 완료 (AuditEvent dataclass)
- [ ] 감사 이벤트 스키마가 ADR로 고정되고 테스트로 검증됨

