---
module: gateway
audience: platform-admin tenant-admin dev-support
last_updated: 2026-04-22
spec_version: Commercial Grade v2
---

# gateway 사용자 매뉴얼

> 대상: 플랫폼 관리자 · 테넌트 관리자 · 개발자 지원 팀
> 최종 갱신: 2026-04-22 (Commercial Grade v2 기준)

## 개요

`gateway` 는 OneERP 전 모듈의 공통 진입점(Entry Point)입니다. 모든 API 요청은
gateway 를 통해 라우팅되며, 인증·인가·레이트 리밋·테넌트 헤더 처리·관측성 집계를
단일 지점에서 담당합니다.

일반 최종 사용자는 gateway 를 직접 조작하지 않습니다. **플랫폼 관리자**는 인증
정책·라우팅 규칙·레이트 리밋 정책을 관리하고, **테넌트 관리자**는 자신의 테넌트
범위 내 역할 권한 매트릭스와 감사 로그를 조회합니다.

### 주요 책임 영역

| 영역 | 설명 |
|------|------|
| 인증 (Authentication) | JWT 발급·검증, OIDC 콜백 처리 |
| 인가 (Authorization) | OPA 정책 평가 연계, RBAC 역할 검사 |
| 레이트 리밋 | 테넌트별·엔드포인트별 RPS 제어 (Redis 기반) |
| 테넌트 라우팅 | `X-Tenant-ID` 헤더 기반 업스트림 라우팅, plane 배치 |
| 관측성 집계 | 요청 추적 ID 주입, 감사 이벤트 발행, 메트릭 노출 |
| 장애 격리 | Circuit Breaker, 업스트림 모듈 격리, 캐시 전용 모드 |

### 구성 요소

- **JWT 발급/검증**: `/auth/token`, `/auth/refresh`, `/auth/introspect` 엔드포인트
- **OIDC callback**: `/auth/callback` — 외부 IdP(Keycloak, Okta 등) 연동
- **OPA 정책 평가 연계**: 인가 판정을 OPA 사이드카에 위임
- **테넌트 헤더 처리**: 요청마다 `X-Tenant-ID`, `X-Tenant-Plan` 헤더 자동 삽입
- **감사 이벤트 발행**: 모든 인증·인가 이벤트를 NATS 로 발행 → 감사 서비스 수신
- **관측성**: Prometheus `/metrics`, OpenTelemetry 트레이스 자동 전파

![gateway 아키텍처 개요](assets/gateway/architecture-overview.png)

---

## 시작하기

### 사전 요구사항

- gateway 관리자 권한 (role: `platform-admin`) — MFA 필수
- OneERP 관리 포털(`https://admin.oneerp.example.com`) 접근 가능 네트워크
- 최초 접속 시 OIDC 공급자 계정(Keycloak/Okta) 준비

### 첫 로그인

1. 관리 포털 `https://admin.oneerp.example.com` 접속
2. **OIDC 로그인** 버튼 클릭 → 외부 IdP 로그인 페이지 리디렉션
3. MFA 인증 완료 → gateway 가 JWT 발급 후 포털 리디렉션
4. 대시보드의 **Gateway 카드** 확인 — 활성 테넌트 수·요청 현황·에러율 표시

> **참고**: JWT 는 기본 3600 초(1시간) 유효. 만료 전 포털이 자동 갱신 요청.

![첫 로그인 화면](assets/gateway/first-login.png)

### 기본 탐색 구조

```
관리 포털
└── Gateway
    ├── 테넌트 관리        (/admin/gateway/tenants)
    ├── JWT 서명키 관리    (/admin/gateway/keys)
    ├── 레이트 리밋 규칙   (/admin/gateway/limits)
    ├── 역할 권한 매트릭스 (/admin/gateway/roles)
    └── 감사 로그 뷰어    (/admin/gateway/audit)
```

---

## 주요 화면

### 테넌트 관리 (`/admin/gateway/tenants`)

테넌트별 활성 plane, 라우팅 설정, 상태를 조회·수정합니다.

| 컬럼 | 설명 |
|------|------|
| 테넌트 ID | 시스템 고유 UUID |
| 플랜 등급 | Free / Standard / Enterprise |
| 활성 plane | API / Realtime / Worker / Scheduler / Edge / Extension |
| 상태 | Active / Suspended / Pending |
| 마지막 요청 | 최근 API 호출 시각 |

