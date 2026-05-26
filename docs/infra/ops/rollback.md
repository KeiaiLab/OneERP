# 롤백 전략

## 목표

- wave 종료 시점의 최소 조건은 **deployable / rollbackable / test-green** 이다.
- 배포 실패 시 “서비스 가용성”을 우선 복구한다.
- DB·이벤트 마이그레이션은 기본적으로 **forward-only** 이고, rollback은 예외 경로다.

## wave 종료 3조건

1. **deployable**: 현재 wave 산출물이 배포 가능한 상태다.
2. **rollbackable**: 직전 안정 버전으로 되돌릴 수 있는 경로가 남아 있다.
3. **test-green**: 계약/배포/웹 검증 게이트가 녹색이다.

## expand / migrate / contract 관계

- **expand**: 새 API 필드, 새 이벤트 필드, 새 배포 항목을 기존 계약과 공존 가능하게 먼저 추가한다.
- **migrate**: 데이터 backfill, consumer 전환, 운영 설정 전환을 수행한다.
- **contract**: old path / old field / old event / old catalog entry를 제거한다.

즉, rollback은 forward-only 마이그레이션을 부정하는 기본 경로가 아니라, expand/migrate/contract 중 어느 단계에서든 현재 wave의 가용성을 회복하기 위한 운영 수단이다.

## 확인 필요(Phase 0)

- 배포 방식(GitOps/Helm 등)
- 마이그레이션 도구/절차
- 데이터 손실 허용 범위(RPO)
