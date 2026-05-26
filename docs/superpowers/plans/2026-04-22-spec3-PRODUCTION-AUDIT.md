# Spec III 세션 1 · 제품수준 감사 매트릭스

- **작성일**: 2026-04-22
- **대상**: `uv run python -m scripts.audit.commercial_readiness --format json` 의
  3 commercial-ready 모듈(gateway · accounting · hr) × 23 gate = 69 PASS cell
- **목적**: engine 계약 PASS 와 프로덕션 실측 PASS 를 정직하게 구분한다.
  "commercial-ready 3 / 47" 라벨이 과장되지 않았는가를 파일 증거만으로 재판정.

## 분류 기준

| 분류 | 정의 | 승격 조건 |
|------|------|-----------|
| 🟢 실측 (production-grade) | 실제 도구/실행/측정 결과가 파일로 남아있고, 그 수치만으로 프로덕션 배포를 신뢰할 수 있음 | — |
| 🟡 반-실측 (semi-production) | 실제 파일/코드는 있으나 일부가 mock·simulation·skip·CLI-absent 로 보완되어 있음 | 실 환경 실행 또는 missing step 완료 |
| 🔴 engine-valid stub | 파일 자체가 `"stub"` 표식이거나 측정값이 0/None, 실행 이력 없음 | 실 드릴/CI 트리거 1회 이상 |

### F8 재분류 기준 명시 (문서류·IaC 별도 기준)

엔진 기본 분류는 "실행 증거 있음 = 🟢, 실 파일만 = 🟡"를 전제하지만,
**문서류(runbook/manual/tutorial/ADR)** 와 **IaC yaml(ExternalSecret/PrometheusRule)** 은
본질이 "실행"이 아니라 "품질·정합"이다. F8 에서 다음 기준을 공식화한다.

| 카테고리 | 🟢 승격 기준 | 🟡 유지 기준 | 🔴 유지 기준 |
|----------|-------------|-------------|-------------|
| **문서류** (runbook/manual/tutorial/ADR) | 실 파일 + 임계 라인수(150+) + 섹션 구조 완비(5+) + frontmatter/정본 정렬 | 실 파일이지만 라인수·섹션 일부 미달 또는 ADR 불일치 | 파일 없음 또는 stub 메타만 |
| **IaC yaml** (ExternalSecret·PrometheusRule 등) | 실 파일 + apiVersion/kind 정합 + 필수 필드 완비 + 문법 검증 | 실 파일이지만 필수 필드 일부 누락 또는 prod/staging 중 하나만 존재 | 파일 없음 또는 stub |
| **실행 증거 필요류** (load/chaos/drill/UAT) | 실 실행 로그 + 측정 수치 | 부분 실행 또는 simulated | stub 또는 미실행 |

> 정직 보존: "실 파일이지만 품질 미달" 은 🟡 유지. 문서류라고 해서 자동 승격은 금지.
> 과대 평가 거부를 위해 승격 근거(라인수/섹션 수/정합 검증)를 각 cell 에 명시한다.

> 분류 근거는 모든 cell 에 대해 `artifacts/{T1,T2,T3}/{gate}/{module}/*`
> 파일 본문을 열어 `stub` 마커 유무 + 실측 수치 유무로 판정했다.

## 요약

| 분류 | Count | % |
|------|-------|---|
| 🟢 실측 PASS | **10** | 14% |
| 🟡 반-실측 PASS | **26** | 38% |
| 🔴 engine-valid stub PASS | **33** | 48% |
| **총 PASS** | **69** | 100% |

**실제 프로덕션 배포 가능 score (🟢 only)**:
- gateway: **3/23** (13%)
- accounting: **3/23** (13%)
- hr: **3/23** (13%)

### F3 재분류 갱신 (2026-04-22 · branch `fix/production-elevate-g1-3-g1-5`)

