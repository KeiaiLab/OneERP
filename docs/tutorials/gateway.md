---
module: gateway
level: intermediate
estimated_minutes: 30
audience: platform-admin
last_updated: 2026-04-22
commercial_grade: v2
---

# gateway 튜토리얼 — 신규 테넌트 온보딩

> 대상: 플랫폼 관리자 · 플랫폼 통합 팀
> 소요 시간: 약 30 분 (staging 기준)
> Commercial Grade v2 준수 (T1+T2 증거 포함)

## 시나리오

신규 고객 `Acme Corp` 의 OneERP 테넌트를 gateway 를 통해 온보딩한다.
완료 후 달성 목표:

- 테넌트 DB 스키마 생성 (FerretDB)
- 관리자 사용자 1 명 생성
- 역할 3 종 (`admin`, `manager`, `viewer`) 할당
- 감사 이벤트 4+ 건 기록
- Prometheus 메트릭 카운터 증가 확인

---

## 전제 조건

### 필수 환경

| 항목 | 최솟값 |
|------|--------|
| OneERP 환경 | staging 이상 |
| OIDC 계정 권한 | `platform-admin` |
| 기동 서비스 | `gateway`, `directory`, `accounting` |
| CLI 도구 | `curl`, `jq`, `kubectl` |

### 서비스 상태 확인

```bash
# 필수 서비스 기동 확인
kubectl -n oneerp get deployment gateway directory accounting \
  -o wide --no-headers | awk '{print $1, $2, $3}'
```

예상 출력:

```text
accounting  1/1  running
directory   1/1  running
gateway     1/1  running
```

```bash
# gateway 헬스 엔드포인트 확인
curl -s http://gateway.local/health | jq '{status, version, uptime_seconds}'
```

---

## Step 1 — 로그인 및 관리자 토큰 획득

### 1-1. 플랫폼 관리자 로그인

```bash
ADMIN_TOKEN=$(curl -s -X POST http://gateway.local/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "***",
    "tenant_id": "platform"
  }' | jq -r '.access_token')

echo "admin token 앞 20자: ${ADMIN_TOKEN:0:20}..."
```

> 비밀번호는 환경변수 `ONEERP_ADMIN_PASSWORD` 로 주입하거나 Vault 에서 조회한다.
> 직접 입력 금지.

### 1-2. 토큰 유효성 검증

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://gateway.local/me | jq '{sub, roles, tenant_id, exp}'
```

예상 응답:

```json
{
  "sub": "user@example.com",
  "roles": ["platform.admin"],
  "tenant_id": "platform",
  "exp": 1750000000
}
```

---

## Step 2 — 테넌트 생성

### 2-1. POST /api/v1/admin/tenants

```bash
TENANT_RESP=$(curl -s -X POST http://gateway.local/api/v1/admin/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "subdomain": "acme",
    "plan": "enterprise",
    "locale": "ko-KR",
    "modules": ["selling", "buying", "stock"]
  }')

TENANT_ID=$(echo "$TENANT_RESP" | jq -r '.id')
echo "tenant_id: $TENANT_ID"
```

`subdomain` 규칙: `^[a-z0-9-]{3,32}$`. 생성 후 변경 불가.

### 2-2. 생성 결과 검증

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://gateway.local/api/v1/admin/tenants/$TENANT_ID" \
  | jq '{id, name, subdomain, plan, provisioning_status, created_at}'
```

`provisioning_status` 가 `pending` → `ready` 로 전환되는 것을 다음 단계에서 확인한다.

---

## Step 3 — DB 스키마 프로비저닝 대기

테넌트 생성 직후 백그라운드에서 FerretDB 스키마가 비동기로 생성된다.
일반적으로 1~3 초 소요. 최대 30 초 폴링한다.

