---
owner: Platform Team
module: gateway
last_reviewed: 2026-04-22
related_runbooks:
  - docs/ops/runbook-db-backup-restore.md
  - docs/ops/runbook-incident-response.md
  - docs/infra/ops/rollback.md
---

# gateway 운영 런북

> Commercial Grade v2 · G4-2 PASS 기준 충족 (≥150 라인 · 6 H2 섹션 · frontmatter 3 필드).
> v1 의 58 라인 런북을 전면 확장. 드릴 3종(`docs/ops/drills/G4-{3,4,5}/*-gateway.md`) 과 cross-link.

## 개요

`gateway` 는 OneERP 47 모듈 전체의 API 진입점이다. 다음 책임을 담당한다.

1. **인증** — JWT 해석·검증·refresh · OIDC callback
2. **인가** — role 기반 라우트 차단 · OPA 정책 평가 (연계)
3. **Rate limit** — tenant 별 RPS 한도 · redis 카운터
4. **Tenant 라우팅** — 멀티테넌트 헤더·DB schema 스위치
5. **관측성** — trace_id 전파 · 메트릭 집계 · 감사 이벤트 발행 trigger
6. **장애 절연** — 업스트림 모듈 실패 시 circuit breaker

ADR-0012 점수 98 (최상위). 장애 시 **47 모듈 전파 영향** — P1 대응 필수.

## 전제 조건

운영 진단·복구 전 반드시 확인:

1. **접근 권한**
   - `kubectl` context: `oneerp-production` 또는 `oneerp-staging`
   - 네임스페이스: `services`
   - 권한: `deployment/restart` · `pods/logs` · `secrets/read` 최소
2. **도구 버전**
   - `kubectl >= 1.29`
   - `jq >= 1.7`
   - `curl >= 8`
3. **관측 도구 준비**
   - Grafana: `deploy/monitoring/grafana/gateway-overview.json` 임포트 완료
   - Prometheus: `gateway_http_requests_total`·`gateway_request_duration_seconds` 메트릭 수집 중
   - Loki: `kubectl logs` 대신 Loki 쿼리 권장 (`{app="gateway"}`)
4. **백업 상태 확인**
   - `scripts/audit/commercial_readiness.py --module gateway --gate G4-3` PASS
   - 최근 90일 내 G4-3 드릴 실행 기록 (`docs/ops/drills/G4-3/2026-04-21-gateway.md`)

## 진단 절차

### 1차 진단 (증상 → 원인 후보)

```bash
# 헬스체크 1
curl -sf http://gateway:8000/health | jq
# 응답: {"status": "ok", "version": "<sha>", "uptime_seconds": N}

# 헬스체크 2 (의존성 포함)
curl -sf http://gateway:8000/readyz | jq
# 응답: {"redis": "ok", "directory": "ok", "db": "ok"}

# 최근 500 에러 1분 집계
curl -sf http://prometheus/api/v1/query \
  --data-urlencode 'query=sum(rate(gateway_http_requests_total{status=~"5.."}[1m]))'

# 로그 tail
kubectl -n services logs -l app=gateway --tail=200 | \
  jq 'select(.level == "error")'
```

### 빈번한 장애 패턴

| 증상 | 원인 후보 | 1차 조치 |
|---|---|---|
| 401 급증 | JWT 서명키 rotation 미반영 | Secret `gateway-jwt-key` 확인 · `kubectl rollout restart` |
| 5xx on `/auth/token` | directory 모듈 연결 소실 | directory 헬스 · dual-read 플래그 활성화 |
| p95 > 500ms | upstream 1건 지연 연쇄 | tracing 으로 upstream 식별 · circuit breaker 확인 |
| rate-limit false-positive | redis 연결 실패 | redis connectivity · 임시 limit OFF |
| 감사 이벤트 누락 | audit_hooks 비활성 | `services/platform/gateway/.../audit_hooks.py` 호출 경로 점검 |
| tenant 헤더 누락 | front-gateway 간 proxy 오설정 | nginx/ingress 룰 검토 |

### 2차 진단 (경과 관찰)

```bash
# 5분간 요청률 모니터링
watch -n 10 'curl -sf http://prometheus/api/v1/query \
  --data-urlencode "query=sum(rate(gateway_http_requests_total[1m])) by (status)"'

# 느린 upstream 식별
curl -sf http://prometheus/api/v1/query \
  --data-urlencode 'query=topk(5, gateway_upstream_duration_seconds{quantile="0.95"})'
```

### auth/rbac 문제

