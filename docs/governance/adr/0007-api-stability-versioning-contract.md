# ADR-0007: API 안정성·버전·Deprecation 계약

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, API 플랫폼 리드 |
| 영향 범위 | 모든 외부 노출 BE API, 통합 허브, FE 클라이언트, 외부 SDK |
| 관련 ADR | ADR-0001(G1-2 OpenAPI), ADR-0006(권한), ADR-0008(관측성) |
| 후속 phase | P-010 (버전 라우팅 인프라), P-011 (Deprecation 알림) |

## 1. 맥락(Context)

OneERP는 외부 통합 허브(`erd-integration-hub`), 모바일/웹 클라이언트,
3rd party SaaS, 파트너 SDK가 동일 API를 호출할 것이다. 외부 고객에게
SLA를 약속하려면(ADR-0001) **API 호환성 계약**이 필수다. 현재:

- API 표준 문서는 존재(`docs/engineering/architecture/api-standards.md`)
- 버전 정책 부재
- Deprecation 절차 부재
- breaking change 정의 모호
- OpenAPI 발행은 G1-2 게이트로만 의무화

이 상태에서 모듈마다 임의로 필드를 바꾸면 외부 클라이언트가 깨진다.
한 번 외부에 노출한 API는 **계약**이며, 그 변경 비용은 OneERP가
아니라 외부 클라이언트가 부담한다.

근거 인벤토리:
- `docs/engineering/architecture/api-standards.md`
- `docs/api/README.md`
- ADR-0001 G1-2 (OpenAPI 발행)
- 사례: Stripe API 버전 정책, GitHub REST/GraphQL 정책

## 2. 결정(Decision)

OneERP의 모든 외부 노출 HTTP API는 다음 6개 규칙을 따른다.

### 2.1 버전 라우팅
- URL prefix: `/api/v{N}/...` (예: `/api/v1/sales/invoices`)
- 메이저 버전(N)은 breaking change 시에만 증가
- 마이너/패치는 URL 무영향 (호환 변경)
- 동시 운영 메이저: 최대 2개 (`vN`, `vN-1`)

### 2.2 호환 변경 vs Breaking 변경
**호환(Allowed without bump)**:
- 신규 엔드포인트 추가
- 응답 객체에 신규 필드 추가
- 요청 객체에 옵셔널 필드 추가
- enum에 신규 값 추가 (단, 클라이언트 forward-compat 가이드 발행)
- 비기능 개선 (성능, 메시지 텍스트)

**Breaking (메이저 bump 필수)**:
- 엔드포인트 삭제·이름 변경
- 응답 필드 삭제·타입 변경·필수 여부 변경
- 요청 필수 필드 추가
- enum 값 삭제·의미 변경
- 인증·권한 요구 강화 (Deprecation 경유 필수)
- 에러 코드 의미 변경

### 2.3 Deprecation 절차
- 최소 6개월 사전 공지
- 응답 헤더: `Deprecation: true`, `Sunset: <RFC1123>`,
  `Link: <docs-url>; rel="deprecation"`
- OpenAPI에 `deprecated: true` + `x-sunset` 표기
- 사용량 모니터링 → 마지막 클라이언트 감지 시 sunset 가능
- Sunset 30일 전 마지막 알림 (메일 + 콘솔)

### 2.4 OpenAPI 의무
- 모든 라우트는 OpenAPI 스키마 노출
- 변경 시 `openapi-diff`로 호환성 자동 분류
- breaking 분류 PR은 메이저 bump 또는 deprecation phase 명시 없이 차단
- 발행: `https://api.oneerp.example/openapi/v{N}.json`

### 2.5 안정성 등급
| 등급 | 의미 | 경로 prefix |
|------|------|------------|
| Stable | 본 ADR 전체 적용 | `/api/v{N}/` |
| Beta | 사전 통지 3개월로 단축 가능 | `/api/v{N}-beta/` |
| Experimental | 통지 없이 변경 가능, 외부 권장 X | `/api/v{N}-experimental/` |

승급 절차: Experimental → Beta → Stable. 강등 금지(새 메이저로 분리).

### 2.6 클라이언트 식별
- 모든 요청에 `User-Agent` 또는 `X-Client-Id` 권장
- 권장 미준수 시 deprecation 통지를 직접 받을 수 없음을 응답 헤더로 안내

- **범위 In**: 외부 노출 HTTP API.
- **범위 Out**:
  - 내부 plane 간 RPC (별도 ADR — gRPC/이벤트)
  - 관리자 콘솔 전용 API (Beta 등급으로 시작)
  - 일회성 마이그레이션 엔드포인트

## 3. 대안(Alternatives Considered)

### 대안 A — 무버전 (단일 `/api/`)
- 단점: breaking change가 곧 외부 사고.
- 채택하지 않은 이유: SLA 약속 불가.

### 대안 B — 헤더 버전 (`Accept: application/vnd.oneerp.v1+json`)
- 장점: URL 안정.
- 단점: 캐시·디버깅·문서화 어려움.
- 채택하지 않은 이유: 인지 비용.