```bash
# 프로비저닝 완료 폴링 (30초 타임아웃)
for i in $(seq 1 30); do
  STATUS=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "http://gateway.local/api/v1/admin/tenants/$TENANT_ID" \
    | jq -r '.provisioning_status')
  printf "[%02d] provisioning_status: %s\n" "$i" "$STATUS"
  [ "$STATUS" = "ready" ] && echo "프로비저닝 완료!" && break
  [ "$STATUS" = "failed" ] && echo "프로비저닝 실패 — 트러블슈팅 참조" && exit 1
  sleep 1
done
```

`ready` 상태 확인 전까지 역할·초대 API 를 호출하지 않는다.

---

## Step 4 — 역할 3 종 설정

역할(`admin`, `manager`, `viewer`)을 순서대로 생성한다.
각 역할에는 permissions 배열로 세부 권한을 부여한다.

### 4-1. admin 역할

```bash
curl -s -X POST \
  "http://gateway.local/api/v1/admin/tenants/$TENANT_ID/roles" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "admin",
    "display_name": "테넌트 관리자",
    "permissions": ["tenant.admin", "module.all", "audit.read"]
  }' | jq '{id, name, permissions}'
```

### 4-2. manager 역할

```bash
curl -s -X POST \
  "http://gateway.local/api/v1/admin/tenants/$TENANT_ID/roles" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "manager",
    "display_name": "매니저",
    "permissions": ["module.write", "module.read", "audit.read"]
  }' | jq '{id, name, permissions}'
```

### 4-3. viewer 역할

```bash
curl -s -X POST \
  "http://gateway.local/api/v1/admin/tenants/$TENANT_ID/roles" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "viewer",
    "display_name": "뷰어 (읽기 전용)",
    "permissions": ["module.read"]
  }' | jq '{id, name, permissions}'
```

### 4-4. 역할 목록 검증

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://gateway.local/api/v1/admin/tenants/$TENANT_ID/roles" \
  | jq '[.[] | {name, permissions}]'
```

예상: 3 개 역할 (`admin`, `manager`, `viewer`) 목록 반환.

---

## Step 5 — 첫 관리자 사용자 초대

테넌트 `admin` 역할로 초대 이메일을 발송한다.
초대 링크는 72 시간 유효하다.

```bash
INVITE_RESP=$(curl -s -X POST \
  "http://gateway.local/api/v1/admin/tenants/$TENANT_ID/invitations" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.example.com",
    "role": "admin",
    "expires_in_hours": 72,
    "send_welcome_email": true
  }')

INVITE_ID=$(echo "$INVITE_RESP" | jq -r '.id')
echo "초대 ID: $INVITE_ID"
echo "초대 링크 만료: $(echo "$INVITE_RESP" | jq -r '.expires_at')"
```

---

## Step 6 — 감사 이벤트 확인

테넌트 생성 이후 발행된 감사 이벤트를 조회한다.
최소 4 건이 기록되어야 한다.

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://gateway.local/api/v1/admin/audit-events?entity_type=tenant&entity_id=$TENANT_ID" \
  | jq '.events[] | {action, actor_email, created_at}'
```

예상 이벤트 목록:

| 순서 | 이벤트 | 트리거 |
|------|--------|--------|
| 1 | `tenant.created` | Step 2 POST |
| 2 | `tenant.provisioned` | Step 3 완료 |
| 3 | `tenant.role.created` × 3 | Step 4 × 3 |
| 4 | `tenant.invitation.sent` | Step 5 POST |

```bash
# 이벤트 건수 확인 (최소 5건 이상)
EVENT_COUNT=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://gateway.local/api/v1/admin/audit-events?entity_type=tenant&entity_id=$TENANT_ID" \
  | jq '.total')
echo "감사 이벤트 건수: $EVENT_COUNT"
[ "$EVENT_COUNT" -ge 5 ] && echo "PASS" || echo "FAIL — 이벤트 부족"
```

---

## Step 7 — Prometheus 메트릭 확인 (T2 증거)

```bash
# gateway 요청 카운터 — 새 테넌트 트래픽 확인
curl -s http://gateway.local:9090/metrics \
  | grep "gateway_http_requests_total" \
  | grep "tenant_id=\"$TENANT_ID\""
```

예상 출력:

```text
gateway_http_requests_total{method="POST",route="/api/v1/admin/tenants",status="201",tenant_id="acme"} 1
gateway_http_requests_total{method="POST",route="/api/v1/admin/tenants/.*/roles",status="201",tenant_id="acme"} 3
gateway_http_requests_total{method="POST",route="/api/v1/admin/tenants/.*/invitations",status="201",tenant_id="acme"} 1
```

---

## Step 8 — 회수·롤백 (실패 시)

### 8-1. 테넌트 일시 정지

프로비저닝 실패 또는 이상 징후 발생 시:

```bash
curl -s -X POST \
  "http://gateway.local/api/v1/admin/tenants/$TENANT_ID/suspend" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '{id, status, suspended_at}'
```

### 8-2. 삭제 (비가역 — 드라이런 필수)

```bash
# 반드시 dry_run=true 로 먼저 확인
curl -s -X DELETE \
  "http://gateway.local/api/v1/admin/tenants/$TENANT_ID?dry_run=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '{would_delete, affected_resources}'
```

`would_delete: true` 와 영향 리소스 확인 후, 실제 삭제는 별도 승인 절차를 따른다.

---

## 검증 체크리스트

온보딩 완료 기준 (DoD):

- [ ] `GET /me` 응답에 새 테넌트 멤버십 포함
- [ ] `GET /api/v1/admin/tenants/$TENANT_ID/roles` 에 3 종 역할 존재
- [ ] 감사 이벤트 5+ 건 기록 확인
- [ ] `provisioning_status: ready` 확인
- [ ] 초대 이메일 발송 완료 (`invitation.sent` 이벤트)
- [ ] Prometheus `gateway_http_requests_total{tenant_id="acme"}` 카운터 증가
- [ ] Grafana `gateway-overview` 대시보드에서 해당 테넌트 트래픽 표시

---

## 트러블슈팅

### 401 Unauthorized on /auth/login

원인: JWT 서명 키 rotation 미반영.

```bash
kubectl -n oneerp rollout restart deployment/gateway
kubectl -n oneerp rollout status deployment/gateway
```

### 422 Unprocessable Entity on POST /tenants

- `name`, `subdomain` 필드 누락 확인
- `subdomain` 패턴 위반: `^[a-z0-9-]{3,32}$`
- `plan` 값: `starter` | `professional` | `enterprise` 만 허용

### provisioning_status: failed

FerretDB 연결 또는 스키마 migration 실패.

```bash
# gateway 파드 로그 확인
kubectl -n oneerp logs deployment/gateway --since=5m \
  | grep -E "ERROR|provisioning|tenant_id=$TENANT_ID"
```

`docs/ops/runbook-gateway.md` §"복구 절차" 참조.

### 감사 이벤트 누락

- `audit_hooks.py` 호출 누락 → `G3-4` 게이트 확인
- 3 개월 보존 정책 초과 → `docs/security/audit-retention-gateway.md` 참조

### rate limit 미반영

새 역할 생성 후 Redis 캐시 분배 지연 (최대 30 초).

```bash
# Redis 캐시 강제 무효화
kubectl -n oneerp exec deployment/gateway -- \
  python -c "from app.cache import invalidate_tenant; invalidate_tenant('$TENANT_ID')"
```

---

## 다음 튜토리얼

- 테넌트별 역할 권한 매트릭스 편집
- JWT 서명 키 회전 (staging 드릴 포함)
- SSO provider 등록 (`directory` 튜토리얼)
- 멀티 리전 배포 설정

---

## 관련 문서

| 문서 유형 | 경로 |
|-----------|------|
| 매뉴얼 | `docs/user-manual/gateway.md` |
| 런북 | `docs/ops/runbook-gateway.md` |
| API 예시 | `docs/api/gateway/examples/` |
| ADR | `docs/governance/adr/gateway-commercial-v2.md` |
| 감사 보존 정책 | `docs/security/audit-retention-gateway.md` |

---

*Commercial Grade v2 · T1+T2 검증 완료 · last_updated: 2026-04-22*
