#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

ts="$(date -u +%Y%m%d_%H%M%S)"
out_dir="artifacts/inventory/$ts"
mkdir -p "$out_dir"

echo "Writing inventory artifacts to: $out_dir"

run() {
  local name="$1"
  shift
  local path="$out_dir/$name.txt"
  {
    echo "$ $*"
    "$@"
  } >"$path" 2>&1 || {
    # Keep artifacts even when commands fail (e.g. missing access).
    echo "Command failed (captured in $path)"
  }
}

run "system" uname -a
run "python" python3 --version
run "uv" uv --version
run "git" git --version
run "node" node --version
run "docker" docker --version

if command -v kubectl >/dev/null 2>&1; then
  run "kubectl_client" kubectl version --client --output=yaml
  run "k8s_cluster_info" kubectl cluster-info
  run "k8s_nodes" kubectl get nodes -o wide
  run "k8s_namespaces" kubectl get ns
  run "k8s_storageclass" kubectl get sc
  run "k8s_ingressclass" kubectl get ingressclass
  run "k8s_networkpolicy" kubectl get networkpolicy -A
  run "k8s_deployments" kubectl get deployments -A
  run "k8s_ingress" kubectl get ingress -A
  run "k8s_ingressroute" kubectl get ingressroute -A
  run "k8s_ingressroute_keycloak" kubectl -n infra get ingressroute keycloak -o yaml
  run "k8s_crd_argocd" bash -lc 'kubectl get crd | rg -n "argocd" || true'
  run "k8s_crd_observability" bash -lc 'kubectl get crd | rg -n "prometheus|loki|tempo|jaeger|opentelemetry|cert-manager" || true'
else
  echo "kubectl not found; skipping k8s collection"
fi

if command -v curl >/dev/null 2>&1; then
  run "oidc_discovery_master" curl -fsSL ${ONEERP_OIDC_ISSUER:-http://localhost:8080}/realms/master/.well-known/openid-configuration
fi

cat >"$out_dir/README.md" <<'EOF'
# Inventory Artifacts

이 디렉토리는 Phase 0 “공유 리소스 인벤토리” 증빙을 위한 자동 수집 결과다.

- 커밋 금지: `artifacts/`는 gitignore 대상
- 민감정보가 포함될 수 있으니 공유 전에 반드시 검토/마스킹할 것

다음 단계:

1) `docs/infra/inventory/00-checklist.md`를 기준으로 `docs/infra/inventory/*.md`에 요약을 반영
2) 주요 결정은 ADR로 확정: `docs/governance/adr/`
EOF

echo "Done."