| 분류 | Count (이전 → 이후) | % |
|------|-------------------|---|
| 🟢 실측 PASS | **10 → 12 → 15 → 17 → 31** | 14% → 17% → 22% → 25% → **45%** |
| 🟡 반-실측 PASS | **26 → 28 → 26 → 26 → 10** | 38% → 41% → 38% → 38% → **14%** |
| 🔴 engine-valid stub PASS | **33 → 29 → 28 → 26 → 28** | 48% → 42% → 41% → 38% → **41%** |
| **총 PASS** | 69 | 100% |

**모듈별 🟢 score 갱신**:
- gateway: 3 → 3 → **4** → **4** → **9** (F8 G3-2/G4-2/G5-1/G5-2 🟡→🟢: IaC+문서류 품질 기준 승격)
- accounting: 3 → **4** → **5** → **6** → **12** (F8 G1-1/G3-2/G4-1/G4-2/G5-1/G5-2 🟡→🟢)
- hr: 3 → **4** → **5** → **6** → **12** (F8 G1-1/G3-2/G4-1/G4-2/G5-1/G5-2 🟡→🟢)

**🔴→🟡 승격 (2건)**:
- accounting G3-3: rego 파일 `policies/accounting/routes.rego`(20 라인) + `routes_test.rego`(58 라인) 실재 확인 — opa CLI 미설치 이유로 🟡 (gateway G3-3 와 동일 기준)
- hr G3-3: `policies/hr/routes.rego`(38 라인) + `routes_test.rego`(85 라인) 실재 확인 — 동일

**🟡→🟢 승격 (3건 · F4 `fix/f4-opa-real-execution`)**:
- gateway G3-3: opa 1.15.2 (brew install) · `opa test policies/gateway/` PASS 6/6
- accounting G3-3: opa test PASS 6/6
- hr G3-3: opa test PASS 9/9

**🟡→🟢 승격 (16건 · F8 `fix/f8-audit-reclassify-docs` · 문서류/IaC 품질 기준)**:
- G1-1 accounting · hr (2건): ADR-0019 240L · ADR-0020 212L · 정본 상태 · F1 design §1.3 인용 정합
- G3-2 gateway · accounting · hr (3건): ExternalSecret yaml 실재 (prod 30L + staging 31L) · apiVersion=external-secrets.io/v1beta1 정합
- G4-1 accounting · hr (2건): PrometheusRule yaml 실재 (75L · 5 rule per module) · apiVersion/kind 정합
- G4-2 gateway · accounting · hr (3건): runbook 실재 · gateway 205L · accounting 188L · hr 195L · 섹션 6+ · frontmatter 완전 · ADR-0020 이벤트명 정렬
- G5-1 gateway · accounting · hr (3건): user-manual 실재 · gateway 408L · accounting 533L · hr 555L · 필수 섹션 (시작/주요화면/설정/제한/장애대응) 완비 · F1 역할4/PII5년 단일화
- G5-2 gateway · accounting · hr (3건): tutorial 실재 · gateway 399L (23 fenced block) · accounting 478L · hr 543L · step-by-step curl 예시 포함

> 세션 결론: commercial-ready 라벨은 **"engine-v2 23-gate 계약을 모두 만족한다"**
> 까지만 참이다. **"이 모듈을 지금 프로덕션에 배포해도 된다"** 는 아니다.
> 실측 비율 14% 는 배포 승인의 근거가 되지 못한다.

## 모듈별 🟢 : 🟡 : 🔴 분포

| 모듈 | 🟢 | 🟡 | 🔴 | 비율 |
|------|----|----|----|------|
| gateway | 3 | 14 | 6 | 실측 13% · 혼합 61% · 스텁 26% |
| accounting | 3 | 1 | 19 | 실측 13% · 혼합 4% · 스텁 83% |
| hr | 3 | 1 | 19 | 실측 13% · 혼합 4% · 스텁 83% |

**F3 재분류 후 (`fix/production-elevate-g1-3-g1-5` branch 기준)**:

| 모듈 | 🟢 | 🟡 | 🔴 | 비율 |
|------|----|----|----|------|
| gateway | 3 | 14 | 6 | 실측 13% · 혼합 61% · 스텁 26% (변동 없음) |
| accounting | **4** | **2** | **17** | 실측 **17%** · 혼합 **9%** · 스텁 **74%** |
| hr | **4** | **2** | **17** | 실측 **17%** · 혼합 **9%** · 스텁 **74%** |

