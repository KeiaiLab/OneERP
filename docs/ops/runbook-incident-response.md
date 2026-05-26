# 장애 대응 Runbook

## 심각도 분류

### P1 (Critical) — 전체 서비스 중단

- **정의**: 운영 환경의 전체 또는 다수 서비스가 동시에 불가용
- **예시**: DB 클러스터 전체 장애, 네트워크 단절, Ingress Controller 장애
- **SLO 영향**: 가용성 99.9% 에러 버짓 급속 소진 (월간 허용 43분)
- **대응 시간**: 감지 후 15분 이내 대응팀 소집
- **최대 해결 시간**: 1시간

### P2 (Major) — 핵심 기능 장애

- **정의**: 단일 서비스 또는 핵심 비즈니스 플로우 장애
- **예시**: 판매/구매 API 응답 불가, 인증(Keycloak) 장애, 특정 서비스 OOM
- **SLO 영향**: 해당 서비스의 에러율 SLO 위반
- **대응 시간**: 감지 후 30분 이내 담당자 확인
- **최대 해결 시간**: 4시간

### P3 (Minor) — 부분 기능 저하

- **정의**: 비핵심 기능 장애 또는 성능 저하
- **예시**: p95 지연 200ms 초과, 특정 API 간헐적 오류, 리포트 생성 지연
- **SLO 영향**: 경고 수준, 에러 버짓 소진 50% 미만
- **대응 시간**: 다음 영업일 내 확인
- **최대 해결 시간**: 1영업일

### P4 (Low) — 관찰 필요

- **정의**: 사용자에게 직접 영향 없으나 잠재적 리스크
- **예시**: Pod 재시작 횟수 증가, 디스크 사용량 경고, 비정상 로그 패턴
- **SLO 영향**: 없음 (예방적 조치)
- **대응 시간**: 주간 점검 시 확인
- **최대 해결 시간**: 1주

## 대응 절차

### 1. 감지 — 알림/모니터링

**자동 감지 (Phase 2 구축 후)**

```
Prometheus 알림 규칙 → Alertmanager → Slack #oneerp-alerts
                                    → PagerDuty (P1/P2)
```

**현재 (Phase 1 — 수동 감지)**

```bash
NS=services

# 전체 Pod 상태 요약
kubectl -n $NS get pods -o wide

# 최근 이벤트 (경고/에러)
kubectl -n $NS get events --sort-by='.lastTimestamp' \
  --field-selector type!=Normal | tail -20

# 서비스 엔드포인트 일괄 헬스체크
API_HOST=${ONEERP_API_HOST}
for SVC in "" selling buying stock accounting; do
  PATH_PREFIX=${SVC:+/$SVC}
  HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" \
    --max-time 5 https://$API_HOST${PATH_PREFIX}/healthz 2>/dev/null)
  echo "$SVC: $HTTP_CODE"
done

# Web 프론트엔드 응답 확인
curl -sf -o /dev/null -w "web: %{http_code}\n" --max-time 5 https://${ONEERP_API_HOST}/
```

### 2. 분류 — 심각도 판정

장애 감지 후 아래 기준으로 심각도를 판정한다.

| 질문 | Yes → 심각도 |
|------|-------------|
| 전체 사용자가 서비스를 이용할 수 없는가? | P1 |
| 핵심 비즈니스 플로우(판매/구매/회계)가 불가한가? | P2 |
| 사용자의 일부 작업이 느리거나 실패하는가? | P3 |
| 사용자에게 직접 영향이 없으나 이상 징후가 보이는가? | P4 |

### 3. 대응팀 소집

**P1/P2**: 즉시 소집

```
1. Slack #oneerp-incidents 채널에 장애 알림 게시
2. 담당자 호출 (PagerDuty 또는 직접 연락)
3. 전용 Slack 스레드 생성하여 실시간 상황 공유
```

**소집 대상**

| 역할 | P1 | P2 | P3 | P4 |
|------|----|----|----|----|
| 인프라 관리자 | 필수 | 상황별 | - | - |
| 서비스 개발자 | 필수 | 필수 | 필수 | - |
| DB 관리자 | 상황별 | 상황별 | - | - |
| 프로젝트 리드 | 필수 | 알림 | - | - |

### 4. 원인 분석

**단계적 진단 절차**

