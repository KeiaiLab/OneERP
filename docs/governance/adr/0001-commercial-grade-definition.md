# ADR-0001: 상용 제품 정의(DoD)와 통과 게이트

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회 |
| 영향 범위 | 전체 (모든 서비스·모듈·런타임) |
| 관련 ADR | ADR-0002(웨이브 정책), ADR-0003(테스트 게이트), ADR-0008(관측성), ADR-0009(백업/복구) |
| 후속 phase | 모든 모듈 상용화 phase의 진입·완료 조건 |

## 1. 맥락(Context)

OneERP는 50+ 모듈(`docs/generated/INDEX.md` 기준 47 ERD 모듈)을 포함하는
모놀리식 모노레포에서 출발해 Runtime-Plane 분해를 거쳤고(legacy
ADR-0014, 본 ADR 채택과 동시에 폐기), 현재는 `services/`와
`packages/core/`에 코드가 분산돼 있다. 일부 모듈은 ERD·API 문서가
존재하지만 구현 깊이는 모듈마다 제각각이다.

"상용 제품 수준"이라는 표현은 지금까지 비공식적으로 사용돼 왔으며,
어떤 모듈이 "상용화 완료" 상태인지 객관적으로 판정할 기준이 없다.
이 모호함은 다음 결과를 만들어 왔다:

- 모듈 간 품질 편차 (인증 통합/감사 로깅이 일부에서만 적용)
- 릴리즈 시기 판단 불가 (얼마나 더 작업해야 하는지 추정 불능)
- 회귀 사고 반복 (DoD 미정의로 회귀 테스트 범위가 모호)
- 외부 도입 검토 시 일관된 답변 불가

본 ADR은 **"상용 제품(commercial-grade)"이라는 단어의 객관 정의를
확정**하고, 모듈/서비스 단위로 그 상태에 도달했는지 판정할
**자동·수동 게이트 집합**을 명시한다.

근거 인벤토리:
- `docs/infra/ops/slo.md` — 가용성 99.9%, p95<200ms, 일 100만 트랜잭션
- `docs/engineering/ci/test-strategy.md` — 단위/통합/E2E 3계층
- `docs/engineering/architecture/api-standards.md` — API 표준
- `docs/engineering/architecture/authz.md` — 권한 표준
- `docs/engineering/architecture/multitenancy.md` — 멀티테넌시 표준
- `docs/infra/ops/observability.md`, `rollback.md`, `backup-restore.md`
- `docs/generated/INDEX.md` — 47 ERD 모듈 인벤토리

## 2. 결정(Decision)

OneERP는 "상용 제품"이라는 단어를 다음과 같이 단일 정의한다:

> **상용 제품(Commercial-grade)이란, 유료 외부 고객에게 SLA를 약속하고
> 운영할 수 있는 상태이며, 본 ADR이 명시한 5개 영역 23개 게이트를 모두
> 통과해야 한다.**

- **단위**: 게이트 통과 판정은 "**모듈(domain module)**" 단위로 한다.
  서비스(`services/<name>`)가 다중 모듈을 호스팅할 경우 모든 모듈이
  통과해야 그 서비스 전체가 상용화 완료다.
- **범위 In**: `services/`, `packages/core/`, `apps/web/`의 모듈별 코드,
  스키마, 문서, 테스트, 인프라 설정, 운영 절차.
- **범위 Out**: 미공개 실험 모듈(`docs/generated/erd-*.md`에 인덱싱되지
  않은 신규 ERD), 내부 도구(`scripts/`), 데모/픽스처.
- **발효 시점**: 2026-04-13 즉시. 단, 기존 모듈에는 ADR-0002 웨이브
  순서대로 적용한다.
- **유효 기간**: 무기한. 외부 SLA가 변경되면 본 ADR을 supersede한다.

## 3. 대안(Alternatives Considered)

### 대안 A — 최소 기준만 정의하고 모듈별 자율
- 설명: "동작하면 상용", 모듈팀이 자체 판단.
- 장점: 빠른 확장, 팀 자율성.
- 단점: 일관성 부재, SLA 약속 불가, 사고 시 책임 분기 모호.
- 채택하지 않은 이유: 외부 고객에게 통합 SLA를 약속하려면 모든 모듈이
  동일 수준이어야 한다. 평균이 아니라 최저점이 SLA를 결정한다.

### 대안 B — 산업 표준(ISO 25010, NIST CSF) 직접 채택
- 설명: 표준 품질 모델을 그대로 사용.
- 장점: 외부 인증 친화적.
- 단점: ERP 도메인에 비해 일반적이고, OneERP 인프라(FerretDB, plane)에
  대한 구체 지표가 없어서 운영 게이트로 변환하는 작업이 별도 필요.