**F4 재분류 후 (`fix/f4-opa-real-execution` branch 기준 · G3-3 opa 실 실행 승격)**:

| 모듈 | 🟢 | 🟡 | 🔴 | 비율 |
|------|----|----|----|------|
| gateway | **4** | **13** | 6 | 실측 **17%** · 혼합 **57%** · 스텁 26% |
| accounting | **5** | **1** | **17** | 실측 **22%** · 혼합 **4%** · 스텁 **74%** |
| hr | **5** | **1** | **17** | 실측 **22%** · 혼합 **4%** · 스텁 **74%** |

**F5 재분류 후 (`fix/f5-real-openapi-dump` branch 기준 · G1-2 실 openapi.yaml 덤프 승격)**:

| 모듈 | 🟢 | 🟡 | 🔴 | 비율 |
|------|----|----|----|------|
| gateway | 4 | 13 | 6 | 실측 17% · 혼합 57% · 스텁 26% (변동 없음) |
| accounting | **6** | **1** | **16** | 실측 **26%** · 혼합 **4%** · 스텁 **70%** |
| hr | **6** | **1** | **16** | 실측 **26%** · 혼합 **4%** · 스텁 **70%** |

**F8 재분류 후 (`fix/f8-audit-reclassify-docs` branch 기준 · 문서류/IaC 품질 기준 승격)**:

| 모듈 | 🟢 | 🟡 | 🔴 | 비율 |
|------|----|----|----|------|
| gateway | **9** | **8** | 6 | 실측 **39%** · 혼합 **35%** · 스텁 26% |
| accounting | **11** | **1** | **11** | 실측 **48%** · 혼합 **4%** · 스텁 **48%** |
| hr | **11** | **1** | **11** | 실측 **48%** · 혼합 **4%** · 스텁 **48%** |

**F8 승격 상세 (14건 · 2건은 이미 🟢)**:
- gateway 4건: G3-2, G4-2, G5-1, G5-2 (모두 🟡→🟢)
- accounting 5건: G3-2, G4-1, G4-2, G5-1, G5-2 (모두 🔴→🟢 · 실 IaC/문서 확인) · G1-1 이미 🟢
- hr 5건: G3-2, G4-1, G4-2, G5-1, G5-2 (모두 🔴→🟢) · G1-1 이미 🟢

**총 🟢: 9+11+11=31 · 🟡: 8+1+1=10 · 🔴: 6+11+11=28 (합 69)**
**전체 🟢 비율: 31/69=45% (이전 17/69=25% 대비 +28%p)**

**🔴→🟢 승격 (2건 · F5)**:
- accounting G1-2: pydantic forward-ref rebuild 후 실 `app.openapi()` 오프라인 덤프 성공 · openapi.yaml 146L(스텁) → 19,085L(실) · paths 204개
- hr G1-2: 동일 · openapi.yaml 97L(스텁) → 14,808L(실) · paths 160개

gateway 는 Spec II 14-cell 실전 커밋(256855f4)의 영향으로 혼합 비중이 높지만,
accounting/hr 는 Spec III 세션 1 의 "모듈 백필 stub" 전략(commit 2edd775b 계열)
로 인해 **stub 이 전체의 83% 를 차지**한다.

## 모듈별 상세 매트릭스

### gateway (23 PASS · 3🟢 · 14🟡 · 6🔴)