```bash
NS=services

# ── 1단계: 인프라 수준 ──
# 노드 상태
kubectl get nodes -o wide

# 네임스페이스 내 전체 리소스 상태
kubectl -n $NS get all

# 리소스 사용량 (노드/Pod)
kubectl top nodes
kubectl -n $NS top pods

# ── 2단계: 서비스 수준 ──
# 문제 서비스의 Pod 로그 (최근 100줄)
SERVICE=gateway  # 문제 서비스로 변경
kubectl -n $NS logs deployment/$SERVICE --tail=100

# Pod 이벤트
kubectl -n $NS describe deployment/$SERVICE

# ── 3단계: 데이터 수준 ──
# FerretDB 상태
kubectl -n $NS logs deployment/ferretdb --tail=50

# PostgreSQL 상태
kubectl -n $NS describe clusters.postgresql.cnpg.io oneerp-db

# ── 4단계: 네트워크 수준 ──
# Ingress 상태
kubectl -n $NS get ingress
kubectl -n $NS describe ingress

# 서비스 엔드포인트 확인 (백엔드 Pod 연결 여부)
kubectl -n $NS get endpoints
```

### 5. 조치 (롤백/핫픽스/스케일링)

장애 유형에 따라 적절한 조치를 선택한다.

**조치 A: 서비스 롤백**

```bash
# 상세 절차: docs/ops/runbook-service-deploy.md "롤백 절차" 참조
argocd app rollback oneerp-gateway <REVISION_NUMBER>
```

**조치 B: 핫픽스 배포**

```bash
# 1. 핫픽스 브랜치에서 수정
# 2. CI 빌드 후 이미지 태그 확인
# 3. 수동 배포 (ArgoCD 또는 kubectl)
NS=services
kubectl -n $NS set image deployment/gateway \
  gateway=ghcr.io/oneerp/gateway:<HOTFIX_TAG>
```

**조치 C: 수평 스케일링**

```bash
NS=services
SERVICE=gateway

# 현재 replica 수 확인
kubectl -n $NS get deployment $SERVICE

# replica 증가
kubectl -n $NS scale deployment $SERVICE --replicas=5

# 스케일링 완료 확인
kubectl -n $NS rollout status deployment/$SERVICE
```

**조치 D: Pod 재시작**

```bash
NS=services
SERVICE=gateway

# 전체 Pod 롤링 재시작
kubectl -n $NS rollout restart deployment/$SERVICE

# 특정 Pod만 삭제 (ReplicaSet이 자동 재생성)
kubectl -n $NS delete pod <POD_NAME>
```

**조치 E: DB Failover 강제 실행**

```bash
NS=services

# CNPG Switchover (계획된 Primary 전환)
kubectl -n $NS cnpg promote oneerp-db <TARGET_INSTANCE>

# 또는 kubectl 플러그인 없이
kubectl -n $NS annotate clusters.postgresql.cnpg.io oneerp-db \
  cnpg.io/switchoverTarget=<TARGET_INSTANCE>
```

### 6. 검증

조치 후 서비스가 정상 복구되었는지 검증한다.

```bash
NS=services

# Pod 상태 확인 (모두 Running/Ready)
kubectl -n $NS get pods -l app.kubernetes.io/part-of=oneerp

# 헬스체크 (전체 서비스)
API_HOST=${ONEERP_API_HOST}
for SVC in "" selling buying stock accounting; do
  PATH_PREFIX=${SVC:+/$SVC}
  HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" \
    --max-time 5 https://$API_HOST${PATH_PREFIX}/healthz 2>/dev/null)
  echo "$SVC: $HTTP_CODE"
done

# 최근 에러 로그 없는지 확인
for SVC in gateway selling buying stock accounting; do
  echo "=== $SVC ==="
  kubectl -n $NS logs deployment/$SVC --since=5m | grep -ic "error\|exception\|traceback"
done

# Pod 재시작 횟수 확인 (증가하지 않아야 함)
kubectl -n $NS get pods -o custom-columns=\
NAME:.metadata.name,\
RESTARTS:.status.containerStatuses[0].restartCount,\
STATUS:.status.phase
```

### 7. 포스트모템

P1/P2 장애는 해결 후 3영업일 이내에 포스트모템을 작성한다.

## 시나리오별 대응

### DB 연결 불가

**증상**: 서비스 로그에 `Connection refused`, `timeout` 등 DB 연결 오류 발생

```bash
NS=services

# FerretDB Pod 상태 확인
kubectl -n $NS get pods -l app=ferretdb

# FerretDB 로그 확인
kubectl -n $NS logs deployment/ferretdb --tail=50

# PostgreSQL 클러스터 상태 확인
kubectl -n $NS get clusters.postgresql.cnpg.io oneerp-db

# PostgreSQL Primary Pod 상태 확인
kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db

# PostgreSQL 연결 테스트
PRIMARY_POD=$(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n $NS exec $PRIMARY_POD -- psql -U postgres -c "SELECT 1;"

# FerretDB → PostgreSQL 연결 확인
kubectl -n $NS exec deployment/ferretdb -- \
  wget -q -O- http://localhost:8080/debug/connz 2>/dev/null || echo "디버그 엔드포인트 없음"
```

