#!/usr/bin/env bash
# FerretDB/CNPG 스냅샷 복구 래퍼 — G4-3 백업·복구 드릴 실행 도구.
# docs/ops/runbook-db-backup-restore.md §"PITR" 절차를 CLI 로 감싸, 드릴에서
# 안전하게 반복 실행하도록 한다.
#
# 사용:
#   scripts/ops/restore-ferretdb.sh \
#       --snapshot oneerp-backup-2026-04-20T23-59Z \
#       --target   staging-ferretdb \
#       --collections "gateway.*"
#
# 옵션:
#   --snapshot NAME    복구 대상 CNPG Backup 리소스 이름(또는 targetTime ISO).
#   --target   CLUSTER 복구 대상 임시 클러스터 이름 (기본: recovery-$(date +%Y%m%d)).
#   --collections GLOB 복구 후 pg_dump 추출 대상 (선택, 생략 시 전체 유지).
#   --namespace NS     기본 services.
#   --dry-run          실제 적용 없이 계획만 출력.
#
# 전제:
#   - kubectl, jq 설치.
#   - CNPG 오퍼레이터(postgresql.cnpg.io/v1) 설치.
#   - ${ONEERP_S3_ENDPOINT:-s3.example.com} 백업 버킷 ACCESS_KEY_ID/SECRET 이 backup-s3-creds 시크릿에 존재.

set -euo pipefail

SNAPSHOT=""
TARGET="recovery-$(date +%Y%m%d)"
COLLECTIONS=""
NS="services"
DRY_RUN=0

usage() { grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//' ; exit "${1:-0}" ; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --snapshot)    SNAPSHOT="$2"; shift 2 ;;
    --target)      TARGET="$2"; shift 2 ;;
    --collections) COLLECTIONS="$2"; shift 2 ;;
    --namespace)   NS="$2"; shift 2 ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     usage 0 ;;
    *)             echo "unknown arg: $1" >&2; usage 2 ;;
  esac
done

[[ -z "$SNAPSHOT" ]] && { echo "ERROR: --snapshot 필수" >&2; exit 2; }

run() { if [[ "$DRY_RUN" = "1" ]]; then echo "[dry-run] $*"; else eval "$@"; fi ; }

# kubectl 연결 확인 — 드릴 실행 환경 사전 점검.
command -v kubectl >/dev/null || { echo "kubectl 없음" >&2; exit 3; }
if ! kubectl api-resources --api-group=postgresql.cnpg.io 2>/dev/null | grep -q clusters; then
  echo "ERROR: CNPG 오퍼레이터 미설치(postgresql.cnpg.io 그룹 없음)" >&2
  exit 4
fi

echo "==> 1/4 복구 클러스터 매니페스트 생성: $TARGET (namespace=$NS)"
MANIFEST=$(cat <<YAML
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: ${TARGET}
  namespace: ${NS}
spec:
  instances: 1
  storage:
    size: 50Gi
  bootstrap:
    recovery:
      source: oneerp-db-backup
      recoveryTarget:
        backupID: ${SNAPSHOT}
  externalClusters:
    - name: oneerp-db-backup
      barmanObjectStore:
        destinationPath: s3://oneerp-backups/prod/
        endpointURL: https://${ONEERP_S3_ENDPOINT:-s3.example.com}
        s3Credentials:
          accessKeyId:    { name: backup-s3-creds, key: ACCESS_KEY_ID }
          secretAccessKey: { name: backup-s3-creds, key: SECRET_ACCESS_KEY }
        wal: { maxParallel: 4 }
YAML
)

echo "$MANIFEST"
echo "==> 2/4 적용"
run "echo '$MANIFEST' | kubectl -n $NS apply -f -"

echo "==> 3/4 Ready 대기 (최대 30분)"
run "kubectl -n $NS wait clusters.postgresql.cnpg.io/${TARGET} --for=condition=Ready --timeout=30m"

if [[ -n "$COLLECTIONS" ]]; then
  echo "==> 4/4 컬렉션 추출: $COLLECTIONS → /tmp/${TARGET}.dump"
  POD=$(kubectl -n "$NS" get pods -l cnpg.io/cluster=${TARGET},role=primary -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
  if [[ -z "$POD" && "$DRY_RUN" = "1" ]]; then POD="<recovery-primary>"; fi
  [[ -z "$POD" ]] && { echo "Primary Pod 찾을 수 없음" >&2; exit 5; }
  # FerretDB 컬렉션 → ferretdb.<db>_<collection> 테이블 매핑.
  TABLE_GLOB=$(echo "$COLLECTIONS" | sed 's#\.\*#%#; s#\.#_#g')
  run "kubectl -n $NS exec $POD -- pg_dump -U postgres -d ferretdb -t 'ferretdb.${TABLE_GLOB}' --data-only -Fc -f /tmp/${TARGET}.dump"
  echo "성공. 덤프 위치: pod ${POD}:/tmp/${TARGET}.dump"
else
  echo "==> 4/4 컬렉션 필터 없음 — 전체 복구 클러스터 유지"
fi

echo
echo "드릴 기록 체크포인트:"
echo "  - 스냅샷: $SNAPSHOT"
echo "  - 복구 클러스터: $NS/$TARGET"
echo "  - 추출 컬렉션: ${COLLECTIONS:-(none)}"
echo "  - 완료 시각: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
