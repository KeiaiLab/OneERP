#!/usr/bin/env bash
# rotate_secret <module> <tier>
# tier = services (prod) | staging
# 범용 시크릿 회전 — OpenBao(kv) + kubernetes rollout
set -euo pipefail

usage() {
  echo "usage: $0 <module> <services|staging>" >&2
  exit 2
}
[ "$#" -eq 2 ] || usage
MODULE="$1"
TIER="$2"
case "$TIER" in
  services) KV_PATH="kv/services/${MODULE}" ; NS="services" ;;
  staging)  KV_PATH="kv/staging/${MODULE}"  ; NS="staging"  ;;
  *) usage ;;
esac

echo "rotating ${MODULE} in tier=${TIER} (kv=${KV_PATH}, ns=${NS})"

# staging은 dry-run 기본
if [ "$TIER" = "staging" ]; then
  echo "[staging] dry-run · read-only rotation simulation"
  bao kv get -format=json "$KV_PATH" >/dev/null
  echo "[staging] simulated rotation complete"
  exit 0
fi

# prod tier — 실제 회전
NEW_SECRET=$(openssl rand -base64 32)
bao kv put "$KV_PATH" secret="$NEW_SECRET"
kubectl -n "$NS" rollout restart deploy/"$MODULE"