**조치 순서**:
1. PostgreSQL Primary가 Running인지 확인 → 아니면 CNPG 자동 failover 대기
2. FerretDB가 Running인지 확인 → 아니면 Pod 재시작
3. 네트워크 정책 확인 → FerretDB에서 PostgreSQL 서비스로의 접근이 허용되어 있는지
4. 서비스 환경변수 `ONEERP_FERRETDB_URI` 값이 올바른지 확인

### 서비스 OOM

**증상**: Pod가 OOMKilled로 반복 재시작, `kubectl describe`에서 `Reason: OOMKilled` 확인

```bash
NS=services
SERVICE=gateway

# OOM 여부 확인
kubectl -n $NS get pods -l app=$SERVICE -o jsonpath=\
'{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].lastState.terminated.reason}{"\n"}{end}'

# 현재 메모리 사용량
kubectl -n $NS top pods -l app=$SERVICE

# 메모리 limits 확인
kubectl -n $NS get deployment $SERVICE -o jsonpath=\
'{.spec.template.spec.containers[0].resources.limits.memory}'
```

**조치**:
1. **즉시**: 메모리 limits 증가 (Helm values 수정 후 배포)
2. **단기**: 애플리케이션 메모리 프로파일링으로 누수 원인 파악
3. **장기**: 메모리 사용 패턴 기반 적정 limits 재설정

```bash
# 긴급 메모리 증가 (예: 256Mi → 512Mi)
NS=services
SERVICE=gateway
kubectl -n $NS patch deployment $SERVICE --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"512Mi"}]'
```

### 인증 장애 (Keycloak)

**증상**: 모든 API 요청이 401/403 반환, 사용자 로그인 불가

```bash
NS=services

# Keycloak Pod 상태 확인 (platform 네임스페이스)
kubectl -n platform get pods -l app=keycloak

# Keycloak 로그 확인
kubectl -n platform logs deployment/keycloak --tail=100

# Keycloak 엔드포인트 접근 확인
curl -sf -o /dev/null -w "%{http_code}" ${ONEERP_OIDC_ISSUER}/realms/oneerp/.well-known/openid-configuration

# 서비스의 OIDC 설정 확인
kubectl -n $NS exec deployment/gateway -- env | grep -i "ONEERP.*OIDC\|ONEERP.*KEYCLOAK\|ONEERP.*AUTH"
```

**조치**:
1. Keycloak Pod 재시작: `kubectl -n platform rollout restart deployment/keycloak`
2. Keycloak DB 연결 확인
3. OIDC discovery URL 응답 확인
4. 인증서 만료 확인 (TLS): `docs/ops/runbook-certificate-renewal.md` 참조
5. 최후 수단: 서비스의 인증 미들웨어 임시 우회 (주의: 보안 리스크)

### 높은 지연 (p95 > 200ms)

**증상**: API 응답 시간이 SLO 기준(p95 < 200ms)을 초과

```bash
NS=services

# Pod 리소스 사용량 확인
kubectl -n $NS top pods

# 노드 리소스 확인
kubectl top nodes

# DB 슬로우 쿼리 확인
PRIMARY_POD=$(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n $NS exec $PRIMARY_POD -- psql -U postgres -d ferretdb \
  -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query
      FROM pg_stat_activity
      WHERE state != 'idle' AND now() - pg_stat_activity.query_start > interval '1 second'
      ORDER BY duration DESC LIMIT 10;"

# 활성 연결 수 확인
kubectl -n $NS exec $PRIMARY_POD -- psql -U postgres -d ferretdb \
  -c "SELECT count(*) as total, state FROM pg_stat_activity GROUP BY state;"

# 서비스 로그에서 느린 요청 패턴 확인
kubectl -n $NS logs deployment/gateway --tail=200 | grep -i "slow\|timeout\|latency"
```

**조치**:
1. **CPU/메모리 병목**: Pod 수평 스케일링 (`kubectl scale`)
2. **DB 병목**: 슬로우 쿼리 최적화, 연결 풀 크기 조정
3. **네트워크 병목**: Ingress 로그 확인, 외부 호출 타임아웃 확인
4. **일시적 부하**: HPA(Horizontal Pod Autoscaler) 설정 확인

### 데이터 불일치

