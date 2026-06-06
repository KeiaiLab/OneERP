# ADR-0010: 배포 파이프라인 표준 (buildx + 환경 승격)

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted (배포 엔진 부분 RFC-0048로 갱신: ArgoCD → Flux, 2026-06-04) |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, 플랫폼 리드 |
| 영향 범위 | 모든 컨테이너 빌드, CI/CD, 환경(dev/stg/prod), 롤백 |
| 관련 ADR | ADR-0001(G4-4 롤백), ADR-0007(API 호환), ADR-0008(관측성), ADR-0011(plane) |
| 후속 phase | P-016 (이미지 파이프라인), P-017 (환경 승격 자동화) |

## 1. 맥락(Context)

ADR-0001 G4-4는 "무중단 또는 N분 이내 롤백 + 마이그레이션 backwards-
compatible 한 단계"를 요구한다. 전역 규칙(`/Users/phil/.claude/CLAUDE.md`):

> 배포 컨테이너 이미지는 `docker buildx` + `masblue-builder`(기본 빌더)로
> 빌드한다. `--platform` 생략 시 자동 linux/amd64. 멀티아키텍처 빌드 금지.

또한 OneERP는 이중 배포 모델(`docs/engineering/architecture/deployment-parity.md`):
- 온프렘: docker compose
- 클라우드: K8s/Helm/Flux (최초 ArgoCD 채택, RFC-0048로 Flux 전환 — 2026-06-04)
- 단일 SoT: `deploy/catalog/`

현재 미정의 사항:
- 이미지 태깅·버저닝 규칙
- 환경 승격(dev → stg → prod) 자동화
- 마이그레이션 단계 분리(expand/contract)
- 롤백 절차 표준
- 카나리/블루그린 정책
- SBOM·이미지 서명

이 상태로는 배포 사고 시 어떤 이미지·어떤 마이그레이션이 적용됐는지
역추적이 어렵고, 롤백 시간이 예측 불가능하다.

근거 인벤토리:
- `docs/engineering/architecture/deployment-parity.md`
- `docs/infra/ops/rollback.md`
- `docs/engineering/msa/CONSOLIDATION.md` (48→19 클러스터, 7 profile)
- `docker-compose.yml`, `deploy/catalog/`
- 전역 규칙 (buildx + masblue-builder)

## 2. 결정(Decision)

OneERP는 7개 결정으로 단일 배포 파이프라인을 표준화한다.

### 2.1 이미지 빌드
- 빌더: `docker buildx` + `masblue-builder` (전역 규칙 강제)
- 플랫폼: `linux/amd64` 단일 (멀티아키 금지)
- 베이스: Python `python:3.14-slim-bookworm`, Node `node:22-bookworm-slim`
- 멀티스테이지: `builder` → `runtime`
- 비특권 사용자(`uid=10001`)
- 이미지당 EntryPoint 하나, CMD 인자 분리
- 헬스체크 `HEALTHCHECK` 정의

### 2.2 태깅·버전
- **의미적 버전**(SemVer): `vX.Y.Z`
  - X: ADR-0007 메이저 또는 plane 경계 변경
  - Y: 호환 기능 추가
  - Z: 호환 패치
- **빌드 메타데이터**: `vX.Y.Z+sha.<git7>`
- **추가 태그**: 환경 alias(`stg-current`, `prod-current` — 가변), 날짜
  (`2026-04-13`), latest는 dev 전용
- **immutable**: prod에 푸시되는 정확한 SHA 태그는 불변

### 2.3 SBOM·서명·취약점
- 빌드 시 SBOM 생성(`syft` SPDX) → 레지스트리 첨부
- 이미지 서명: `cosign` keyless (OIDC) — prod 배포 검증
- 취약점 스캔: `trivy` Critical/High 0건 PR 통과 조건
- 시크릿 스캔: 빌드 산출물에서 `gitleaks` 0건

### 2.4 환경 승격 흐름
```text
PR merge → dev 자동 → CI 게이트 → stg 자동 → soak 30분 → prod 수동 승인
                                          │
                                          └→ 카나리(10%→50%→100%)
```
- dev: 모든 커밋
- stg: dev 통과 + smoke + 보안 스캔
- prod: stg soak 30분 + 카나리 + 수동 승인(2-eye)

### 2.5 마이그레이션 단계 분리(Expand/Contract)
모든 스키마 변경은 3단계.

1. **Expand**: 신규 필드/컬렉션/인덱스 추가 (구버전 호환)
2. **Migrate**: 데이터 이동·코드 두 경로 모두 동작
3. **Contract**: 구필드/컬렉션/인덱스 제거

각 단계는 별도 PR + 별도 배포. 단일 PR에 3단계 결합 금지.
관련 backfill은 idempotent + 재시작 가능.

### 2.6 카나리·블루그린
- 기본: 카나리 10% → 50% → 100% (15분 간격)
- 기준 메트릭: SLI(에러율·지연·readiness) 비교, 임계 초과 시 자동 중단
- 블루그린: 마이그레이션이 expand-only인 경우 옵션
- 데이터베이스: 단일 인스턴스 공유, 서비스 단위 카나리

### 2.7 롤백 표준
- 모든 배포는 **이전 immutable 태그**로 즉시 롤백 가능
- 롤백 명령: `make rollback ENV=prod TARGET=vA.B.C`
- RTO: ≤ 5분 (애플리케이션), ≤ 30분 (마이그레이션 contract 단계만 필요 시 — 단, 사전 검증 의무)
- 마이그레이션 롤백: contract 단계는 별도 ADR/CR 필요(파괴적)

