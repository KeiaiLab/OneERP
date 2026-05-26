# FerretDB/PostgreSQL 백업/복구 Runbook

## 개요

OneERP의 데이터 계층인 FerretDB(MongoDB 프로토콜) + PostgreSQL 17(백엔드 스토리지)의 백업/복구 절차를 정의한다.

| 항목 | 값 |
|------|-----|
| DB 엔진 | FerretDB 2.7.0 |
| 백엔드 스토리지 | PostgreSQL 17 |
| K8s 오퍼레이터 | CloudNativePG (CNPG) |
| 백업 저장소 | S3 호환 오브젝트 스토리지 (Ceph RGW: `${ONEERP_S3_ENDPOINT}`) |
| WAL 아카이빙 | Barman (CNPG 내장) |
| RPO (목표 복구 시점) | < 5분 (WAL 연속 아카이빙 기준) |
| RTO (목표 복구 시간) | < 30분 (PITR 기준) |
| 네임스페이스 | `services` |

## 아키텍처 (CNPG + FerretDB)

```
[FastAPI 서비스] → [FerretDB] → [PostgreSQL 17 (CNPG)]
                                       │
                                       ├── WAL 연속 아카이빙 → [Ceph RGW/S3]
                                       ├── ScheduledBackup → [Ceph RGW/S3]
                                       └── pg_basebackup (수동)
```

### CNPG 클러스터 리소스 구조

```yaml
# 예시: services 환경의 PostgreSQL 클러스터
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: oneerp-db
  namespace: services
spec:
  instances: 3  # Primary 1 + Replica 2
  storage:
    size: 50Gi
    storageClass: local-path  # 환경에 따라 조정
  backup:
    barmanObjectStore:
      destinationPath: s3://oneerp-backups/prod/
      endpointURL: https://${ONEERP_S3_ENDPOINT}
      s3Credentials:
        accessKeyId:
          name: backup-s3-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-s3-creds
          key: SECRET_ACCESS_KEY
      wal:
        compression: gzip
        maxParallel: 4
    retentionPolicy: "30d"
```

### 현재 클러스터 상태 확인

```bash
NS=services

# CNPG 클러스터 상태
kubectl -n $NS get clusters.postgresql.cnpg.io

# 클러스터 상세 정보 (Primary/Replica 역할, 동기화 상태)
kubectl -n $NS describe clusters.postgresql.cnpg.io oneerp-db

# Pod 상태 확인
kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db -o wide

# Primary 노드 식별
kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary

# FerretDB 상태 확인
kubectl -n $NS get pods -l app=ferretdb
```

## 정기 백업

### ScheduledBackup (CNPG 자동)

CNPG의 ScheduledBackup 리소스로 자동 백업을 수행한다.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: oneerp-db-daily
  namespace: services
spec:
  schedule: "0 2 * * *"  # 매일 02:00 KST (UTC 17:00)
  backupOwnerReference: self
  cluster:
    name: oneerp-db
  method: barmanObjectStore
  target: prefer-standby  # Replica에서 백업하여 Primary 부하 최소화
```

**ScheduledBackup 적용**

```bash
NS=services

# ScheduledBackup 리소스 적용
kubectl -n $NS apply -f k8s/backup/scheduled-backup.yaml

# 등록된 스케줄 확인
kubectl -n $NS get scheduledbackups.postgresql.cnpg.io

# 최근 백업 목록 확인
kubectl -n $NS get backups.postgresql.cnpg.io --sort-by='.status.startedAt'
```

**백업 상태 모니터링**

```bash
NS=services

# 최근 백업 상세 확인
kubectl -n $NS describe backup $(kubectl -n $NS get backups.postgresql.cnpg.io \
  --sort-by='.status.startedAt' -o jsonpath='{.items[-1].metadata.name}')

# 백업 성공/실패 이력
kubectl -n $NS get backups.postgresql.cnpg.io \
  -o custom-columns=NAME:.metadata.name,STARTED:.status.startedAt,STOPPED:.status.stoppedAt,PHASE:.status.phase
```

### 수동 백업

긴급 백업 또는 특정 시점의 스냅샷이 필요한 경우 사용한다.

**방법 A: CNPG Backup 리소스**

```bash
NS=services

# 즉시 백업 실행
cat <<EOF | kubectl -n $NS apply -f -
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: oneerp-db-manual-$(date +%Y%m%d-%H%M%S)
  namespace: $NS
spec:
  method: barmanObjectStore
  cluster:
    name: oneerp-db
  target: prefer-standby
EOF

# 백업 진행 상태 확인 (완료까지 대기)
kubectl -n $NS get backups.postgresql.cnpg.io -w
```

**방법 B: pg_dump (논리 백업)**

특정 데이터베이스/컬렉션만 백업하거나 다른 환경으로 마이그레이션할 때 사용한다.

```bash
NS=services
PRIMARY_POD=$(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary \
  -o jsonpath='{.items[0].metadata.name}')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 전체 데이터베이스 논리 백업