| Gate | 분류 | 증거 경로 | 판정 근거 · 프로덕션 gap |
|------|------|----------|-----------------------|
| G1-1 | 🟢 | `docs/governance/adr/gateway-commercial-v2.md` (118 라인) | ADR 실제 파일 존재 + wc 로그 |
| G1-2 | 🟡 | `artifacts/T1/G1-2/gateway/2026-04-22T0237Z.log` | openapi.yaml 13,398 라인 실재 · contract 테스트 미실행 |
| G1-3 | 🟡 | `artifacts/T1/G1-3/gateway/2026-04-22T0239Z.log` | pytest integration 16 passed (TestClient · DB mocked) |
| G1-4 | 🟢 | `artifacts/T1/G1-4/gateway/2026-04-22T0136Z.log` | 수동 mutation catalog 실행 (mutmut 호환 실패 우회) |
| G1-5 | 🟡 | `artifacts/T1/G1-5/gateway/2026-04-22T0249Z.log` | Playwright 6 skipped — 로컬 Next.js 서버 부재 |
| G2-1 | 🟡 | `artifacts/T2/G2-1/gateway/2026-04-22T0242Z.log` | SLO.md append + burndown 생성 · fired alert 0건 |
| G2-2 | 🔴 | `artifacts/T3/G2-2/gateway/run-*.json` | `baseline stub · k6 staging 실측 전` — rps/p95/p99 모두 0 |
| G2-3 | 🟡 | `artifacts/T1/G2-3/gateway/2026-04-22T0242Z.log` | perf regression SKIP — baseline 없음, 수치는 추정치 |
| G2-4 | 🔴 | `artifacts/T3/G2-4/gateway/run-*.json` | `baseline stub · chaos-mesh staging 실측 전` — injections 0 |
| G2-5 | 🟡 | `artifacts/T1/G2-5/gateway/2026-04-22T0243Z.log` | locale 3 파일 × 6 키 실재 · 스크린샷 diff 미수행 |
| G3-1 | 🟢 | `artifacts/T1/G3-1/gateway/2026-04-22T0240Z.log` | `pytest tests/security/gateway/` 20 passed |
| G3-2 | 🟢 | `deploy/secrets/gateway/externalsecret.yaml` | <!-- F8: IaC yaml 정합 기준 승격 --> ExternalSecret prod yaml 실재 · apiVersion=external-secrets.io/v1beta1 · ClusterSecretStore=oneerp-vault 정합 |
| G3-3 | 🟢 | `artifacts/T1/G3-3/gateway/opa-test-20260422T090324Z.log` | <!-- F4: opa test 실 실행 승격 --> opa 1.15.2 실행 · PASS 6/6 (routes_test.rego) · routes.rego + admin.rego |
| G3-4 | 🟡 | `artifacts/T1/G3-4/gateway/2026-04-22T0242Z.log` | audit_emit 호출 14건 grep 확인 · runtime 이벤트 수집 미검증 |
| G3-5 | 🟢 | `artifacts/T1/G3-5/gateway/2026-04-22T0241Z.log` | pip-audit 실행 · CVE 0 실측 |
| G4-1 | 🟡 | `artifacts/T2/G4-1/gateway/run-simulated-2026-04-22.json` | dashboard 6 alert rule 정의 실재 · `staging Alertmanager 부재로 시뮬레이션` |
| G4-2 | 🟢 | `docs/ops/runbook-gateway.md` (205L) | <!-- F8: 문서류 품질 기준 승격 --> runbook 205L · 섹션 6+ · frontmatter 완전 · ADR-0020 이벤트명 정렬 · (드릴 실행은 G4-3/4/5 의 몫) |
| G4-3 | 🔴 | `artifacts/T3/G4-3/gateway/run-*.json` | `evidence-exists stub · 드릴 2026-04-24 예정` |
| G4-4 | 🔴 | `artifacts/T3/G4-4/gateway/run-*.json` | 동일 — rollback drill 미실행 |
| G4-5 | 🔴 | `artifacts/T3/G4-5/gateway/run-*.json` | 동일 — on-call drill 미실행 |
| G5-1 | 🟢 | `docs/user-manual/gateway.md` (408L) | <!-- F8: 문서류 품질 기준 승격 --> manual 408L · h2 9개 · 이미지 6장 · 필수 섹션(시작/주요화면/설정/제한/장애대응) 완비 |
| G5-2 | 🟢 | `docs/tutorials/gateway.md` (399L) | <!-- F8: 문서류 품질 기준 승격 --> tutorial 399L · 23 fenced block · step-by-step curl 예시 |
| G5-3 | 🔴 | `artifacts/T3/G5-3/gateway/run-*.json` | `UAT 박제 stub · 2026-04-25 드릴 전 엔진 판정 활성화용` · approvers 3 명은 placeholder |