- **라우팅 토글**: plane 별 활성·비활성 전환. 변경 사항은 30 초 내 전 Pod 전파.
- **테넌트 추가**: 신규 테넌트 UUID 생성 + 플랜 할당 + 초기 역할 구성
- **테넌트 일시정지**: 해당 테넌트 모든 요청 차단 (SLA 위반·보안 사고 시 활용)

![테넌트 관리 화면](assets/gateway/tenants-list.png)

### JWT 서명키 관리 (`/admin/gateway/keys`)

JWT HMAC/RSA 서명 키 수명주기를 관리합니다.

| 필드 | 설명 |
|------|------|
| 키 ID (kid) | 현재 활성 키 식별자 |
| 알고리즘 | RS256 (기본) |
| 생성일 | 키 발급 시각 |
| 만료일 | 유예 기간 포함 만료 |
| 상태 | Active / Retiring / Expired |

- **회전(Rotate)** 버튼: 새 키 발급 → dual-signing → 구 키 유예 기간(기본 24h) → 폐기
- **수동 폐기**: 보안 사고 시 즉각 폐기. 이후 기존 JWT 모두 무효화됨에 주의.
- 회전 드릴 근거: `docs/ops/drills/G4-4/2026-04-21-gateway.md`

![JWT 서명키 관리 화면](assets/gateway/jwt-key-management.png)

### 역할 권한 매트릭스 (`/admin/gateway/roles`)

RBAC 역할별 리소스·액션 허용 여부를 표 형태로 시각화합니다.

- **역할 추가**: 이름·설명·상위 역할(상속) 설정
- **권한 셀 클릭**: Allow / Deny / Inherit 순환 토글
- **변경 감사**: 모든 편집은 `audit.role_changed` 이벤트로 자동 기록
- **역할 삭제**: 해당 역할을 보유한 사용자 수 표시 후 확인 필요

> **권한 요구**: 역할 편집은 `platform-admin` 권한 필요. 조회는 `platform-ops`.

![역할 권한 매트릭스](assets/gateway/role-permissions.png)

### 감사 로그 뷰어 (`/admin/gateway/audit`)

gateway 를 통과한 모든 인증·인가·정책 변경 이벤트를 조회합니다.

- **필터**: 테넌트 ID, 이벤트 유형, 시간 범위, 사용자 ID
- **이벤트 유형**: `auth.login`, `auth.logout`, `auth.token_refresh`, `authz.denied`, `role.changed`, `tenant.suspended`
- **상세 뷰**: 요청 헤더·응답 코드·OPA 평가 결과 JSON 확인
- **다운로드**: CSV / NDJSON 형식으로 최대 10,000 건 내보내기
- **재생(Replay)**: 특정 이벤트 시퀀스를 테스트 환경에서 재실행 (디버깅용)

![감사 로그 뷰어](assets/gateway/audit-log-viewer.png)

### 레이트 리밋 규칙 (`/admin/gateway/limits`)

테넌트별·엔드포인트 패턴별 RPS(초당 요청 수) 및 버스트 한도를 설정합니다.

| 컬럼 | 설명 |
|------|------|
| 패턴 | 경로 Glob (`/api/v*/**`) |
| 기본 RPS | 테넌트 플랜 기준 기본값 |
| 버스트 | 짧은 피크 허용 배수 |
| 현재 도달률 | 실시간 한도 도달 빈도 |

---

## 자주 쓰는 작업

### 신규 테넌트 온보딩

새 고객사를 OneERP 에 등록하는 전체 절차입니다.

1. **테넌트 생성**: `/admin/gateway/tenants` → **추가** 버튼
2. **기본 정보 입력**: 회사명, 플랜 등급, 관리자 이메일
3. **UUID 확인**: 시스템이 자동 생성한 테넌트 ID 기록
4. **plane 활성화**: 계약 플랜에 맞춰 필요한 plane 토글 ON
5. **초기 역할 할당**: 테넌트 관리자 계정에 `tenant-admin` 역할 부여
6. **레이트 리밋 설정**: 플랜별 기본값 확인 후 필요 시 조정
7. **연동 테스트**: 테넌트 관리자 계정으로 로그인 → JWT 발급 확인
8. **온보딩 이메일 발송**: 포털에서 초대 메일 발송 버튼 클릭