kubectl -n $NS exec $PRIMARY_POD -- \
  pg_dump -U postgres -d ferretdb -Fc -f /tmp/oneerp_${TIMESTAMP}.dump

# 로컬로 복사
kubectl -n $NS cp $PRIMARY_POD:/tmp/oneerp_${TIMESTAMP}.dump \
  ./backups/oneerp_${TIMESTAMP}.dump

# Pod 내 임시 파일 정리
kubectl -n $NS exec $PRIMARY_POD -- rm /tmp/oneerp_${TIMESTAMP}.dump
```

## 복구 절차

### PITR (Point-in-Time Recovery)

특정 시점으로 정밀 복구한다. WAL 아카이빙이 정상 동작하는 경우에만 가능하다.

> **주의**: PITR은 새로운 클러스터를 생성한다. 기존 클러스터를 직접 수정하지 않는다.

```bash
NS=services

# 1. 복구 대상 시점 결정 (UTC 기준)
RECOVERY_TARGET="2026-03-18T10:30:00Z"

# 2. PITR 클러스터 생성
cat <<EOF | kubectl -n $NS apply -f -
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: oneerp-db-recovery
  namespace: $NS
spec:
  instances: 1  # 복구 검증용 단일 인스턴스
  storage:
    size: 50Gi
  bootstrap:
    recovery:
      source: oneerp-db
      recoveryTarget:
        targetTime: "$RECOVERY_TARGET"
  externalClusters:
    - name: oneerp-db
      barmanObjectStore:
        destinationPath: s3://oneerp-backups/prod/
        endpointURL: https://${ONEERP_S3_ENDPOINT}
        s3Credentials:
          accessKeyId:
            name: backup-s3-creds
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: backup-s3-creds
            key: SECRET_ACCESS_KEY
        wal:
          maxParallel: 4
EOF

# 3. 복구 클러스터 상태 확인
kubectl -n $NS get clusters.postgresql.cnpg.io oneerp-db-recovery -w

# 4. 데이터 검증 (FerretDB 연결하여 확인)
kubectl -n $NS port-forward svc/oneerp-db-recovery-rw 5432:5432 &
# mongosh 또는 psql로 데이터 확인

# 5-a. 검증 성공 → FerretDB 연결을 복구 클러스터로 전환
#      (서비스 엔드포인트 또는 환경변수 수정)
# 5-b. 검증 후 복구 클러스터 삭제
kubectl -n $NS delete clusters.postgresql.cnpg.io oneerp-db-recovery
```

### 전체 복구

최신 백업으로 전체 클러스터를 재구성한다.

```bash
NS=services

# 1. 기존 클러스터 삭제 전 최종 백업 시도
cat <<EOF | kubectl -n $NS apply -f -
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: oneerp-db-final-$(date +%Y%m%d-%H%M%S)
  namespace: $NS
spec:
  method: barmanObjectStore
  cluster:
    name: oneerp-db
EOF

# 2. FerretDB 중지 (데이터 정합성 보호)
kubectl -n $NS scale deployment ferretdb --replicas=0

# 3. 기존 클러스터 삭제
kubectl -n $NS delete clusters.postgresql.cnpg.io oneerp-db

# 4. 백업에서 새 클러스터 복원
cat <<EOF | kubectl -n $NS apply -f -
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: oneerp-db
  namespace: $NS
spec:
  instances: 3
  storage:
    size: 50Gi
  bootstrap:
    recovery:
      source: oneerp-db-backup
  externalClusters:
    - name: oneerp-db-backup
      barmanObjectStore:
        destinationPath: s3://oneerp-backups/prod/
        endpointURL: https://${ONEERP_S3_ENDPOINT}
        s3Credentials:
          accessKeyId:
            name: backup-s3-creds
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: backup-s3-creds
            key: SECRET_ACCESS_KEY
        wal:
          maxParallel: 4
  backup:
    barmanObjectStore:
      destinationPath: s3://oneerp-backups/prod/
      endpointURL: https://${ONEERP_S3_ENDPOINT}
      s3Credentials:
        accessKeyId:
          name: backup-s3-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-s3-creds
          key: SECRET_ACCESS_KEY
      wal:
        compression: gzip
        maxParallel: 4
    retentionPolicy: "30d"
EOF

# 5. 클러스터 Ready 대기
kubectl -n $NS get clusters.postgresql.cnpg.io oneerp-db -w

# 6. FerretDB 재시작
kubectl -n $NS scale deployment ferretdb --replicas=2

# 7. 서비스 연결 확인
for SVC in gateway selling buying stock accounting; do
  kubectl -n $NS logs deployment/$SVC --tail=10 | grep -i "database\|connect"
