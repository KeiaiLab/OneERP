# 서비스 배포/롤백 Runbook

## 개요

OneERP 마이크로서비스의 배포, 롤백, 배포 후 검증 절차를 정의한다.

| 항목 | 값 |
|------|-----|
| 대상 서비스 | gateway, selling, buying, stock, accounting, hr, payroll, expenses, web |
| 배포 도구 | ArgoCD + Helm |
| 이미지 레지스트리 | Harbor (`ghcr.io/oneerp/`) |
| CI | CI Actions (`build-push.yml`) |
| 빌드 도구 | Buildah (CI) / `apple/container` (로컬) |
| 네임스페이스 | `services` |

## 사전 조건

- `kubectl` 클러스터 접근 확인 (`kubectl get ns services`)
- `argocd` CLI 로그인 (`argocd login argo.example.com`)
- Harbor 레지스트리 접근 권한 (`buildah login ghcr.io`)
- Helm 3.x 설치 확인 (`helm version`)
- ArgoCD Application 리소스가 배포 대상 서비스에 대해 등록되어 있을 것

## 배포 전 게이트

- `./scripts/ci/run.sh` 통과
- `./scripts/ci/run_contract_tests.sh` 통과
- `./scripts/ci/check_openapi_drift.sh` 에서 generated drift 없음
- `web/lib/types/generated/` 기준 generated 타입이 현재 커밋과 일치

## 배포 절차

### 일반 배포 (ArgoCD 자동 동기화)

표준 배포 흐름이다. main 브랜치에 머지하면 CI가 이미지를 빌드·푸시하고 ArgoCD가 자동 동기화한다.

```
PR 머지 → CI Actions(build-push.yml)
  → Buildah 빌드(linux/amd64)
  → Harbor 푸시(SHA 태그 + latest)
  → ArgoCD 자동 감지
  → Helm 릴리즈 업그레이드
  → Pod 롤링 업데이트
```

**1. PR 머지 후 CI 빌드 확인**

```bash
# CI Actions에서 build-push 워크플로우 상태 확인
# CI 시스템 UI: https://github.com/oneerp/oneerp/actions

# Harbor에서 이미지 태그 확인
# Harbor UI: https://ghcr.io/harbor/projects/oneerp/repositories
```

**2. ArgoCD 동기화 상태 확인**

```bash
# 전체 앱 상태 확인
argocd app list --project oneerp

# 특정 서비스 동기화 상태 확인
argocd app get oneerp-gateway -o wide

# 동기화 대기 (최대 5분)
argocd app wait oneerp-gateway --timeout 300
```

**3. Pod 롤아웃 완료 대기**

```bash
# 네임스페이스 지정
NS=services

# 특정 서비스 롤아웃 상태 확인
kubectl -n $NS rollout status deployment/gateway --timeout=120s
kubectl -n $NS rollout status deployment/selling --timeout=120s
```

### 수동 배포 (긴급)

ArgoCD 자동 동기화가 동작하지 않거나 즉시 배포가 필요한 경우에 사용한다.

**방법 A: ArgoCD 수동 동기화**

```bash
# 단일 서비스 강제 동기화
argocd app sync oneerp-gateway --force

# 전체 프로젝트 동기화
argocd app sync -l app.kubernetes.io/part-of=oneerp --force
```

**방법 B: Helm 직접 업그레이드**

ArgoCD가 완전히 불가한 상황에서만 사용한다. ArgoCD와 상태 불일치가 발생하므로 반드시 사후 동기화를 수행한다.

```bash
NS=services
SERVICE=gateway
TAG=abc1234  # 빌드된 커밋 SHA 앞 7자리

# Helm 업그레이드
helm upgrade $SERVICE charts/$SERVICE \
  --namespace $NS \
  --set image.repository=ghcr.io/oneerp/$SERVICE \
  --set image.tag=$TAG \
  --wait --timeout 120s

# ArgoCD 상태 재동기화 (반드시 실행)
argocd app sync oneerp-$SERVICE
```

**방법 C: 이미지 태그 직접 변경**

최후 수단이다. Helm/ArgoCD 모두 불가한 상황에서만 사용한다.

```bash
NS=services
SERVICE=gateway
TAG=abc1234

kubectl -n $NS set image deployment/$SERVICE \
  $SERVICE=ghcr.io/oneerp/$SERVICE:$TAG

kubectl -n $NS rollout status deployment/$SERVICE --timeout=120s
```

> **주의**: 이 방법은 ArgoCD가 감지하면 OutOfSync 상태가 된다. 복구 후 반드시 ArgoCD와 동기화한다.

### 카나리 배포 (선택)

트래픽의 일부만 신규 버전으로 라우팅하여 점진적으로 검증하는 방식이다.