### 대안 C — GraphQL 단일 엔드포인트
- 장점: 클라이언트별 필드 선택, 버전 무관.
- 단점: REST 호환 외부 통합 불가, 권한 매트릭스 매핑 복잡.
- 채택하지 않은 이유: 통합 허브 우선, GraphQL은 부가로 별도 ADR.

### 대안 D — 날짜 기반 (Stripe 스타일 `2026-04-13`)
- 장점: 세밀한 계약.
- 단점: 운영 복잡, 다중 버전 동시 유지 부담.
- 채택하지 않은 이유: OneERP 규모에 과대.

### 대안 E — 현 상태 유지
- 채택하지 않은 이유: 외부 도입 차단.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 4/5 | 메이저 2개 동시 운영 = 비용 한계 명시 |
| 리스크 | 5/5 | breaking 자동 차단 |
| 운영 | 4/5 | 사용량 모니터로 sunset 객관 |
| 팀 역량 | 4/5 | URL prefix는 친숙, openapi-diff 학습 필요 |

## 5. 영향(Consequences)

### 5.1 긍정적
- 외부 클라이언트 안정성 보장.
- breaking change PR 사전 차단.
- Deprecation이 객관 지표로 진행.

### 5.2 부정적
- 메이저 2개 동시 운영 비용.
- 변경 자유도 감소 → Beta/Experimental 등급으로 완화.

### 5.3 호환성/마이그레이션
- 현재 라우트는 `/api/v1/`로 명시 이전 (URL 변경 없으면 `/api/v1`로 별칭)
- v0 또는 prefix 없는 라우트는 이전 시 별도 phase

### 5.4 측정 지표

| 지표 | 현재 | 목표(6개월) |
|------|------|-------------|
| breaking PR 자동 차단율 | n/a | 100% |
| Deprecation 6개월 통지 준수율 | n/a | 100% |
| 동시 메이저 수 | 1 | ≤ 2 |
| 클라이언트 식별률 | n/a | ≥ 80% |

## 6. 응답 표준

```json
{
  "data": { ... },          // 또는 "items": [...] + "page": {...}
  "meta": {
    "request_id": "uuid",
    "api_version": "v1",
    "deprecation": null     // 또는 { "sunset": "...", "link": "..." }
  }
}
```

에러:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "human readable",
    "details": [...]
  },
  "meta": { ... }
}
```

오류 코드 카탈로그: `docs/api/error-codes.md` (모듈 횡단)

## 7. 페이징·필터·정렬 표준

- 페이징: `?page[size]=20&page[after]=<cursor>` (cursor 우선)
- 정렬: `?sort=-created_at,name`
- 필터: `?filter[status]=draft&filter[company]=ACME`
- 결과 sparse fieldset: `?fields[invoice]=name,total`

이 표준 미준수 라우트는 G1-2 게이트 fail.

## 8. Deprecation 라이프사이클

```text
[Stable] ──공지── [Deprecated, 6개월] ──Sunset 통지(30일전)── [Sunset]
                          │                                       │
                          ▼                                       ▼
                     사용량 모니터                          410 Gone 응답
```

- 사용량 0 + 90일 경과 → 조기 sunset 가능 (단, 공지는 유지)
- Sunset 후 6개월간 410 응답 + 마이그레이션 가이드 링크
- 그 후 라우트 제거 가능

## 9. 실행 항목

- [ ] API 플랫폼 — 버전 라우터 + `/api/v1/` 정규화 — 2026-05-15 — phase: P-010
- [ ] API 플랫폼 — `openapi-diff` CI 잡 — 2026-05-15
- [ ] API 플랫폼 — Deprecation 헤더 미들웨어 + 사용량 메트릭 — 2026-06-15 — phase: P-011
- [ ] 인프라팀 — 클라이언트 식별 메트릭 대시보드 — 2026-06-30
- [ ] 모든 모듈 오너 — 응답 표준 적용 + 에러 코드 등록

## 10. 검증

- [ ] CI에 OpenAPI breaking 차단 활성
- [ ] 분기마다 deprecation 진행 현황 보고
- [ ] sunset 일자 자동 알림

## 11. 부록 — 호환성 자동 판정 규칙 (요약)

`openapi-diff` 결과 매핑:
| 변경 종류 | 호환? | PR 처리 |
|-----------|-------|---------|
| 신규 path | 호환 | 통과 |
| path 삭제 | breaking | 차단 (메이저 또는 deprecation) |
| 응답 신규 옵션 필드 | 호환 | 통과 |
| 응답 필수 필드 삭제 | breaking | 차단 |
| 요청 신규 옵션 | 호환 | 통과 |
| 요청 신규 필수 | breaking | 차단 |
| enum 추가 | 호환 (forward-compat 가이드 의무) | 경고 |
| enum 삭제 | breaking | 차단 |

## 12. 참고 자료

- `docs/engineering/architecture/api-standards.md`
- Stripe API versioning: <https://stripe.com/docs/api/versioning>
- GitHub API: <https://docs.github.com/en/rest/overview/api-versions>
- IETF RFC 9745 (Deprecation header)
- ADR-0001 G1-2, ADR-0006