done
```

### 특정 컬렉션 복구

특정 비즈니스 데이터만 복구해야 하는 경우이다. PITR 복구 클러스터에서 해당 컬렉션만 추출하여 운영 DB에 삽입한다.

```bash
NS=services

# 1. PITR 복구 클러스터를 생성한다 (위 PITR 절차 참조)

# 2. 복구 클러스터에서 특정 테이블 추출 (FerretDB는 PostgreSQL 스키마에 매핑)
RECOVERY_POD=$(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db-recovery,role=primary \
  -o jsonpath='{.items[0].metadata.name}')

# FerretDB의 컬렉션은 PostgreSQL의 테이블로 매핑됨
# 스키마: ferretdb.{database_name}_{collection_name}
kubectl -n $NS exec $RECOVERY_POD -- \
  pg_dump -U postgres -d ferretdb \
  -t 'ferretdb.oneerp_sales_orders' \
  --data-only -Fc -f /tmp/collection_recovery.dump

# 3. 운영 DB에 복원
PRIMARY_POD=$(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary \
  -o jsonpath='{.items[0].metadata.name}')

kubectl -n $NS cp $RECOVERY_POD:/tmp/collection_recovery.dump /tmp/collection_recovery.dump
kubectl -n $NS cp /tmp/collection_recovery.dump $PRIMARY_POD:/tmp/collection_recovery.dump

# 기존 데이터를 백업 후 복원 (--clean 옵션은 기존 데이터를 먼저 삭제)
kubectl -n $NS exec $PRIMARY_POD -- \
  pg_restore -U postgres -d ferretdb --data-only --clean /tmp/collection_recovery.dump

# 4. 임시 파일 및 복구 클러스터 정리
kubectl -n $NS exec $RECOVERY_POD -- rm /tmp/collection_recovery.dump
kubectl -n $NS exec $PRIMARY_POD -- rm /tmp/collection_recovery.dump
kubectl -n $NS delete clusters.postgresql.cnpg.io oneerp-db-recovery
```

## 백업 검증

### 복구 테스트 (분기별)

분기마다 1회 이상 복구 리허설을 수행하여 백업 유효성을 검증한다.

**검증 절차**

```bash
NS=services  # 운영 환경 (단일 환경)

# 1. 운영 백업에서 스테이징 클러스터 복원
cat <<EOF | kubectl -n $NS apply -f -
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: recovery-test-$(date +%Y%m%d)
  namespace: $NS
spec:
  instances: 1
  storage:
    size: 50Gi
  bootstrap:
    recovery:
      source: prod-backup
  externalClusters:
    - name: prod-backup
      barmanObjectStore:
        destinationPath: s3://oneerp-backups/prod/
        endpointURL: https://${ONEERP_S3_ENDPOINT}
        s3Credentials:
          accessKeyId:
            name: backup-s3-creds
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: backup-s3-creds
            key: SECRET_ACCESS_KEY
EOF

# 2. 복원 완료 대기
kubectl -n $NS get clusters.postgresql.cnpg.io recovery-test-$(date +%Y%m%d) -w

# 3. 데이터 무결성 검증
RECOVERY_POD=$(kubectl -n $NS get pods -l cnpg.io/cluster=recovery-test-$(date +%Y%m%d),role=primary \
  -o jsonpath='{.items[0].metadata.name}')

# 테이블 수 확인
kubectl -n $NS exec $RECOVERY_POD -- psql -U postgres -d ferretdb \
  -c "SELECT schemaname, COUNT(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') GROUP BY schemaname;"

# 레코드 수 샘플 확인
kubectl -n $NS exec $RECOVERY_POD -- psql -U postgres -d ferretdb \
  -c "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 20;"

# 4. 검증 완료 후 정리
kubectl -n $NS delete clusters.postgresql.cnpg.io recovery-test-$(date +%Y%m%d)
```

**검증 체크리스트**

| 항목 | 확인 |
|------|------|
| 복원 클러스터가 Ready 상태에 도달 | [ ] |
| 테이블/컬렉션 수가 운영과 일치 | [ ] |
| 주요 컬렉션 레코드 수가 합리적 | [ ] |
| FerretDB 연결 후 쿼리 정상 응답 | [ ] |
| 복구 소요 시간이 RTO(30분) 이내 | [ ] |
| 결과를 복구 리허설 기록에 첨부 | [ ] |

## 데이터 마이그레이션

### 스키마 변경 시 절차

FerretDB는 스키마리스이지만, 애플리케이션 레벨에서 문서 구조가 변경되는 경우의 절차이다.

**1. 변경 영향 분석**

```bash
# 영향받는 컬렉션의 현재 문서 구조 샘플 확인
# (FerretDB에 mongosh로 접속)
mongosh "mongodb://ferretdb.services.svc:27017/oneerp" --eval '
  db.sales_orders.find().limit(5).pretty()