- 채택하지 않은 이유: 본 ADR을 ISO 25010 매핑 가능한 형태로 작성하되,
  게이트 자체는 OneERP 컨텍스트에 맞춰 구체화한다(부록 §9 매핑 참조).

### 대안 C — 현 상태 유지(Do Nothing)
- 비용: 모듈 간 품질 편차 누적, 릴리즈 판단 불능 지속.
- 리스크: 첫 외부 도입 시 SLA 위반 → 신뢰도 손상.
- 채택하지 않은 이유: "상용화"는 마케팅 표현이 아니라 운영 책임이므로
  객관 게이트 없이는 진입 자체가 위험하다.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 3/5 | 게이트 23개의 자동화에 초기 1~2 phase 투입 필요 |
| 리스크 | 5/5 | 게이트 통과 = SLA 약속 가능, 미통과 모듈 식별 자동화 |
| 운영 | 5/5 | "상용/비상용" 라벨이 모니터링·알림 우선순위에 직접 매핑 |
| 팀 역량 | 4/5 | 기존 표준 문서들과 1:1 매칭, 학습 부담 낮음 |

- **결정적 근거**: SLO(`docs/infra/ops/slo.md`)가 99.9%·p95<200ms로
  이미 정량 정의돼 있으므로, 그 위에 게이트를 얹는 것은 기존 운영
  정책의 자연 확장이다.
- **수용한 트레이드오프**: 게이트가 23개로 적지 않아 신규 모듈이
  상용화 라벨을 얻는 데 시간이 걸린다. 반대급부로 라벨을 얻은
  순간부터 SLA 약속이 가능하다.

## 5. 영향(Consequences)

### 5.1 긍정적 영향
- 모듈별 "상용화 완료/진행 중/미착수" 라벨이 단일 정의로 집계 가능.
- 외부 도입 검토 시 객관 답변(통과 게이트 N/23) 가능.
- 회귀 사고 발생 시 어느 게이트가 깨졌는지 즉시 식별.
- 릴리즈 의사결정이 게이트 통과율로 자동화 가능.

### 5.2 부정적 영향 / 리스크
- 게이트 23개를 모두 자동화하기 전에는 수동 점검 부담이 크다.
- 현재 통과 모듈이 0~소수일 가능성이 높아, 단기적으로 "상용 모듈 0개"
  라는 정확하지만 부담스러운 메시지를 노출하게 된다.
- 게이트가 너무 엄격해서 일부 모듈이 영구히 비상용으로 남을 위험.

### 5.3 마이그레이션 / 호환성
- 기존 코드는 그대로 둔다. 게이트 미통과는 결함이 아니라 "비상용"
  라벨이며, ADR-0002 웨이브 순서로 격상한다.
- 외부 API 호환성에 영향 없음(본 ADR은 정의만 한다).
- 롤백: 본 ADR을 supersede하는 새 ADR로 정의를 갱신할 수 있다.
  과거 라벨링 기록은 git 이력에 보존된다.

### 5.4 측정 지표

| 지표 | 현재(2026-04-13) | 목표(6개월) | 측정 방법 |
|------|------------------|-------------|-----------|
| 상용화 완료 모듈 수 | 측정 필요 | 12개(웨이브 1+2) | `scripts/audit/commercial-readiness.py` |
| 게이트 평균 통과율 | 측정 필요 | 80% | 동일 스크립트 |
| SLA 위반(월간) | 측정 필요 | 0건 | Prometheus + 인시던트 로그 |
| 회귀 사고(분기) | 측정 필요 | <1건 | INC-* 카운트 |

## 6. 5개 영역 23개 게이트 (정의 본체)

> 모듈 M이 "상용화 완료" 라벨을 얻으려면 아래 23개 게이트를 모두
> 통과해야 한다. 각 게이트는 자동(A)/수동(M)/문서(D) 점검 유형을 갖는다.

### 6.1 영역 1 — 기능 완전성 (Functional Completeness, 5게이트)

#### G1-1 (D) ERD/스펙 일치
- `docs/generated/erd-<module>.md`가 존재하며 최신 코드와 일치
- 검증: `scripts/docs/gen_erd.py --check` 무차분
- 책임: 모듈 오너

#### G1-2 (D) API 명세 발행
- `docs/api/<module>/openapi.yaml` 또는 자동 생성된 OpenAPI가 존재
- FastAPI `/openapi.json`이 schema validation 통과
- 검증: `scripts/api/validate_openapi.py`