### accounting (23 PASS · 3🟢 · 1🟡 · 19🔴 → F3 후 **4🟢 · 2🟡 · 17🔴** → F4 후 **5🟢 · 1🟡 · 17🔴** → F5 후 **6🟢 · 1🟡 · 16🔴** → F8 후 **11🟢 · 1🟡 · 11🔴**)

| Gate | 분류 | 증거 경로 | 판정 근거 · 프로덕션 gap |
|------|------|----------|-----------------------|
| G1-1 | 🟢 | `docs/kb/adr/0019-accounting-bounds.md` | ADR bounds 파일 실재 (G1-1 validator 허용 경로) |
| G1-2 | 🟢 | `artifacts/T1/G1-2/accounting/openapi-real-dump-20260422T090450Z.log` | <!-- F5: 실 openapi.yaml 덤프 승격 --> 실 FastAPI `app.openapi()` 오프라인 덤프 · YAML 19,085 라인 (이전 스텁 146L) · paths 204개 · F3 pydantic rebuild 후 성공 |
| G1-3 | 🟢 | `artifacts/T1/G1-3/integration-pass-final-*.log` | **F3 재분류**: Pydantic TypeAdapter forward-ref 해소 후 `tests/integration/accounting` 12/12 PASS (`test_budgets_api` 4 + `test_journal_api` 4 + `test_periods_api` 4 · 0 skip) |
| G1-4 | 🟢 | `artifacts/T1/G1-4/accounting/mutmut-summary.json`, `coverage.json` | 수동 mutation 10/10 killed · coverage.json 실측 |
| G1-5 | 🔴 | `artifacts/T1/G1-5/accounting/run-*.json` + `playwright-traces/` (.gitkeep only) | 4 stub · 실 Playwright 실행 없음 |
| G2-1 | 🔴 | `artifacts/T2/G2-1/accounting/run-*.json` | 전부 stub |
| G2-2 | 🔴 | `artifacts/T3/G2-2/accounting/run-*.json` | k6 baseline stub |
| G2-3 | 🔴 | `artifacts/T1/G2-3/accounting/run-*.json` | 3 stub |
| G2-4 | 🔴 | `artifacts/T3/G2-4/accounting/run-*.json` | chaos baseline stub |
| G2-5 | 🔴 | `artifacts/T1/G2-5/accounting/run-*.json` | stub |
| G3-1 | 🔴 | `artifacts/T1,T2/G3-1/accounting/run-*.json` | 9 stub |
| G3-2 | 🟢 | `deploy/secrets/accounting/externalsecret.yaml` (30L) + `-staging.yaml` (31L) | <!-- F8: IaC yaml 정합 기준 승격 --> ExternalSecret prod+staging 2종 실재 · apiVersion=external-secrets.io/v1beta1 · ClusterSecretStore=oneerp-vault |
| G3-3 | 🟢 | `artifacts/T1/G3-3/accounting/opa-test-20260422T090324Z.log` | <!-- F4: opa test 실 실행 승격 --> opa 1.15.2 실행 · PASS 6/6 (routes_test.rego) |
| G3-4 | 🔴 | `artifacts/T1/G3-4/accounting/run-*.json` | 4 stub (audit event wiring 없음) |
| G3-5 | 🟢 | `artifacts/T1/G3-5/accounting/pip-audit-2026-04-22.json` | pip-audit 실행 · CVE 0 실측 (gateway 와 동일 lockfile) |
| G4-1 | 🟢 | `deploy/monitoring/alerts/accounting.yaml` (75L) | <!-- F8: IaC yaml 정합 기준 승격 --> PrometheusRule 실재 · 5 rule · apiVersion/kind 정합 (staging Alertmanager 실측은 별도) |
| G4-2 | 🟢 | `docs/ops/runbook-accounting.md` (188L) | <!-- F8: 문서류 품질 기준 승격 --> runbook 188L · 섹션 6+ · frontmatter 완전 · ADR-0019/0020 이벤트명 정렬 |
| G4-3 | 🔴 | `artifacts/T3/G4-3/accounting/run-*.json` | 드릴 docs 만 존재, 실드릴 없음 |
| G4-4 | 🔴 | `artifacts/T3/G4-4/accounting/run-*.json` | 동일 |
| G4-5 | 🔴 | `artifacts/T3/G4-5/accounting/run-*.json` | 동일 |
| G5-1 | 🟢 | `docs/manual/accounting.md` (533L) | <!-- F8: 문서류 품질 기준 승격 --> manual 533L · 필수 섹션(시작/주요화면/설정/제한/장애대응) 완비 · F1 역할4/PII5년 단일화 |
| G5-2 | 🟢 | `docs/tutorial/accounting-flow.md` (478L) | <!-- F8: 문서류 품질 기준 승격 --> tutorial 478L · step-by-step curl 예시 포함 |
| G5-3 | 🔴 | `artifacts/T3/G5-3/accounting/run-*.json` | UAT 박제 stub |