'
```

**2. 마이그레이션 스크립트 작성 및 테스트**

```bash
# 스테이징에서 먼저 실행
NS=services

# 마이그레이션 Job 실행
kubectl -n $NS apply -f k8s/migrations/migration-YYYYMMDD.yaml

# 결과 확인
kubectl -n $NS logs job/migration-YYYYMMDD
```

**3. 운영 적용**

```bash
NS=services

# 마이그레이션 전 수동 백업 (필수)
cat <<EOF | kubectl -n $NS apply -f -
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: pre-migration-$(date +%Y%m%d-%H%M%S)
  namespace: $NS
spec:
  method: barmanObjectStore
  cluster:
    name: oneerp-db
EOF

# 백업 완료 대기
kubectl -n $NS get backups.postgresql.cnpg.io -w

# 마이그레이션 Job 실행
kubectl -n $NS apply -f k8s/migrations/migration-YYYYMMDD.yaml
kubectl -n $NS logs -f job/migration-YYYYMMDD

# 실패 시 PITR로 마이그레이션 직전 시점으로 복구
```

## 트러블슈팅

### WAL 아카이빙 실패

**증상**: CNPG 클러스터의 WAL 아카이빙이 실패하여 PITR이 불가능해진다.

```bash
NS=services

# 클러스터 상태에서 WAL 아카이빙 오류 확인
kubectl -n $NS describe clusters.postgresql.cnpg.io oneerp-db | grep -A 10 "Conditions"

# Primary Pod의 barman 로그 확인
PRIMARY_POD=$(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n $NS logs $PRIMARY_POD | grep -i "wal\|archive\|barman"

# S3 연결 테스트
kubectl -n $NS exec $PRIMARY_POD -- \
  barman-cloud-check-wal-archive \
  --cloud-provider aws-s3 \
  --endpoint-url https://${ONEERP_S3_ENDPOINT} \
  s3://oneerp-backups/prod/ oneerp-db
```

**조치**:
1. S3(Ceph RGW) 접근 자격증명 확인 (`backup-s3-creds` Secret)
2. S3 버킷 존재 및 권한 확인
3. 네트워크 정책으로 Ceph RGW(`${ONEERP_S3_ENDPOINT}`) 접근이 차단되지 않았는지 확인
4. 디스크 공간 확인 (WAL이 로컬에 쌓이고 있을 수 있음)

```bash
# WAL 파일 로컬 축적량 확인
kubectl -n $NS exec $PRIMARY_POD -- du -sh /var/lib/postgresql/data/pgdata/pg_wal/
```

### 스토리지 부족

**증상**: PVC 용량이 부족하여 PostgreSQL이 쓰기를 거부한다.

```bash
NS=services

# PVC 사용량 확인
kubectl -n $NS exec $(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary \
  -o jsonpath='{.items[0].metadata.name}') -- df -h /var/lib/postgresql/data

# PVC 현재 크기 확인
kubectl -n $NS get pvc -l cnpg.io/cluster=oneerp-db
```

**조치**:

```bash
NS=services

# 방법 1: CNPG 클러스터의 스토리지 크기 확장 (StorageClass가 확장 지원 시)
kubectl -n $NS patch clusters.postgresql.cnpg.io oneerp-db \
  --type merge -p '{"spec":{"storage":{"size":"100Gi"}}}'

# 방법 2: 불필요한 데이터 정리 (PostgreSQL VACUUM)
PRIMARY_POD=$(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n $NS exec $PRIMARY_POD -- psql -U postgres -d ferretdb \
  -c "VACUUM FULL VERBOSE;"

# 방법 3: 오래된 WAL 파일 정리 (CNPG가 자동 관리하지만 수동 확인)
kubectl -n $NS exec $PRIMARY_POD -- \
  ls -la /var/lib/postgresql/data/pgdata/pg_wal/ | wc -l
```

### CNPG Primary 장애 시 자동 Failover 확인

```bash
NS=services

# 현재 Primary 확인
kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db \
  -o custom-columns=NAME:.metadata.name,ROLE:.metadata.labels.role

# Failover 이벤트 확인
kubectl -n $NS get events --field-selector reason=Failover --sort-by='.lastTimestamp'

# 새로운 Primary가 정상인지 확인
kubectl -n $NS exec $(kubectl -n $NS get pods -l cnpg.io/cluster=oneerp-db,role=primary \
  -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -c "SELECT pg_is_in_recovery();"
# 결과가 'f' (false)이면 Primary로 정상 승격된 것
```

> **참조 문서**:
> - `docs/infra/ops/backup-restore.md` — 백업/복구 전략 설계
> - `docs/infra/ops/slo.md` — RPO/RTO 목표
> - `docs/infra/inventory/data-storage.md` — 스토리지 인벤토리