```bash
NS=services
SERVICE=gateway
TAG_NEW=abc1234

# 1. 카나리 디플로이먼트 생성 (전체 replicas의 10%)
kubectl -n $NS create deployment ${SERVICE}-canary \
  --image=ghcr.io/oneerp/$SERVICE:$TAG_NEW \
  --replicas=1

# 2. 동일한 서비스 셀렉터 레이블 부여
kubectl -n $NS label deployment ${SERVICE}-canary app=$SERVICE

# 3. 트래픽 분산 확인 (기존 N개 + 카나리 1개)
kubectl -n $NS get endpoints $SERVICE

# 4. 로그/메트릭 모니터링 (최소 15분)
kubectl -n $NS logs -l app=$SERVICE --tail=100 -f

# 5-a. 카나리 성공 → 전체 배포 진행
kubectl -n $NS delete deployment ${SERVICE}-canary
argocd app sync oneerp-$SERVICE

# 5-b. 카나리 실패 → 카나리만 삭제
kubectl -n $NS delete deployment ${SERVICE}-canary
```

## 롤백 절차

### ArgoCD 롤백

가장 권장하는 롤백 방법이다.

```bash
# 배포 이력 조회
argocd app history oneerp-gateway

# 특정 리비전으로 롤백
argocd app rollback oneerp-gateway <REVISION_NUMBER>

# 롤백 후 상태 확인
argocd app get oneerp-gateway
```

### 롤백 전 체크리스트

- 직전 wave가 deployable / rollbackable / test-green 상태였는지 확인
- `./scripts/ci/run_contract_tests.sh` 와 `uv run python -m scripts.deploy validate` 결과를 확인
- 관련 운영 문서(`README.md`, `docs/ARCHITECTURE-MAP.md`, `docs/infra/ops/rollback.md`)의 SoT 참조가 현재 gate와 일치하는지 확인

### 롤백 후 체크리스트

- `argocd app get` / `rollout status` / smoke check로 복구 상태 확인
- `./scripts/ci/run.sh` 또는 최소 `./scripts/ci/run_contract_tests.sh` 재실행
- generated drift 상태와 문서 sync 여부를 기록

### 이미지 태그 롤백

이전에 정상 동작했던 이미지 태그로 즉시 롤백한다.

```bash
NS=services
SERVICE=gateway
PREV_TAG=def5678  # 이전 정상 태그

# 현재 이미지 태그 확인
kubectl -n $NS get deployment $SERVICE -o jsonpath='{.spec.template.spec.containers[0].image}'

# 이전 태그로 롤백
kubectl -n $NS set image deployment/$SERVICE \
  $SERVICE=ghcr.io/oneerp/$SERVICE:$PREV_TAG

kubectl -n $NS rollout status deployment/$SERVICE --timeout=120s
```

### Helm 롤백

```bash
NS=services
SERVICE=gateway

# Helm 릴리즈 이력 조회
helm -n $NS history $SERVICE

# 이전 리비전으로 롤백
helm -n $NS rollback $SERVICE <REVISION_NUMBER> --wait --timeout 120s

# ArgoCD 동기화
argocd app sync oneerp-$SERVICE
```

### Kubernetes 네이티브 롤백

```bash
NS=services
SERVICE=gateway

# 롤아웃 이력 조회
kubectl -n $NS rollout history deployment/$SERVICE

# 직전 리비전으로 롤백
kubectl -n $NS rollout undo deployment/$SERVICE

# 특정 리비전으로 롤백
kubectl -n $NS rollout undo deployment/$SERVICE --to-revision=<N>

kubectl -n $NS rollout status deployment/$SERVICE --timeout=120s
```

## 배포 후 검증

### 헬스체크

```bash
NS=services

# 모든 Pod Ready 상태 확인
kubectl -n $NS get pods -l app.kubernetes.io/part-of=oneerp -o wide

# Readiness Probe 상태 확인
kubectl -n $NS describe pod -l app=gateway | grep -A 5 "Readiness"

# 서비스 엔드포인트 헬스체크 (포트포워딩으로 확인)
for SVC in gateway selling buying stock accounting; do
  echo "=== $SVC ==="
  kubectl -n $NS port-forward svc/$SVC 8080:8000 &
  sleep 2
  curl -sf http://localhost:8080/healthz && echo " OK" || echo " FAIL"
  kill %1 2>/dev/null
done
```

### 스모크 테스트

```bash
NS=services
API_HOST=${ONEERP_API_HOST}

# Gateway 루트 응답 확인
curl -sf https://$API_HOST/api/gateway/healthz | jq .

# 각 서비스 헬스체크 (경로 기반 라우팅)
for SVC in selling buying stock accounting; do
  echo "=== $SVC ==="
  HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" https://$API_HOST/api/$SVC/healthz)
  if [ "$HTTP_CODE" = "200" ]; then
    echo "  OK ($HTTP_CODE)"
  else
    echo "  FAIL ($HTTP_CODE)"
  fi
done

# Web 프론트엔드 응답 확인
curl -sf -o /dev/null -w "HTTP %{http_code}\n" https://${ONEERP_API_HOST}/
```

### 메트릭 확인

> Phase 2에서 Grafana/Prometheus 구축 후 대시보드로 대체할 항목이다.