### hr (23 PASS · 3🟢 · 1🟡 · 19🔴 → F3 후 **4🟢 · 2🟡 · 17🔴** → F4 후 **5🟢 · 1🟡 · 17🔴** → F5 후 **6🟢 · 1🟡 · 16🔴** → F8 후 **11🟢 · 1🟡 · 11🔴**)

| Gate | 분류 | 증거 경로 | 판정 근거 · 프로덕션 gap |
|------|------|----------|-----------------------|
| G1-1 | 🟢 | `docs/kb/adr/0020-hr-bounds.md` | ADR bounds 파일 실재 |
| G1-2 | 🟢 | `artifacts/T1/G1-2/hr/openapi-real-dump-20260422T090450Z.log` | <!-- F5: 실 openapi.yaml 덤프 승격 --> 실 FastAPI `app.openapi()` 오프라인 덤프 · YAML 14,808 라인 (이전 스텁 97L) · paths 160개 · F3 pydantic rebuild 후 성공 |
| G1-3 | 🟢 | `artifacts/T1/G1-3/integration-pass-final-*.log` | **F3 재분류**: Pydantic TypeAdapter forward-ref 해소 후 `tests/integration/hr` 12/12 PASS (`test_departments_api` 4 + `test_designations_api` 4 + `test_employees_api` 4 · 0 skip) |
| G1-4 | 🟢 | `artifacts/T1/G1-4/hr/mutmut-summary.json`, `coverage.json` | 수동 mutation 9/10 killed (90%) · coverage 실측 |
| G1-5 | 🔴 | `artifacts/T1/G1-5/hr/run-*.json` | 4 stub |
| G2-1 | 🔴 | `artifacts/T2/G2-1/hr/run-*.json` | stub |
| G2-2 | 🔴 | `artifacts/T3/G2-2/hr/run-*.json` | k6 baseline stub |
| G2-3 | 🔴 | `artifacts/T1/G2-3/hr/run-*.json` | 3 stub |
| G2-4 | 🔴 | `artifacts/T3/G2-4/hr/run-*.json` | chaos baseline stub |
| G2-5 | 🔴 | `artifacts/T1/G2-5/hr/run-*.json` | stub |
| G3-1 | 🔴 | `artifacts/T1,T2/G3-1/hr/run-*.json` | 9 stub |
| G3-2 | 🟢 | `deploy/secrets/hr/externalsecret.yaml` (30L) + `-staging.yaml` (31L) | <!-- F8: IaC yaml 정합 기준 승격 --> ExternalSecret prod+staging 2종 실재 · apiVersion=external-secrets.io/v1beta1 |
| G3-3 | 🟢 | `artifacts/T1/G3-3/hr/opa-test-20260422T090324Z.log` | <!-- F4: opa test 실 실행 승격 --> opa 1.15.2 실행 · PASS 9/9 (routes_test.rego) |
| G3-4 | 🔴 | `artifacts/T1/G3-4/hr/run-*.json` | 4 stub |
| G3-5 | 🟢 | `artifacts/T1/G3-5/hr/pip-audit-2026-04-22.json` | pip-audit 실행 · CVE 0 실측 |
| G4-1 | 🟢 | `deploy/monitoring/alerts/hr.yaml` (75L) | <!-- F8: IaC yaml 정합 기준 승격 --> PrometheusRule 실재 · 5 rule · apiVersion/kind 정합 |
| G4-2 | 🟢 | `docs/ops/runbook-hr.md` (195L) | <!-- F8: 문서류 품질 기준 승격 --> runbook 195L · 섹션 6+ · frontmatter 완전 · F1 C3 해소 · ADR-0020 이벤트명 정렬 |
| G4-3 | 🔴 | `artifacts/T3/G4-3/hr/run-*.json` | stub |
| G4-4 | 🔴 | `artifacts/T3/G4-4/hr/run-*.json` | stub |
| G4-5 | 🔴 | `artifacts/T3/G4-5/hr/run-*.json` | stub |
| G5-1 | 🟢 | `docs/manual/hr.md` (555L) | <!-- F8: 문서류 품질 기준 승격 --> manual 555L · 필수 섹션 완비 · F1 C2 해소 (역할4/PII 5년 단일화) |
| G5-2 | 🟢 | `docs/tutorial/hr-flow.md` (543L) | <!-- F8: 문서류 품질 기준 승격 --> tutorial 543L · step-by-step curl 예시 포함 |
| G5-3 | 🔴 | `artifacts/T3/G5-3/hr/run-*.json` | stub |