#### G1-3 (A) CRUD 전 흐름 동작
- 핵심 엔티티에 대한 Create/Read/Update/Delete + List + Search가
  통합 테스트로 검증됨
- 검증: `pytest -m integration -k <module>` 100% 통과

#### G1-4 (A) 도메인 규칙 단위 테스트
- `docs/generated/erd-<module>.md`의 비즈니스 규칙(상태 전이, 검증,
  계산식)이 단위 테스트로 1:1 매핑됨
- 검증: 커버리지 ≥ 90% (도메인 모듈 한정), 분기 커버리지 ≥ 80%

#### G1-5 (D) UI 페이지 템플릿 적용
- `apps/web/`에 List/Detail/Form 페이지가 `docs/engineering/ui/page-templates.md`
  표준대로 구현됨
- 검증: Storybook 또는 시각 회귀(visual regression) 통과

### 6.2 영역 2 — 비기능 품질 (Non-Functional, 5게이트)

#### G2-1 (A) SLO 충족
- `docs/infra/ops/slo.md`의 모듈별 시나리오 SLO 만족
  - 가용성 ≥ 99.9% (월간)
  - API p95 < 200ms, p99 < 500ms
  - 에러율 < 0.1%
- 검증: Prometheus 30일 롤링 계산값

#### G2-2 (A) 부하 시험 통과
- `docs/engineering/data/perf-benchmarks.md`의 목표 RPS 달성
- 동시 1만 사용자 시나리오에서 SLO 만족
- 검증: k6 또는 Locust 시나리오 결과 첨부

#### G2-3 (A) 메모리/CPU 회귀 게이트
- baseline 대비 +20% 초과 시 CI 실패
- 검증: `scripts/perf/regression.py`

#### G2-4 (M) 장애 시나리오(Chaos) 검증
- DB 단절, 네트워크 지연, 다운스트림 실패 시나리오를 수동 또는
  자동으로 1회 이상 실행하고 결과 보고서 보관
- 검증: `docs/kb/incident/chaos-<module>-YYYYMMDD.md` 존재

#### G2-5 (A) i18n/L10n 핸들링
- 한국어/영어 최소 2 로케일 동작
- 날짜·통화·숫자 포맷이 `docs/engineering/architecture/i18n.md` 표준 준수
- 검증: 로케일 단위 스냅샷 테스트

### 6.3 영역 3 — 보안·컴플라이언스 (Security & Compliance, 5게이트)

#### G3-1 (A) 인증 통합
- 모든 엔드포인트가 OIDC를 통한 인증을 요구하거나 명시적 public 표시
- 검증: `scripts/security/auth_coverage.py` 100%

#### G3-2 (A) 권한 매트릭스 적용
- ADR-0006(권한 모델) 기반 권한 매트릭스가 모듈별 정의됨
- 권한 체크 누락 라우트 0건
- 검증: 정적 분석 + 라우트별 권한 테스트

#### G3-3 (A) 멀티테넌시 격리
- 모든 쿼리에 `tenant_id` 필터 강제 (ORM/리포지토리 레이어)
- cross-tenant 접근 시도 시 403 + 감사 로그
- 검증: 페어테넌트 격리 테스트 100% 통과

#### G3-4 (A) 감사 로그
- `docs/engineering/data/audit-log-spec.md` 필수 이벤트 모두 기록
  (생성/수정/삭제, 권한 변경, 민감 데이터 접근)
- 검증: 모듈별 감사 이벤트 카탈로그 ≥ 명세된 항목

#### G3-5 (A) 의존성·시크릿 스캔
- `pip-audit`, `npm audit` Critical/High 0건
- 시크릿이 코드/이미지에 포함되지 않음(`gitleaks` 통과)
- 검증: CI 게이트

### 6.4 영역 4 — 운영 준비 (Operability, 5게이트)

#### G4-1 (A) 관측성 표준
- ADR-0008(관측성) 의무 항목 모두 구현
  - `/healthz`, `/readyz` 정상 응답
  - 표준 메트릭(요청 수/지연/에러율) 노출
  - 구조화 로그 (JSON, traceId 필수)
  - OpenTelemetry trace 발신
- 검증: `scripts/ops/observability_check.py`

#### G4-2 (D) Runbook 발행
- `docs/ops/runbook-<module>.md`에 다음 절차 포함:
  - 시작/중지/재시작
  - 주요 알림 5종에 대한 1차 대응
  - 데이터 정합성 점검 쿼리
  - 에스컬레이션 경로
- 검증: 체크리스트

#### G4-3 (A) 백업·복구 검증
- ADR-0009 RPO/RTO 등급 충족
- 분기 1회 이상 복구 시뮬레이션 성공 기록
- 검증: `docs/ops/runbook-db-backup-restore.md` 실행 로그