**CLI 대안** (자동화 스크립트):
```bash
uv run --package oneerp-gateway --directory services/gateway \
  python -m scripts.onboard_tenant \
  --name "ACME Corp" --plan enterprise --admin-email admin@acme.com
```

### JWT 서명 키 회전

보안 정책에 따라 정기적으로(180 일 권장) 또는 사고 발생 시 즉시 수행합니다.

**UI 절차**:
1. `/admin/gateway/keys` 접속
2. 현재 활성 키 확인
3. **회전** 버튼 클릭 → 확인 다이얼로그
4. 새 키 ID 확인 → `dual-signing` 상태 30 분간 유지
5. 유예 기간 24 시간 후 구 키 자동 폐기

**ESO(External Secrets Operator) 연계**:
```bash
# 비상 키 회전 — ESO 트리거
bash scripts/secrets/rotate-gateway.sh --env prod --force
```

> **주의**: 즉시 폐기(Force Revoke) 선택 시 기존 JWT 전체 무효화. 사용자 재로그인 필요.

### 역할 추가·편집

1. `/admin/gateway/roles` → **역할 추가** 또는 기존 역할 행 클릭
2. **이름**: `kebab-case` 형식 (`finance-viewer`)
3. **상위 역할**: 상속할 기본 역할 선택 (선택 사항)
4. **권한 셀**: 각 리소스·액션 조합별 Allow / Deny 설정
5. **저장**: `audit.role_changed` 이벤트 자동 발행 확인

> **편집 권한**: `platform-admin` 역할 보유자만 저장 가능.

### 레이트 리밋 조정

특정 테넌트의 RPS 임시 상향이 필요한 경우:

1. `/admin/gateway/limits` → 해당 테넌트 행 클릭
2. **RPS** 및 **버스트** 값 수정
3. **적용 범위**: `테넌트 전체` 또는 `특정 엔드포인트 패턴` 선택
4. **만료 시각** 설정 (임시 상향이면 반드시 만료 시각 지정)
5. **저장** — Redis 반영은 10 초 이내

> 기본 상한: 테넌트 RPS 1,000 / 전체 클러스터 40,000 RPS.

### 업스트림 모듈 격리

특정 업스트림 서비스 장애 시 Circuit Breaker 를 수동으로 열어 다른 테넌트 영향을 최소화합니다.

1. `/admin/gateway/tenants` → 해당 업스트림 모듈 선택
2. **격리(Isolate)** 버튼 → Fallback 응답 코드(503) 반환 모드 활성
3. **staging 선행 검증**: 격리 해제 전 `staging` 환경에서 헬스 확인
4. **격리 해제**: 헬스 확인 완료 후 **격리 해제** 버튼

---

## 설정

### 환경 변수 (`ONEERP_GATEWAY_*`)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `ONEERP_GATEWAY_AUTH_MODE` | `live` | `live` \| `cached-only` (directory 장애 시 캐시 전용) |
| `ONEERP_GATEWAY_RATE_LIMIT_RPS` | `1000` | 테넌트 기본 RPS |
| `ONEERP_GATEWAY_RATE_LIMIT_BURST` | `2000` | 버스트 상한 (RPS × 2 기본) |
| `ONEERP_GATEWAY_JWT_TTL_SECONDS` | `3600` | JWT 만료 시간(초) |
| `ONEERP_GATEWAY_JWT_REFRESH_TTL_SECONDS` | `86400` | Refresh 토큰 만료(초) |
| `ONEERP_GATEWAY_OIDC_ISSUER` | `` | OIDC 공급자 Issuer URL |
| `ONEERP_GATEWAY_OPA_ENDPOINT` | `http://opa:8181` | OPA 사이드카 주소 |
| `ONEERP_GATEWAY_AUDIT_NATS_SUBJECT` | `audit.gateway` | 감사 이벤트 NATS 주제 |
| `ONEERP_GATEWAY_CB_THRESHOLD` | `50` | Circuit Breaker 오류율 임계(%) |
| `ONEERP_GATEWAY_CB_TIMEOUT_SECONDS` | `60` | Circuit Breaker 열린 후 재시도 대기(초) |