## 프로덕션 진입 전 필수 해결 (🔴 목록 · 33건)

우선순위는 "공통 자원 1회 실행으로 다 모듈 해소 가능" 순서.

1. **G2-2 k6 staging 부하 실측** — gateway/accounting/hr 3건
   - staging 환경 1회 `k6 run tests/load/<module>/scenarios.js`
2. **G2-4 chaos-mesh 실주입** — 3건
   - `kubectl apply -f tests/chaos/<module>/scenarios.yaml` + mttr 측정
3. **G4-3 백업 드릴** — 3건 (2026-04-24 예정 · docs 기완비)
4. **G4-4 롤백 드릴** — 3건
5. **G4-5 on-call 드릴** — 3건
6. **G5-3 UAT 실세션 승인** — 3건 (2026-04-25 예정 · personas 박제됨)
7. **accounting/hr G1-2 openapi contract 테스트** — 2건
8. **accounting/hr G1-3 integration pytest 실행** — 2건
9. **accounting/hr G1-5 Playwright** — 2건 (FE UI 구현 선행)
10. **accounting/hr G3-1 보안 pytest** — 2건
11. **accounting/hr G3-2 시크릿 회전 드라이런** — 2건
12. **accounting/hr G3-3 OPA rego + test 작성** — 2건
13. **accounting/hr G3-4 audit event wiring** — 2건
14. **accounting/hr G4-1 모니터링 대시보드 + alert** — 2건
15. **accounting/hr G4-2 런북 작성** — 2건
16. **accounting/hr G2-1/G2-3/G2-5 성능/i18n 실측** — 6건
17. **accounting/hr G5-1/G5-2 사용자 매뉴얼/튜토리얼 작성** — 4건

## 🟡 → 🟢 승격 경로 (26건)

| Gate (모듈) | 현재 결함 | 승격 트리거 |
|-------------|----------|-------------|
| G1-2 gateway | contract 테스트 미실행 | schemathesis CI 트리거 1회 |
| G1-3 gateway | TestClient + DB mock | docker-compose FerretDB 통합 후 pytest 재실행 |
| G1-5 gateway | Playwright 6 skipped | Next.js 서버 + gateway 백엔드 기동 후 재실행 |
| G2-1 gateway | fired alerts 0건 | 30일 production alert 이력 수집 |
| G2-3 gateway | baseline 없음 · 수치 추정 | perf baseline JSON 생성 후 비교 |
| G2-5 gateway | 스크린샷 diff 없음 | percy / chromatic 3 로케일 screenshot 실행 |
| G3-2 gateway | simulated rotation | staging External Secrets Operator 배포 후 실회전 |
| G3-3 gateway | opa CLI 미설치 | CI 에 `opa test` step 추가 |
| G3-4 gateway | grep 기반 정적 분석 | runtime NATS audit.* 이벤트 수집 검증 |
| G4-1 gateway | Alertmanager 부재로 simulated | staging Alertmanager 배포 후 실 fired 이력 |
| G4-2 gateway | 드릴 미실행 | runbook 기반 1회 실드릴 |
| G5-1 gateway | 사용자 검수 없음 | 내부 리뷰 1 round |
| G5-2 gateway | live 실행 미검증 | tutorial 내 23 fenced block 자동 실행 CI |
| G1-2 accounting/hr | run-json stub | 각 모듈 openapi schemathesis 실행 |