#### G4-4 (A) 롤백 절차
- 무중단 롤백 또는 N분 이내 롤백 가능
- 마이그레이션이 backwards-compatible 한 단계로 작성됨
- 검증: 스테이징에서 롤백 시뮬레이션 통과

#### G4-5 (D) On-call 등록
- 모듈 오너 + 백업이 PagerDuty/Slack 알림 그룹에 등록
- 사고 분류·심각도 매핑 문서화

### 6.5 영역 5 — 사용자 가치 (User Value, 3게이트)

#### G5-1 (D) 사용자 매뉴얼
- `docs/user-manual/<module>.md` 또는 in-app help 존재
- 핵심 시나리오 5개 이상의 step-by-step

#### G5-2 (D) 튜토리얼/온보딩
- `docs/tutorials/<module>.md`에 30분 이내 완수 가능한 튜토리얼

#### G5-3 (M) UAT 통과
- 외부 또는 내부 도메인 전문가 1인 이상의 UAT 완료
- UAT 시나리오 통과율 ≥ 95%

## 7. 라벨링 정책

게이트 통과 상태에 따라 모듈에 다음 라벨을 부여한다. 라벨은
`docs/generated/commercial-status.md` (자동 생성)에 집계한다.

| 라벨 | 정의 |
|------|------|
| `commercial-ready` | 23/23 통과. SLA 약속 가능. |
| `pre-commercial` | 18/23 이상 통과 + G3 영역(보안) 5/5 통과. 사내·파일럿 도입 가능. |
| `beta` | 12/23 이상 통과. UI/기능 시연 가능, 데이터 손실 없음. |
| `alpha` | 그 외. 내부 개발/실험 한정. |

라벨은 모듈 README, OpenAPI `info.x-status`, 관리자 대시보드에 노출.

## 8. 실행 항목(Action Items)

- [ ] 인프라팀 — 게이트 자동 점검 스크립트 골격(`scripts/audit/commercial-readiness.py`) 작성 — 2026-04-30 — phase: P-001
- [ ] 인프라팀 — `docs/generated/commercial-status.md` 자동 생성 파이프라인 — 2026-05-15 — phase: P-002
- [ ] 아키텍처 위원회 — ADR-0002~0012 본 ADR과 정합 확인 — 2026-04-30
- [ ] 모든 모듈 오너 — ADR-0002 웨이브 분류표 검토·확정 — 2026-04-20

## 9. 검증(Verification)

- [ ] CI에 `commercial-readiness.py` 결과가 PR 코멘트로 게시됨
- [ ] 분기 회고에서 라벨 분포 검토
- [ ] 6개월 시점에 측정 지표(§5.4) 재측정

## 10. 부록 A — ISO 25010 매핑

| ISO 25010 특성 | 본 ADR 게이트 |
|----------------|---------------|
| Functional Suitability | G1-1 ~ G1-5 |
| Performance Efficiency | G2-1 ~ G2-3 |
| Compatibility | G2-5(i18n), G7(추후 ADR) |
| Usability | G5-1 ~ G5-3 |
| Reliability | G2-4, G4-3, G4-4 |
| Security | G3-1 ~ G3-5 |
| Maintainability | G1-4(테스트), G4-2(runbook) |
| Portability | G2-5, G4-4 |

## 11. 부록 B — 게이트 통과 기록 양식

각 모듈은 `docs/governance/commercial/<module>.md`에 다음 양식으로 기록.

```markdown
# <module> 상용화 게이트 기록

| 게이트 | 상태 | 증거 | 최근 검증일 | 검증자 |
|--------|------|------|-------------|--------|
| G1-1 | ✅/❌/⚠️ | 링크/커밋 | YYYY-MM-DD | @user |
| ... | | | | |

## 라벨 이력
- YYYY-MM-DD: alpha → beta (G1-1~G1-5, G3 통과)
- YYYY-MM-DD: beta → pre-commercial
- YYYY-MM-DD: pre-commercial → commercial-ready
```

## 12. 참고 자료

- `docs/infra/ops/slo.md`
- `docs/engineering/ci/test-strategy.md`
- `docs/engineering/architecture/api-standards.md`
- `docs/engineering/architecture/authz.md`
- `docs/engineering/architecture/multitenancy.md`
- `docs/engineering/data/audit-log-spec.md`
- `docs/engineering/data/perf-benchmarks.md`
- `docs/infra/ops/observability.md`, `rollback.md`, `backup-restore.md`
- ISO/IEC 25010:2011 — Software product quality model
- Google SRE Book — Service Level Objectives