**증상**: 비즈니스 데이터가 서비스 간 불일치 (예: 판매 주문과 재고가 맞지 않음)

```bash
NS=services

# 서비스별 최근 에러 로그 확인
for SVC in selling stock accounting; do
  echo "=== $SVC ==="
  kubectl -n $NS logs deployment/$SVC --since=1h | grep -i "error\|conflict\|integrity"
done

# FerretDB에서 직접 데이터 확인 (예: 특정 주문)
kubectl -n $NS port-forward svc/ferretdb 27017:27017 &
mongosh "mongodb://localhost:27017/oneerp" --eval '
  // 문제가 되는 문서 ID로 조회
  db.sales_orders.findOne({_id: ObjectId("...")})
'
```

**조치**:
1. 관련 서비스의 이벤트/로그를 시간순으로 추적
2. 데이터 정합성 보정 스크립트 작성 (스테이징에서 검증 후 운영 적용)
3. 필요 시 PITR로 특정 시점 데이터 확인: `docs/ops/runbook-db-backup-restore.md` 참조
4. 포스트모템에서 근본 원인 분석 (이벤트 순서, 동시성 이슈 등)

## 커뮤니케이션 템플릿

### 초기 알림

```
[P{심각도}] OneERP 서비스 장애 발생

■ 시각: YYYY-MM-DD HH:MM KST
■ 영향 범위: {영향받는 서비스/기능}
■ 증상: {사용자에게 보이는 증상}
■ 현재 상태: 원인 조사 중
■ 대응 담당: {담당자 이름}
■ 다음 업데이트: {예상 시각} 또는 상황 변경 시

@{호출 대상}
```

### 진행 상황 업데이트

```
[P{심각도}] OneERP 장애 업데이트 #{N}

■ 시각: YYYY-MM-DD HH:MM KST
■ 원인 (추정): {파악된 원인 또는 조사 중인 가설}
■ 조치 내용: {수행 중인/완료된 조치}
■ 현재 상태: {조치 중 / 검증 중 / 부분 복구}
■ 예상 복구 시각: {예상 시각}
■ 다음 업데이트: {예상 시각}
```

### 해결 완료 통보

```
[P{심각도} 해결] OneERP 장애 복구 완료

■ 발생 시각: YYYY-MM-DD HH:MM KST
■ 복구 시각: YYYY-MM-DD HH:MM KST
■ 총 장애 시간: {N}분
■ 근본 원인: {원인 요약}
■ 조치 내용: {수행한 조치 요약}
■ 재발 방지: {즉시 조치 / 포스트모템 예정일}
■ 포스트모템: {작성 예정일 또는 링크}
```

## 포스트모템 템플릿

```markdown
# 포스트모템: {장애 제목}

## 요약
| 항목 | 값 |
|------|-----|
| 일시 | YYYY-MM-DD HH:MM ~ HH:MM KST |
| 심각도 | P{N} |
| 장애 시간 | {N}분 |
| 영향 범위 | {영향받은 서비스/사용자 수} |
| 에러 버짓 소진 | {N}% (월간 기준) |

## 타임라인
| 시각 (KST) | 이벤트 |
|------------|--------|
| HH:MM | 장애 감지 (알림 / 사용자 보고) |
| HH:MM | 대응팀 소집 |
| HH:MM | 원인 파악 |
| HH:MM | 조치 수행 (롤백/핫픽스/스케일링) |
| HH:MM | 서비스 복구 확인 |
| HH:MM | 장애 종료 선언 |

## 근본 원인 (Root Cause)
{근본 원인에 대한 상세 설명}

## 영향
- 사용자 영향: {구체적 영향}
- 데이터 영향: {데이터 손실/불일치 여부}
- SLO 영향: {에러 버짓 소진량}

## 조치 내용
| 조치 | 시각 | 결과 |
|------|------|------|
| {조치 1} | HH:MM | 성공/실패 |

## 재발 방지 (Action Items)
| # | 조치 | 담당 | 기한 | 상태 |
|---|------|------|------|------|
| 1 | {즉시 조치} | {담당자} | {기한} | 완료/진행중 |
| 2 | {구조적 개선} | {담당자} | {기한} | 미착수 |

## 교훈 (Lessons Learned)
### 잘한 점
- {잘한 점}

### 개선할 점
- {개선할 점}
```

> **참조 문서**:
> - `docs/infra/ops/slo.md` — SLO/에러 버짓 정의
> - `docs/ops/runbook-service-deploy.md` — 배포/롤백 절차
> - `docs/ops/runbook-db-backup-restore.md` — DB 복구 절차