- **범위 In**: 모든 BE 서비스, FE 빌드 산출물, 마이그레이션, 인프라
  매니페스트.
- **범위 Out**:
  - 데이터 파이프라인 외부 잡(별도 ADR)
  - 클라이언트 모바일 앱(별도 store 정책)

## 3. 대안(Alternatives Considered)

### 대안 A — 멀티 아키 빌드(arm64 + amd64)
- 단점: 빌드 시간 X2, masblue-builder 정책 위반.
- 채택하지 않은 이유: 전역 규칙.

### 대안 B — 환경별 별도 빌드
- 단점: dev/stg/prod 이미지가 다른 코드일 위험.
- 채택하지 않은 이유: "동일 이미지 승격" 원칙 깨짐.

### 대안 C — 직접 푸시(prod 즉시)
- 단점: stg 검증 생략 → 사고 빈도 증가.
- 채택하지 않은 이유: G4-4 위반.

### 대안 D — GitOps 단일(ArgoCD만)
- 장점: 선언적.
- 단점: 온프렘 docker compose 흐름과 중복.
- 채택하지 않은 이유: 이중 배포 모델 유지(`deployment-parity.md`).

### 대안 E — 현 상태 유지
- 채택하지 않은 이유: 추적성·롤백 불능.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 4/5 | 단일 빌드 + 승격 |
| 리스크 | 5/5 | expand/contract + 카나리 + 롤백 표준 |
| 운영 | 4/5 | 단일 SoT(deploy/catalog) 유지 |
| 팀 역량 | 4/5 | buildx/cosign 학습 곡선 낮음 |

## 5. 영향(Consequences)

### 5.1 긍정적
- 사고 시 즉시 롤백.
- 이미지 출처·SBOM 추적성.
- 환경 간 동일 산출물 보장.

### 5.2 부정적
- 마이그레이션 PR 분할 부담(expand/migrate/contract 3 PR).
- soak 30분 대기 → 긴급 핫픽스 별도 fast-path 필요.

### 5.3 호환성/마이그레이션
- 기존 이미지 태그 그대로 유지, 신규부터 표준 태깅.
- 마이그레이션 분할 미적용 기존 PR은 예외 처리(별도 검토).

### 5.4 측정 지표

| 지표 | 현재 | 목표(6개월) |
|------|------|-------------|
| 롤백 평균 시간 | 측정 | ≤ 5분 |
| prod 배포 실패율 | 측정 | < 5% |
| stg → prod 평균 lead time | 측정 | < 4시간(영업일) |
| SBOM 첨부율 | 0% | 100% |
| 이미지 서명 검증율(prod) | 0% | 100% |
| 카나리 자동 중단 정상 동작 | n/a | 분기 1회 검증 |

## 6. 핫픽스(Fast-Path)

- 보안/데이터 정합성 사고 한정
- soak 30분 → 5분으로 단축, 카나리 단계 50%→100% 즉시
- 사후 24시간 내 회고 + 회귀 테스트 추가
- 분기 fast-path 사용 횟수가 일반 흐름의 20% 초과 시 본 ADR 재검토

## 7. 환경 매트릭스

| 환경 | 트리거 | 승인 | 카나리 | 롤백 RTO |
|------|--------|------|--------|----------|
| dev | 모든 커밋 | 자동 | 즉시 100% | 즉시 |
| stg | dev 통과 | 자동 | 즉시 100% | 즉시 |
| prod | stg soak | 2-eye 수동 | 10/50/100 | ≤ 5분 |

## 8. 이미지 레지스트리

- prod 이미지: 사내 Harbor(레지스트리)
- 태그 정책: prod 푸시 후 immutable
- 보존: prod 태그 24개월, dev/stg 90일
- 액세스: 빌더 push만, 사용자 read-only

## 9. 실행 항목

- [ ] 플랫폼 — buildx + masblue-builder 워크플로 통일 — 2026-05-15 — phase: P-016
- [ ] 플랫폼 — `cosign` keyless 서명 + 검증 admission — 2026-05-31
- [ ] 플랫폼 — `syft`/`trivy`/`gitleaks` CI 잡 — 2026-05-31
- [ ] 플랫폼 — 카나리 자동 중단(메트릭 비교) — 2026-06-30 — phase: P-017
- [ ] SRE — 환경 승격 흐름 + soak 자동화 — 2026-06-30
- [ ] DBA — expand/contract 마이그레이션 가이드 — 2026-05-31
- [ ] SRE — `make rollback` 통일 명령 — 2026-05-31

## 10. 검증

- [ ] CI에 SBOM/서명/스캔 강제
- [ ] 분기 1회 카나리 자동 중단 시뮬레이션
- [ ] 분기 1회 롤백 RTO 검증
- [ ] 마이그레이션 단계 분리 미준수 PR 차단

## 11. 부록 — Dockerfile 표준 (요약)

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.14-slim-bookworm AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.14-slim-bookworm AS runtime
RUN useradd -u 10001 -m app
USER app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app . .
ENV PATH="/app/.venv/bin:$PATH"
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1
EXPOSE 8000
ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 12. 참고 자료

- `docs/engineering/architecture/deployment-parity.md`
- `docs/infra/ops/rollback.md`
- `docs/engineering/msa/CONSOLIDATION.md`
- ADR-0001 G4-4, ADR-0007, ADR-0008, ADR-0011
- 전역 CLAUDE.md (buildx + masblue-builder 규칙)
- DORA — Continuous Delivery
- Sigstore/cosign: <https://docs.sigstore.dev>