### Helm Values

환경별 values 파일로 설정을 분리합니다.

| 파일 | 용도 |
|------|------|
| `deploy/charts/gateway/values.yaml` | 기본값 (모든 환경 공통) |
| `deploy/charts/gateway/values-staging.yaml` | 스테이징 오버라이드 |
| `deploy/charts/gateway/values-prod.yaml` | 운영 오버라이드 |
| `deploy/charts/gateway/values-release.yaml` | 릴리즈 후보 |

주요 Helm 설정 항목:

```yaml
gateway:
  replicaCount: 3          # 운영: 최소 3 Pod
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2"
      memory: "1Gi"
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 60
```

### 외부 시크릿 관리 (ESO)

JWT 서명 키와 OIDC 클라이언트 시크릿은 ESO 를 통해 Vault 에서 주입됩니다.

```
deploy/secrets/gateway/externalsecret.yaml
```

OIDC 엔드포인트 변경 시 이 파일의 `oidcIssuer` 값을 수정 후 rollout:
```bash
kubectl rollout restart deployment/gateway -n oneerp
```

---

## 제한사항

### 시스템 한도

| 항목 | 상한 | 비고 |
|------|------|------|
| 테넌트 수 | 1,000 | DB 인덱스 제약. 초과 시 샤딩 필요 |
| 동시 접속 피크 | 30,000 | SLO 기준 99.9% 가용성 |
| JWT 크기 | 4 KB | Claim 과다 시 gateway 가 413 반환 |
| Rate limit 전체 | 40,000 RPS | Redis 1 샤드 기준 |
| 감사 로그 내보내기 | 10,000 건/회 | 대량 추출은 Data Export API 사용 |
| OPA 정책 평가 타임아웃 | 50 ms | 초과 시 기본 Deny 반환 |

### 기능 제한

- **JWT 즉시 폐기**: 현재 Blacklist 방식 미지원. 만료 전 무효화는 강제 키 회전으로만 가능.
- **멀티 리전 동기화**: 레이트 리밋 카운터는 단일 Redis 클러스터 기준. 멀티 리전 시 독립 카운팅.
- **OIDC 공급자**: 동시에 1 개 공급자만 지원. 멀티 IdP 는 Spec III 예정.
- **Webhook 알림**: 레이트 리밋 도달 이벤트 Webhook 미지원 (NATS 이벤트만 제공).

---

## 장애 대응

### 일반 대응 체인

모든 gateway 장애는 다음 순서로 접근합니다.

1. **헬스 체크 확인**: `GET /health` → 200 이 아니면 Pod 재시작 검토
2. **의존성 확인**: Redis (레이트 리밋), directory 서비스 (인증), OPA (인가), NATS (감사)
3. **런북 참조**: `docs/ops/runbook-gateway.md`
4. **드릴 기록**: `docs/ops/drills/G4-{3,4,5}/*-gateway.md`
5. **에스컬레이션**: Primary `@platform-oncall` → Secondary `@iam-ops`

### 증상별 1차 조치

| 증상 | 원인 추정 | 1차 조치 |
|------|----------|----------|
| 401 급증 | JWT 키 회전 미반영 | `kubectl rollout restart deployment/gateway` |
| 5xx on `/auth/token` | directory 모듈 장애 | directory 헬스 확인 → ONEERP_GATEWAY_AUTH_MODE=cached-only 전환 |
| p95 레이턴시 > 500 ms | OPA 또는 업스트림 지연 | OPA 사이드카 CPU 확인 → upstream 추적 |
| Rate limit 오탐 | Redis 연결 불안정 | Redis 연결 상태 확인 → kubectl rollout restart |
| 감사 이벤트 손실 | NATS 연결 끊김 | NATS 클러스터 상태 확인 → gateway 재시작 |
| 테넌트 라우팅 실패 | X-Tenant-ID 누락 | 클라이언트 헤더 설정 확인, gateway 라우팅 규칙 점검 |

### 캐시 전용 모드 (directory 장애 시)

directory 서비스 장애 시 JWT 캐시 기반 인증으로 전환하여 서비스 연속성을 유지합니다.