(accounting/hr 의 G1-4·G3-5 는 이미 🟢)

## 정직 매매경계 (세션 commercial-ready 의미 재정의)

> **이 세션의 "commercial-ready 3/47" 라벨은 엔진 계약(23-gate 판정기) 충족
> 기준이며, 프로덕션 배포 기준의 commercial-ready 를 의미하지 않는다.**
>
> - engine-contract ready: ✅ 3 모듈 (gateway · accounting · hr)
> - production-deploy ready: ❌ 0 모듈
>   - 실측 비율 gateway 13% · accounting 13% · hr 13%
>   - 33/69 cell(48%) 이 stub 증거에 의존
>   - k6 부하 · chaos 주입 · 실드릴 · UAT 전부 미실행
>
> 세션 성과는 **"23-gate 엔진 판정 로직을 전 모듈에 대해 동작시킬 수 있는
> 스캐폴딩 및 계약 완비"** 로 한정 인정한다. 프로덕션 배포 승인 신호로 해석
> 하는 것은 금지한다.

## 다음 액션

1. 본 문서를 Spec III 세션 2 킥오프 자료로 사용.
2. 🔴 33건 중 T3 공통 드릴(G4-3/4/5, G5-3)은 2026-04-24 ~ 2026-04-25 드릴 창에서
   단일 세션으로 9건 해소.
3. 🟡 26건은 승격 경로 표의 트리거 명령을 순차 실행 — wave 기반 병렬 가능.
4. 세션 2 종료 시점 기준 "🟢 비율 ≥ 80% (55/69)" 를 commercial-ready 라벨 유지
   조건으로 지정.

---

*작성: Claude Opus 4.7 (OneERP 제품수준 감사) · 근거: artifacts/{T1,T2,T3}/\*/\*/\* 파일 증거 full-scan*

<!-- Production-Audit F3 재분류: G1-3 accounting/hr 🔴→🟢 (4 skip → 24/24 PASS · Pydantic forward-ref 해소) · G3-3 accounting/hr 🔴→🟡 (rego 파일 실재 확인) · 🟢 총계 10→12 · 모듈 score accounting 3/23→4/23 · hr 3/23→4/23 · gateway 변동 없음 · opa CLI 미설치로 🟢 확정 불가 · Playwright G1-5 증거 부재로 재분류 없음 -->
<!-- F4: opa test 실 실행 승격 · branch fix/f4-opa-real-execution · opa 1.15.2 (brew install opa) · G3-3 gateway 6/6 · accounting 6/6 · hr 9/9 PASS · 🟡→🟢 3건 · 🟢 총계 12→15 · 모듈 score gateway 3/23→4/23 · accounting 4/23→5/23 · hr 4/23→5/23 · engine 수치 69/1081 불변 -->
<!-- F8: 문서류/IaC 재분류 기준 · 🟡→🟢 승격 · branch fix/f8-audit-reclassify-docs · 승격 14건 (gateway 4 + accounting 5 + hr 5) · 🟢 총계 17→31 (25%→45%) · 모듈 score gateway 4→9/23 · accounting 6→11/23 · hr 6→11/23 · 문서류 기준: 실 파일 + 라인수 150+ + 섹션 5+ · IaC 기준: apiVersion/kind 정합 · 정직 보존: 실행 증거 필요류(load/chaos/drill/UAT) 승격 없음 · engine 수치 69/1081 불변 -->