```bash
NS=services

# Pod 리소스 사용량
kubectl -n $NS top pods

# 최근 5분간 이벤트 확인 (에러/경고 필터)
kubectl -n $NS get events --sort-by='.lastTimestamp' | tail -30

# Pod 재시작 횟수 확인 (0이어야 정상)
kubectl -n $NS get pods -o custom-columns=\
NAME:.metadata.name,\
RESTARTS:.status.containerStatuses[0].restartCount,\
STATUS:.status.phase
```

## 트러블슈팅

### Pod CrashLoopBackOff

**증상**: Pod가 반복적으로 시작과 종료를 반복한다.

```bash
NS=services
POD_NAME=<문제 Pod 이름>

# Pod 상태 및 이벤트 확인
kubectl -n $NS describe pod $POD_NAME

# 현재 컨테이너 로그 (크래시 직전)
kubectl -n $NS logs $POD_NAME --previous

# 공통 원인 점검
# 1. 환경변수/시크릿 누락
kubectl -n $NS get pod $POD_NAME -o jsonpath='{.spec.containers[0].env[*].name}'

# 2. DB 연결 실패
kubectl -n $NS logs $POD_NAME | grep -i "connection\|ferretdb\|postgres"

# 3. 포트 충돌
kubectl -n $NS get pod $POD_NAME -o jsonpath='{.spec.containers[0].ports[*].containerPort}'
```

**조치**:
1. 로그에서 에러 메시지 확인
2. 환경변수/시크릿 누락 시 → ConfigMap/Secret 수정 후 Pod 재시작
3. DB 연결 실패 시 → FerretDB Pod 상태 확인, 네트워크 정책 점검
4. 해결 불가 시 → 이전 이미지로 롤백

### ImagePullBackOff

**증상**: 컨테이너 이미지를 가져올 수 없다.

```bash
NS=services
POD_NAME=<문제 Pod 이름>

# 이벤트에서 상세 에러 확인
kubectl -n $NS describe pod $POD_NAME | grep -A 10 "Events:"

# 이미지 이름/태그 확인
kubectl -n $NS get pod $POD_NAME -o jsonpath='{.spec.containers[0].image}'

# Harbor imagePullSecret 확인
kubectl -n $NS get secret harbor-pull-secret -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d | jq .
```

**조치**:
1. 이미지 태그가 Harbor에 존재하는지 확인 (Harbor UI)
2. `imagePullSecret`이 네임스페이스에 존재하는지 확인
3. Secret의 레지스트리 URL, 사용자, 비밀번호가 유효한지 확인
4. Harbor 접근 가능 여부 확인 (`curl -s https://ghcr.io/v2/`)

### 설정 누락

**증상**: 서비스가 시작되지만 특정 기능이 실패하거나 `KeyError`/`ValidationError` 로그가 발생한다.

```bash
NS=services
SERVICE=gateway

# 현재 환경변수 목록 확인
kubectl -n $NS exec deployment/$SERVICE -- env | grep ONEERP_

# ConfigMap 내용 확인
kubectl -n $NS get configmap ${SERVICE}-config -o yaml

# Secret 키 목록 확인 (값은 노출하지 않음)
kubectl -n $NS get secret ${SERVICE}-secret -o jsonpath='{.data}' | jq 'keys'
```

**조치**:
1. `ONEERP_` 접두사 환경변수가 서비스의 `Settings` 클래스 필드와 일치하는지 확인
2. 누락된 환경변수를 ConfigMap 또는 Secret에 추가
3. Pod 재시작: `kubectl -n $NS rollout restart deployment/$SERVICE`

### OOMKilled

**증상**: Pod가 메모리 한도를 초과하여 강제 종료된다.

```bash
NS=services
POD_NAME=<문제 Pod 이름>

# OOM 여부 확인
kubectl -n $NS get pod $POD_NAME -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'

# 현재 메모리 limits 확인
kubectl -n $NS get pod $POD_NAME -o jsonpath='{.spec.containers[0].resources.limits.memory}'
```

**조치**:
1. 메모리 limits를 단계적으로 증가 (예: 256Mi → 512Mi)
2. 애플리케이션 레벨 메모리 누수 조사
3. Helm values에서 `resources.limits.memory` 수정 후 재배포

## 연락처

| 역할 | 담당 | 연락처 |
|------|------|--------|
| 인프라/K8s 관리자 | TBD | TBD |
| 서비스 개발 리드 | TBD | TBD |
| DB 관리자 | TBD | TBD |
| 보안 담당 | TBD | TBD |

**에스컬레이션 경로**: 담당자 → 개발 리드 → 인프라 관리자 → CTO

> **참조 문서**:
> - `docs/engineering/architecture/repo-structure-rules.md` — 구조/소유권 정본
 > - `docs/infra/ops/rollback.md` — 롤백 전략 설계
 > - `docs/infra/ops/slo.md` — SLO 목표 및 에러 버짓
 > - `docs/infra/inventory/cicd.md` — CI/CD 인벤토리