```bash
# 캐시 전용 모드 활성화
kubectl set env deployment/gateway \
  ONEERP_GATEWAY_AUTH_MODE=cached-only -n oneerp

# 복구 후 정상 모드 복귀
kubectl set env deployment/gateway \
  ONEERP_GATEWAY_AUTH_MODE=live -n oneerp
kubectl rollout restart deployment/gateway -n oneerp
```

> **주의**: 캐시 전용 모드에서는 JWT TTL 내 폐기된 사용자도 접근 가능할 수 있음.

### 에스컬레이션

| 단계 | 담당 | 조건 |
|------|------|------|
| 1차 | `@platform-oncall` | p95 > 500 ms 지속 5 분 이상 |
| 2차 | `@iam-ops` | 인증·인가 관련 장애 |
| 3차 | `@sre-lead` | SLO 위반 (오류율 > 0.1%) |

---

## FAQ

### Q: JWT TTL 을 어떻게 늘리나요?
A: `ONEERP_GATEWAY_JWT_TTL_SECONDS` 환경변수로 조정합니다. 단, 3,600 초(1 시간) 초과 시 보안 검토가 필요하며, 86,400 초(24 시간)를 초과하면 Refresh Token 전략 전환을 권장합니다.

### Q: 테넌트 간 데이터 격리는 어떻게 보장되나요?
A: DB 스키마 단위 격리를 적용합니다. gateway 는 `X-Tenant-ID` 헤더 기반으로 업스트림을 라우팅하며, 잘못된 테넌트 ID 는 gateway 에서 즉시 403 으로 차단합니다.

### Q: OIDC 공급자를 변경할 수 있나요?
A: `deploy/secrets/gateway/externalsecret.yaml` 의 `oidcIssuer` 값을 수정 후 `kubectl rollout restart deployment/gateway` 를 실행합니다. 변경 전 staging 환경에서 반드시 검증하세요.

### Q: 감사 이벤트 보존 기간은 얼마나 되나요?
A: Hot 스토리지 90 일 + Cold 백업 3 년입니다. 상세 정책은 `docs/security/audit-retention-gateway.md` 참조.

### Q: 장애 드릴 주기는?
A: 180 일마다 staging 환경에서 G4-3 / G4-4 / G4-5 드릴을 재실행합니다 (Spec II.5 이후 필수).

### Q: Rate limit 도달 시 사용자에게 어떤 응답이 가나요?
A: HTTP 429 Too Many Requests 와 함께 `Retry-After` 헤더로 재시도 가능 시각을 알립니다. 응답 본문에는 초과한 리밋 값과 현재 카운터가 포함됩니다.

### Q: Circuit Breaker 가 열린 상태는 어디서 확인하나요?
A: `/admin/gateway/tenants` 화면에서 업스트림 모듈 상태 컬럼을 확인합니다. Prometheus 메트릭 `gateway_circuit_breaker_state` 도 활용할 수 있습니다.

### Q: OPA 정책을 직접 수정해도 되나요?
A: `packages/core/opa/policies/` 경로의 `.rego` 파일을 수정 후 PR 을 통해 반영합니다. 정책 변경은 반드시 `opa test` 통과 후 staging 배포 검증이 선행되어야 합니다.

### Q: 멀티 리전 환경에서 레이트 리밋이 공유되나요?
A: 현재는 각 리전의 Redis 클러스터가 독립적으로 카운팅합니다. 글로벌 공유 레이트 리밋은 Spec III 로드맵에 포함되어 있습니다.

---

## 관련 문서

| 문서 | 경로 |
|------|------|
| 운영 런북 | `docs/ops/runbook-gateway.md` |
| 장애 드릴 기록 | `docs/ops/drills/G4-{3,4,5}/*-gateway.md` |
| 튜토리얼 | `docs/tutorials/gateway.md` |
| OPA 정책 | `packages/core/opa/policies/` |
| 시크릿 관리 | `deploy/secrets/gateway/externalsecret.yaml` |
| Helm Charts | `deploy/charts/gateway/` |
| 감사 보존 정책 | `docs/security/audit-retention-gateway.md` |
| Playwright UI 테스트 | `tests/playwright/ui/gateway/` |
| ADR (Commercial v2) | `docs/governance/adr/gateway-commercial-v2.md` |
| 키 회전 스크립트 | `scripts/secrets/rotate-gateway.sh` |
