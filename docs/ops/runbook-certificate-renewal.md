# TLS 인증서 갱신 Runbook

## 개요

OneERP 클러스터의 TLS 인증서 관리, 자동/수동 갱신, 만료 모니터링 절차를 정의한다.

| 항목 | 값 |
|------|-----|
| 인증서 관리 | cert-manager |
| 발급 기관 | Let's Encrypt (ACME) |
| ClusterIssuer | `letsencrypt-prod` |
| Ingress Controller | Cilium Gateway API (HTTPRoute) |
| 인증서 유효 기간 | 90일 (Let's Encrypt 기본) |
| 자동 갱신 시점 | 만료 30일 전 (cert-manager 기본) |

## 인증서 구조 (와일드카드 단일 Secret)

구 모델(서비스별 TLS Secret)에서 `*.example.com` 와일드카드 단일 인증서로 전환되었다.

| 항목 | 값 |
|------|-----|
| Secret 이름 | `keiailab-tls` |
| 네임스페이스 | `infra` |
| 도메인 | `*.example.com` |
| Certificate 이름 | `keiailab-wildcard` |
| 용도 | 모든 `.example.com` 서비스 공통 |

Cilium Gateway(`services` 네임스페이스)에서 `infra`의 `keiailab-tls`를 참조하기 위해 ReferenceGrant가 필요하다.

```yaml
# deploy/k8s/referencegrant.yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: ReferenceGrant
metadata:
  name: oneerp-tls-grant
  namespace: infra
spec:
  from:
    - group: gateway.networking.k8s.io
      kind: Gateway
      namespace: services
  to:
    - group: ""
      kind: Secret
      name: keiailab-tls
```

### 각 서비스별 도메인 매핑

| 도메인 | 서비스 | 네임스페이스 |
|--------|--------|------------|
| `oneerp.example.com` | OneERP API + Web | `services` |
| `git.example.com` | CI 시스템 | `platform` |
| `registry.example.com` | Harbor (별도 관리) | `platform` |
| `openbao.example.com` | OpenBao | `platform` |
| `sso.example.com` | Keycloak | `infra` |
| `grafana.example.com` | Grafana | `data` |
| `s3.example.com` | Ceph RGW | `rook-ceph` |

> `registry.example.com`(Harbor)는 `.dev` 도메인을 유지하므로 별도 인증서를 사용한다.

## 자동 갱신 (cert-manager)

### ClusterIssuer 설정

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ci@keiailab.dev
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
```

> 와일드카드 인증서는 HTTP-01 challenge가 불가하므로 DNS-01(Cloudflare) 방식을 사용한다.

**ClusterIssuer 상태 확인**

```bash
# ClusterIssuer 상태 확인
kubectl get clusterissuers.cert-manager.io

# 상세 정보 (Ready 조건 확인)
kubectl describe clusterissuers.cert-manager.io letsencrypt-prod
```

### Certificate 리소스

```yaml
# infra 네임스페이스에 와일드카드 Certificate 정의
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: keiailab-wildcard
  namespace: infra
spec:
  secretName: keiailab-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - "*.example.com"
    - "example.com"
  duration: 2160h    # 90일
  renewBefore: 720h  # 만료 30일 전 갱신
```

**전체 Certificate 상태 조회**

```bash
# 모든 네임스페이스의 인증서 상태 확인
kubectl get certificates.cert-manager.io --all-namespaces

# 상세 출력 (만료일, 갱신일, 상태)
kubectl get certificates.cert-manager.io --all-namespaces \
  -o custom-columns=\
NAMESPACE:.metadata.namespace,\
NAME:.metadata.name,\
READY:.status.conditions[0].status,\
EXPIRY:.status.notAfter,\
RENEWAL:.status.renewalTime

# 와일드카드 인증서 상세 확인
kubectl -n infra describe certificates.cert-manager.io keiailab-wildcard
```

**Cilium Gateway에서 인증서 연결**

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: oneerp-gateway
  namespace: services
spec:
  gatewayClassName: cilium
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: "oneerp.example.com"
      tls:
        mode: Terminate
        certificateRefs:
          - kind: Secret
            name: keiailab-tls
            namespace: infra
```

## 수동 갱신 (긴급)

cert-manager 자동 갱신이 실패했거나 즉시 갱신이 필요한 경우 사용한다.

### 방법 A: cert-manager 강제 갱신

```bash
NS=infra
CERT_NAME=keiailab-wildcard

# cert-manager에 갱신 요청 (cmctl 사용)
cmctl renew $CERT_NAME -n $NS

# cmctl이 없는 경우: Certificate 리소스에 어노테이션으로 갱신 트리거
kubectl -n $NS annotate certificate $CERT_NAME \
  cert-manager.io/renew="true" --overwrite

# 갱신 진행 상태 확인
kubectl -n $NS get certificaterequests.cert-manager.io --sort-by='.metadata.creationTimestamp'

# 갱신 완료 확인
kubectl -n $NS get certificates.cert-manager.io $CERT_NAME
```

### 방법 B: Secret 수동 교체

cert-manager 자체가 장애인 극단적 상황에서 사용한다.

```bash
NS=infra
DOMAIN="*.example.com"

# 1. certbot으로 와일드카드 인증서 수동 발급 (로컬에서, DNS-01 필요)
certbot certonly --manual --preferred-challenges dns \
  -d "*.example.com" -d "example.com" \
  --config-dir ./certbot-config \
  --work-dir ./certbot-work \
  --logs-dir ./certbot-logs

# 2. 기존 Secret 삭제
kubectl -n $NS delete secret keiailab-tls

# 3. 새 인증서로 Secret 생성
kubectl -n $NS create secret tls keiailab-tls \
  --cert=./certbot-config/live/example.com/fullchain.pem \
  --key=./certbot-config/live/example.com/privkey.pem

# 4. Cilium Gateway Controller 재시작 (인증서 반영)
kubectl -n kube-system rollout restart deployment/cilium-operator

# 5. cert-manager 복구 후 Certificate 리소스와 재동기화
kubectl -n $NS annotate certificate keiailab-wildcard \
  cert-manager.io/renew="true" --overwrite
```

## 갱신 검증

인증서 갱신 후 반드시 아래 항목을 확인한다.

### 인증서 유효성 확인

```bash
# openssl로 실제 서빙되는 인증서 확인
for DOMAIN in oneerp.example.com sso.example.com argo.example.com grafana.example.com git.example.com openbao.example.com; do
  echo "=== $DOMAIN ==="
  echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | \
    openssl x509 -noout -dates -subject -issuer 2>/dev/null || echo "  연결 실패"
  echo
done
```

### Kubernetes Secret 확인

```bash
# infra 네임스페이스의 keiailab-tls Secret 확인
echo "=== 네임스페이스: infra ==="
EXPIRY=$(kubectl -n infra get secret keiailab-tls -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -enddate 2>/dev/null)
echo "  keiailab-tls: $EXPIRY"
```

### 서비스 접근 확인

```bash
# HTTPS 응답 코드 확인
for URL in \
  https://oneerp.example.com/api/gateway/healthz \
  https://oneerp.example.com/ \
  https://sso.example.com/realms/oneerp/.well-known/openid-configuration \
  https://argo.example.com/ \
  https://git.example.com/ \
  https://grafana.example.com/; do
  HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 5 "$URL" 2>/dev/null)
  echo "$URL: $HTTP_CODE"
done
```

## 만료 모니터링

### cert-manager 이벤트 모니터링

```bash
# cert-manager 관련 이벤트 확인
kubectl get events --all-namespaces \
  --field-selector reason=Issuing --sort-by='.lastTimestamp' | tail -20

# 실패 이벤트 확인
kubectl get events --all-namespaces \
  --field-selector reason=Failed --sort-by='.lastTimestamp' | tail -20
```

### 만료 임박 인증서 조기 탐지

```bash
# 14일 이내 만료 예정 인증서 확인
THRESHOLD_DAYS=14
THRESHOLD_EPOCH=$(date -v+${THRESHOLD_DAYS}d +%s 2>/dev/null || date -d "+${THRESHOLD_DAYS} days" +%s)

for NS in infra platform services data; do
  for SECRET in $(kubectl -n $NS get secrets -o jsonpath='{range .items[?(@.type=="kubernetes.io/tls")]}{.metadata.name}{"\n"}{end}' 2>/dev/null); do
    EXPIRY_DATE=$(kubectl -n $NS get secret $SECRET -o jsonpath='{.data.tls\.crt}' | \
      base64 -d | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    if [ -n "$EXPIRY_DATE" ]; then
      EXPIRY_EPOCH=$(date -j -f "%b %d %T %Y %Z" "$EXPIRY_DATE" +%s 2>/dev/null || \
        date -d "$EXPIRY_DATE" +%s 2>/dev/null)
      if [ -n "$EXPIRY_EPOCH" ] && [ "$EXPIRY_EPOCH" -lt "$THRESHOLD_EPOCH" ]; then
        echo "경고: $NS/$SECRET 만료 임박 ($EXPIRY_DATE)"
      fi
    fi
  done
done
```

### Prometheus 알림 규칙 (Phase 2)

cert-manager가 내보내는 메트릭으로 자동 알림을 구성한다.

```yaml
# PrometheusRule 리소스 예시
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cert-manager-alerts
  namespace: monitoring
spec:
  groups:
    - name: cert-manager
      rules:
        - alert: CertificateExpiringSoon
          expr: |
            certmanager_certificate_expiration_timestamp_seconds - time() < 7 * 24 * 3600
          for: 1h
          labels:
            severity: warning
          annotations:
            summary: "인증서 만료 7일 이내: {{ $labels.name }} ({{ $labels.namespace }})"
            description: "인증서 {{ $labels.name }}이(가) {{ $value | humanizeDuration }} 후 만료됩니다."

        - alert: CertificateExpiryCritical
          expr: |
            certmanager_certificate_expiration_timestamp_seconds - time() < 3 * 24 * 3600
          for: 10m
          labels:
            severity: critical
          annotations:
            summary: "인증서 만료 3일 이내: {{ $labels.name }} ({{ $labels.namespace }})"
            description: "즉시 갱신이 필요합니다. 인증서 {{ $labels.name }}이(가) {{ $value | humanizeDuration }} 후 만료됩니다."

        - alert: CertificateNotReady
          expr: |
            certmanager_certificate_ready_status{condition="True"} == 0
          for: 15m
          labels:
            severity: critical
          annotations:
            summary: "인증서 Ready 상태 아님: {{ $labels.name }} ({{ $labels.namespace }})"
            description: "cert-manager가 인증서를 발급/갱신하지 못하고 있습니다."
```

## 트러블슈팅

### ACME DNS-01 challenge 실패

**증상**: CertificateRequest가 `False` 상태, cert-manager 로그에 DNS-01 challenge 오류

```bash
# CertificateRequest 상태 확인
kubectl get certificaterequests.cert-manager.io --all-namespaces

# 실패한 CertificateRequest 상세 확인
kubectl describe certificaterequest <NAME> -n <NS>

# Order 및 Challenge 상태 확인
kubectl get orders.acme.cert-manager.io --all-namespaces
kubectl get challenges.acme.cert-manager.io --all-namespaces

# 실패한 Challenge 상세 확인
kubectl describe challenge <NAME> -n <NS>

# cert-manager 로그 확인
kubectl -n cert-manager logs deployment/cert-manager --tail=100 | grep -i "error\|fail\|challenge"
```

**원인별 조치**:

| 원인 | 조치 |
|------|------|
| Cloudflare API 토큰 만료 | `cloudflare-api-token` Secret 갱신 후 cert-manager 재시작 |
| DNS TXT 레코드 전파 지연 | Cloudflare DNS TTL 확인, 최대 5분 대기 |
| 방화벽 차단 | Let's Encrypt 서버에서 DNS 응답 접근이 허용되는지 확인 |
| Rate limit 초과 | Let's Encrypt rate limits 확인 (주당 인증서 5개 제한). 스테이징 서버로 테스트 |
| ClusterIssuer 설정 오류 | `kubectl describe clusterissuer letsencrypt-prod` 에서 Ready 조건 확인 |

```bash
# DNS 해석 확인
for DOMAIN in oneerp.example.com sso.example.com argo.example.com; do
  echo "=== $DOMAIN ==="
  dig +short $DOMAIN
done
```

### Gateway 반영 지연

**증상**: 인증서가 갱신되었으나 브라우저에서 여전히 이전 인증서가 표시됨

```bash
# 1. Secret이 실제로 갱신되었는지 확인
NS=infra
SECRET=keiailab-tls

# Secret의 마지막 수정 시각
kubectl -n $NS get secret $SECRET -o jsonpath='{.metadata.creationTimestamp}'

# Secret 내 인증서 만료일
kubectl -n $NS get secret $SECRET -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -dates

# 2. Cilium Operator가 Secret 변경을 감지했는지 확인
kubectl -n kube-system logs deployment/cilium-operator --tail=50 | \
  grep -i "ssl\|cert\|secret\|reload\|gateway"
```

**조치**:

```bash
# Cilium Operator 강제 재시작
kubectl -n kube-system rollout restart deployment/cilium-operator

# Gateway 리소스 재적용
kubectl -n services get gateway oneerp-gateway -o yaml | kubectl apply -f -

# 확인: 실제 서빙 인증서가 새 인증서인지 검증
echo | openssl s_client -connect oneerp.example.com:443 -servername oneerp.example.com 2>/dev/null | \
  openssl x509 -noout -dates -serial
```

### cert-manager 자체 장애

**증상**: 모든 인증서 갱신이 중단됨, cert-manager Pod가 비정상

```bash
# cert-manager Pod 상태 확인
kubectl -n cert-manager get pods

# cert-manager 로그 확인
kubectl -n cert-manager logs deployment/cert-manager --tail=100
kubectl -n cert-manager logs deployment/cert-manager-cainjector --tail=50
kubectl -n cert-manager logs deployment/cert-manager-webhook --tail=50

# cert-manager CRD 상태 확인
kubectl get crd | grep cert-manager

# cert-manager 웹훅 서비스 확인
kubectl -n cert-manager get svc cert-manager-webhook
```

**조치**:
1. cert-manager Pod 재시작: `kubectl -n cert-manager rollout restart deployment cert-manager`
2. 웹훅 연결 확인: `kubectl -n cert-manager describe svc cert-manager-webhook`
3. CRD 정합성 확인: 필요 시 cert-manager Helm 차트 재설치
4. 긴급 시 "수동 갱신 (방법 B)" 절차로 인증서 교체

> **참조 문서**:
> - `docs/infra/inventory/dns-tls.md` — DNS/TLS 인벤토리
> - `docs/ops/runbook-incident-response.md` — 인증서 만료로 인한 장애 대응
> - `docs/superpowers/specs/2026-03-24-cilium-gateway-deployment-design.md` — Cilium Gateway 설계
