# ADR-0014: 런타임 Plane 분해 (Traffic-Shape 기반)

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted (2026-04-13 부활 — 본 ADR 폐기 결정 철회) |
| 채택일 | 원 채택 2026-04-12, 본 부활 채택 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, 플랫폼 리드 |
| 영향 범위 | 컨테이너/프로세스 경계, 배포 단위, 헬스체크, 자원 할당 |
| 관련 ADR | ADR-0011(코드 클러스터, **본 ADR과 직교 축**), ADR-0008(관측성), ADR-0010(배포) |
| 후속 phase | M3 완료 — `docs/engineering/msa/CONSOLIDATION.md` |

책임 기준선은 `docs/governance/architecture/responsibility-matrix.md`를 따른다.

## 0. 부활 노트 (2026-04-13)

본 ADR은 2026-04-13 ADR 전면 재작성 시 일시 폐기됐다. 이는 ADR-0011
초안이 본 ADR을 supersede한다고 잘못 단언한 결과였다. 그러나 실측
조사에서 다음을 확인:

- `deploy/catalog/planes.yaml` 첫 줄: "ADR-0014 Runtime Plane SoT"
- `docker-compose.yml` 6개 plane을 활성 컨테이너로 정의
- `planes/` 디렉토리에 6개 plane 코드(api/realtime/worker/scheduler/edge/extension) 가동 중

본 ADR이 정의한 런타임 모델은 활성 운영 중이며, ADR-0011은 코드 조직
축만 다루도록 §0 노트로 범위를 축소했다. 따라서 본 ADR을 동일자에
부활시키고 ADR-0011과 동등한 활성 ADR로 공존한다.

ADR 불변 원칙 예외 적용 사유: 채택 당일 동일 위원회 검토에서 발견된
사실 오류(폐기 결정의 근거 부재) 정정. 결정 자체의 변경이 아니라
잘못된 폐기의 철회.

## 1. 맥락(Context)

OneERP는 도메인 디렉토리 18~48개 단위로 컨테이너를 띄우면 다음 비용이
발생한다:

- 컨테이너 18~48개, 로컬 RAM 16GB+ (M2 Mac 한계)
- 동일 도메인 코드의 HTTP 라우트·워커·스케줄러 작업이 별도 컨테이너로
  분산 → 자원 비효율 + 코드 위치와 컨테이너 위치 불일치
- compose profile 7종 운영 부담

도메인 응집도 축(ADR-0011)으로 코드를 조직했더라도, **트래픽 형태
(Traffic-Shape)** — 동기 HTTP, 양방향 실시간, 백그라운드 워커, 스케줄,
외부 게이트웨이, 외부 시스템 어댑터 — 는 자원 프로파일·SLO·확장
정책이 다르다. 이를 컨테이너 경계로 분리하면 자원·확장 효율이 크게
개선된다.

근거 인벤토리:
- `deploy/catalog/planes.yaml` (런타임 SoT)
- `planes/api_plane/`, `planes/realtime_plane/`, `planes/worker_plane/`,
  `planes/scheduler_plane/`, `planes/edge_plane/`, `planes/extension_plane/`
- `docker-compose.yml`
- `scripts/verify_plane_boot.py`
- `docs/engineering/msa/CONSOLIDATION.md` (M3 완료 기록)

## 2. 결정(Decision)

OneERP의 런타임 컨테이너 경계는 **6개 Plane**으로 분해한다. 각 plane은
트래픽 형태가 같은 코드를 호스팅한다.

### 2.1 6개 Plane

| Plane | 책임 | 트래픽 형태 | 외부 노출 |
|-------|------|------------|-----------|
| `edge` | 외부 진입 게이트웨이, OIDC 검증, 권한 1차, 라우팅 | 외부 동기 HTTP | host:8080 (유일) |
| `api` | 도메인 동기 HTTP API (`/api/v1/<domain>/*`) | 동기 HTTP | 내부 |
| `realtime` | WebSocket, SSE, 실시간 알림·메시지 | 양방향 영구 연결 | 내부 |
| `worker` | NATS subscribe → 비동기 작업 (이메일·집계·이벤트 핸들러) | 큐 소비 | 내부 |
| `scheduler` | cron 잡 (마감·점검·배치) | 시간 기반 | 내부 |
| `extension` | 외부 시스템 어댑터 (integration-hub, IoT 게이트웨이) | 외부 비동기/Webhook | 옵션 |

### 2.2 경계 원칙
- **단일 외부 노출**: `edge` 만 호스트 포트 노출. 나머지 plane은 내부망.
- **plane 간 통신**: compose 네트워크 hostname (예: `http://api-plane:8000`)
- **공유 코드**: `planes/_shared/` + `core/oneerp_core/`
- **도메인 코드 import**: 각 plane이 `services/<cluster>/<domain>/`에서
  필요한 라우트·핸들러·잡·스케줄을 명시 import (ADR-0011 코드 조직과
  N:M 매핑)

### 2.3 도메인 코드 ↔ Plane 매핑
- 단일 도메인이 여러 plane에서 호스팅될 수 있다(ADR-0011 §9 부록 참조)
- 매핑 SoT: `deploy/catalog/planes.yaml`의 `planes.<name>.includes` 절
- 변경 시 `scripts/verify_plane_boot.py`로 부팅 검증

### 2.4 Plane별 SLO 차등
| Plane | 가용성 SLO | 지연 SLO | 자원 프로파일 |
|-------|-----------|----------|--------------|
| edge | 99.95% | p95 < 50ms (overhead) | CPU 우선 |
| api | 99.9% | p95 < 200ms (ADR-0001 G2-1) | CPU + 메모리 균형 |
| realtime | 99.9% | p99 RTT < 100ms | 메모리 + 연결 수 |
| worker | 99.5% | p95 작업 < 30초 (ADR-0001) | CPU 폭증 허용 |
| scheduler | 99.5% | 정시±1분 | 경량 |
| extension | 99.5% | 외부 시스템 의존 | 격리 |