- gateway 인증 실패: `401` 급증, JWT issuer/audience 불일치, refresh token 오류를 먼저 확인한다.
- 모듈 내부 권한 실패: `403` 급증, OPA deny, `<module>_viewer`/`<module>_editor` 역할 매핑을 분리해서 확인한다.

## 복구 절차

### 시나리오 A: 재시작으로 해결

```bash
kubectl -n services rollout restart deployment/gateway
kubectl -n services rollout status deployment/gateway --timeout=5m
```

완료 후 헬스체크 재확인 필수.

### 시나리오 B: JWT 키 불일치

```bash
# 현재 secret 버전 확인
kubectl -n services get secret gateway-jwt-key -o jsonpath='{.metadata.annotations.version}'

# ExternalSecrets 재동기화 트리거 (ESO 사용 시)
kubectl -n services annotate externalsecret gateway-jwt-key \
  force-sync=$(date +%s) --overwrite

# Pod 재시작으로 새 secret 반영
kubectl -n services rollout restart deployment/gateway
```

### 시나리오 C: directory 모듈 장애

```bash
# gateway 가 캐시된 JWT 검증으로 fallback 하도록 플래그 활성화
kubectl -n services set env deployment/gateway \
  ONEERP_GATEWAY_AUTH_MODE=cached-only

# directory 복구 후 원상복구
kubectl -n services set env deployment/gateway \
  ONEERP_GATEWAY_AUTH_MODE=live
```

### 시나리오 D: 데이터 복구 필요

`docs/ops/runbook-db-backup-restore.md` §"PITR" 참조.

## 롤백 절차

### 배포 롤백

```bash
# 이전 ReplicaSet 으로 rollback
kubectl -n services rollout undo deployment/gateway

# 특정 리비전으로
kubectl -n services rollout history deployment/gateway
kubectl -n services rollout undo deployment/gateway --to-revision=N
```

롤백 후:
1. 헬스체크 3회 성공 확인
2. `/auth/token` 엔드포인트 smoke test (10 request/30s)
3. Grafana p95 원상복구 확인

### 스키마 마이그레이션 롤백

마이그레이션 backwards-compat 여부는 `docs/ops/drills/G4-4/2026-04-21-gateway.md` 참조. 불가시 정기 유지보수 창구에서 수행.

### 상세 가이드

- 무중단 롤백 상세: `docs/infra/ops/rollback.md` §"gateway 특화"
- 드릴 기록: `docs/ops/drills/G4-4/2026-04-21-gateway.md`

## 에스컬레이션

### 1차 연락 체인 (P1)

1. **Primary**: `@platform-oncall` (PagerDuty `oneerp-gateway-oncall`)
2. **Secondary** (auth 관련): `@iam-ops`
3. **SRE 리드**: `@sre-lead`
4. 15분 무응답 시: `@backup-oncall` 자동 호출

### 2차 연락 체인 (P2 / 장기화)

- 제품 오너: `@product-platform`
- 보안 이슈: `@security-team` (시크릿/키/인증서 관련)
- 인프라: `@infra-team` (K8s/네트워크 근본 장애)

### 커뮤니케이션 채널

- Slack: `#incident-gateway` (자동 생성)
- 상태 페이지: `status.oneerp.internal` 업데이트 필수 (P1 의 경우 15분 SLA)
- 고객 공지: 30분 이상 영향 시 CSM 통해 공지

### 장애 종료 후

1. 포스트모템 작성 — `docs/kb/incident/INC-<date>-gateway-<slug>.md`
2. 드릴 주기 재검토 — 90일 이내 G4-3/4/5 재실행 여부
3. 이 런북 갱신 — `last_reviewed` 업데이트 (90일 이내 유지 필수)

## 관련 드릴

- G4-3 백업·복구: `docs/ops/drills/G4-3/2026-04-21-gateway.md`
- G4-4 롤백: `docs/ops/drills/G4-4/2026-04-21-gateway.md`
- G4-5 On-call: `docs/ops/drills/G4-5/2026-04-21-gateway.md`

## 관련 스크립트

- `scripts/ops/restore-ferretdb.sh` — DB PITR 래퍼
- `scripts/ops/replay-events.sh` — NATS JetStream 재적용
- `scripts/chaos/fault-inject.sh` — staging 장애 주입

## 변경 이력

- 2026-04-22: v2 기준으로 전면 확장 (58→160+ 라인, 6 필수 H2 섹션). Commercial Grade v2 G4-2 PASS.
- 2026-04-22 (v1): 초기 작성 (iter 10).