### 2.5 Compose Profile
- `infra` — 데이터/메시징/캐시 5종
- `plane` — 6 plane + infra (기본 개발 흐름)
- `full` — plane + 추가 도메인별 컨테이너(필요 시)
- `dev-ports` — 모든 plane 호스트 포트 노출(개발 한정)

- **범위 In**: 컨테이너 경계, 헬스체크, 자원 할당, 배포 단위.
- **범위 Out**:
  - 코드 조직 (ADR-0011)
  - FE 빌드 (단일 Next.js, `web/`)
  - 인프라 구성요소(별도 ADR/문서)

## 3. 대안(Alternatives Considered)

### 대안 A — 도메인 단위 컨테이너 (18~48개)
- 단점: 자원 비효율, 워커/스케줄 트래픽 형태 무시.
- 채택하지 않은 이유: 측정값으로 명확.

### 대안 B — 단일 모놀리식 컨테이너
- 단점: 트래픽 형태별 SLO·자원 분리 불능, 한 번의 장애가 전체 정지.
- 채택하지 않은 이유: 격리 가치 손실.

### 대안 C — Kubernetes Deployment per 도메인 (12~48 deployments)
- 단점: 클러스터 자원 오버헤드, 워커/스케줄 인스턴스 빈 자원 다수.
- 채택하지 않은 이유: 본 ADR이 정의한 6 plane 위에 Helm chart 6개로
  매핑하는 게 단순 + 효율.

### 대안 D — 현 상태 유지 (도메인 컨테이너)
- 채택하지 않은 이유: 캠페인 동기 무력화.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 5/5 | RAM/CPU 효율 큰 폭 개선 |
| 리스크 | 4/5 | 6 plane 경계 단순, 부팅 검증 자동화 |
| 운영 | 5/5 | 트래픽 형태별 자원·SLO 차등 |
| 팀 역량 | 4/5 | 코드 위치(ADR-0011)와 컨테이너 위치 분리 학습 필요 |

## 5. 영향(Consequences)

### 5.1 긍정적
- RAM/CPU 자원 효율.
- 트래픽 형태별 SLO·확장 정책 가능(예: worker만 burst auto-scale).
- 컨테이너 수 감소로 운영 단순.

### 5.2 부정적
- 코드 위치(ADR-0011 클러스터) ≠ 컨테이너 위치(plane). 신규 인원
  학습 곡선 → §6 매핑 표 + onboarding 문서로 완화.
- plane 간 통신은 in-cluster HTTP → cross-cluster 호출의 일부가 plane
  경계를 횡단할 수 있음. ADR-0007/0008 표준으로 관측 의무.

### 5.3 호환성/마이그레이션
- 외부 API 라우트 영향 0 (edge → api plane으로 forward, 라우트 prefix 보존).
- 이벤트 체인 영향 0 (NATS 토픽 동일).
- 기존 도메인 컨테이너 정의는 deprecated, P5에서 정리.

### 5.4 측정 지표

| 지표 | 이전 | 현재 | 목표 유지 |
|------|------|------|-----------|
| 컨테이너 수(plane profile) | 48+ | 6 + infra(5) | ≤ 12 |
| 로컬 기동 RAM | 16GB+ | 측정 | < 8GB |
| `verify_plane_boot.py` 통과 | n/a | 6/6 | 100% |
| edge 외 plane의 호스트 포트 노출 | 다수 | 0 | 0 |

## 6. ADR-0011과의 매핑

ADR-0011 §9 부록 A의 코드 클러스터 ↔ plane 매트릭스 참조. 본 ADR과
ADR-0011은 N:M:
- 한 클러스터의 코드가 여러 plane에서 호스팅
- 한 plane이 여러 클러스터의 코드를 호스팅

매핑 SoT: `deploy/catalog/planes.yaml`.

## 7. 실행 항목

- [x] M1~M3 완료 — 6 plane 부팅 검증 (2026-04-12)
- [ ] 플랫폼 — `verify_plane_boot.py`를 CI 게이트로 활성 — 2026-05-15
- [ ] 플랫폼 — plane별 SLO 대시보드 (ADR-0008 §부록) — 2026-06-15
- [ ] 인프라 — Helm chart 6 plane 정비 — 캠페인 P4
- [ ] 운영 — plane별 자원 baseline 측정 + 알림 룰 — 2026-06-30

## 8. 검증

- [ ] CI에 plane 부팅 회귀 검사
- [ ] 분기 RAM·기동 시간 측정
- [ ] edge 외 plane의 외부 노출 차단 admission

## 9. Plane 별 책임 매트릭스 (요약)

| Plane | HTTP 라우트 | NATS subscribe | cron | WebSocket | 외부 호출 |
|-------|------------|---------------|------|-----------|-----------|
| edge | `/*` (모든 도메인 forward) | X | X | (옵션) | X |
| api | `/api/v1/*` | (선택) | X | X | (선택) |
| realtime | `/ws/*` | X | X | O | X |
| worker | X | O | X | X | (선택) |
| scheduler | X | (publish) | O | X | X |
| extension | `/webhooks/*` | (publish) | X | X | O |

## 10. 참고 자료

- `deploy/catalog/planes.yaml`
- `docker-compose.yml`
- `planes/`
- `scripts/verify_plane_boot.py`
- `docs/engineering/msa/CONSOLIDATION.md`
- ADR-0011 (코드 조직 — 본 ADR과 직교 축)
- ADR-0008 (관측성), ADR-0010 (배포)
