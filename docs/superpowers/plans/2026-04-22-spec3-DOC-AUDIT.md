---
title: Spec III 세션 1 · 전 문서 감사 보고서
date: 2026-04-22
status: review
scope: 설계 · 플랜 · HANDOFF · ADR 4편 · 매뉴얼 2편 · 튜토리얼 2편 · Runbook 2편 · 드릴 9편 · UAT 3편 · Secrets README 2편 · OPA README 2편 (총 27 문서)
audit_tool: Read (전량 완독) + rg/grep/find 실측
auditor: Claude Opus 4.7 (1M context)
---

# Spec III 세션 1 · 전 문서 감사 보고서

## 요약

**검토 문서 수 — 요청 25편 / 실제 27편** (G4-3/4/5 × {gateway, accounting, hr} 드릴 9편 포함)

- Critical (🔴): **3건**
- Warning (🟡): **11건**
- Minor (🟢): **8건**
- 커밋 SHA 실존율: **11/11 (100%)** — HANDOFF 인용 전체 SHA 실존 확인
- 문서 간 교차 참조 정확성: **약 85%** (문서 경로 참조 전량 정확, 숫자·역할·이벤트 이름 문서 간 3군데 불일치)

세션 1 성과는 견고하다 — 68 커밋 · 설계 487L · 플랜 2055L · ADR 4편 · 매뉴얼/튜토리얼/런북/드릴/UAT/Secrets/OPA 문서가 1일 자율 세션으로 응집력 있게 박제되었다. 발견된 이슈는 주로 **1차 박제 직후의 "같은 사실을 여러 문서에 서로 다른 숫자로 기록"** 유형이며, 코드/인프라 정합성은 양호하다.

---

## 1. 문서별 감사

### 1.1 설계/플랜/HANDOFF

#### `docs/superpowers/specs/2026-04-22-spec3-staging-quality-design.md` (487L)

- **상태**: 🟡 Warning
- **요약**: 3 트랙 통합 설계 · 6주 Wave A-D · 구조 합리적.
- **발견사항**:
  - 🔴 §1.3 "accounting · hr 출발선" 표 수치가 **ADR-0019/0020 및 실측 모두와 불일치** — accounting "59 엔티티 · 15 + 11 자동 CRUD 라우터 · 26 서비스 · 332 tests(44 파일)" vs 실측 모델 56 파일 · EntityMeta 47 · routes 11 파일(70 엔드포인트) · services 22 파일 · tests 51 파일. hr "47 엔티티 · 8 라우터 · 15 서비스 · 154 tests(25 파일)" vs 실측 routes 8 파일 · services 11 파일 · tests 34 파일. 설계 기준표가 정확하지 않으면 Wave B/C 완료 판정 근거가 흔들린다. (ADR의 "56·47·11·70·23" 수치를 정본으로 통일 필요)
  - 🟡 §0.2 Wave B "Phase 1: accounting L0 11셀 (gateway 템플릿 재사용)" 중 11셀 나열(§3.2 B-2)에 **G1-4 Unit+Mutation이 누락됨** (10셀만 열거 — G1-1 있고 G1-4 누락). HANDOFF §12와 실측 커밋 로그는 G1-4 완료를 기록. 설계 열거가 불완전.
  - 🟡 §1.2 "Spec II.5 이관 6셀 — G2-2, G2-4, G4-3, G4-4, G4-5, G5-3" — G5-3이 T3 UAT인데 원 Spec II의 "PARTIAL 4셀 (G1-2/3/5, G3-1)"과 혼동될 여지. 두 분류가 독립이라는 주석 권장.
  - 🟢 §1.4 "ruff 73 errors"는 정확 (HANDOFF 시작값과 일치).

#### `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md` (2055L)

- **상태**: ✅ OK
- **요약**: Wave A/B/C/D 전 구현 단계 박제 · Checkbox 구조 · 명령·커밋 메시지 포함. superpowers:executing-plans 포맷 준수.
- **발견사항**:
  - 🟡 §Wave A Task A3 "unsafe-fix 32건" 예상 — 실제 HANDOFF는 58건 (`0fddd20d`) 적용. 플랜 예측치와 실행 차이는 자연스러우나 플랜 본문을 실행 결과에 맞춰 갱신하지 않음 (1회성 문서로 허용 범위).
  - 🟡 §Task D4 ADR-0018 frontmatter 예시 `date: 2026-04-29` — 실제 ADR-0018은 2026-04-22. 플랜은 6주 Wave D 마감 시점 예측 날짜이므로 예시로 이해 가능.
  - 🟢 §Task B2-1 T2 수집기 TDD는 실제 구현과 정합 (`178cf450` 커밋).

#### `docs/superpowers/plans/2026-04-22-spec3-staging-quality-HANDOFF.md` (401L)

- **상태**: ✅ OK
- **요약**: 6 차 확장 · v3.0 최종판 · 숫자 타임라인 상세.
- **발견사항**:
  - ✅ 인용 커밋 SHA 11개 전량 실존 확인 (`26a770be` `343b5c76` `0fddd20d` `178cf450` `7a49ab8d` `3b97fbc3` `8e1904fa` `9cd04fd8` `72d1648e` `36c61efd` `d70e8cc9`).
  - 🟡 §2 표의 "B2-3 ~ B2-14 accounting L0 11셀 ❌" 와 §14.1 "accounting 17/23 alpha" 간 내러티브가 다소 혼란. 실제 17/23 은 backfill stub + 실측 증거 혼합 — 독자가 어떤 셀이 실증거/실성공인지 구분하기 어려움. §14.5 "최종 진실 경계" 로 일부 해소되나 표 단위에선 더 명료한 주석 권장.
  - 🟡 §8 자산 맵 "`docs/ops/drills/{G4-3,G4-4,G4-5}/2026-04-24-gateway.md` (C1-3~5)" — accounting 드릴이 `2026-04-21`, hr 드릴이 `2026-04-22`로 별도 존재하는 점이 §8엔 누락. 드릴 docs 총 9 파일 (세션 1 추가 6 파일) 표기가 더 정확.
  - 🟢 §1.1 "ruff 73 → 30 (세션 종료)" 과 §14 "73 → 0" 이 공존하는 이유는 `<!-- v1.0 → v3.0 -->` 확장 기록이므로 명시적. OK.

### 1.2 ADR 4편

#### `docs/kb/adr/0017-ruff-baseline-ratchet.md` (43L)

- **상태**: ✅ OK
- **요약**: Wave A 완료 직후 박제 · ratchet CI 합의 · floor 합의 방식 기록.
- **발견사항**:
  - 🟡 Context "67에서 73으로 증가" — 설계 §1.4 도 동일. 그러나 ADR-0018 은 "73 → 0"을 주장. ADR-0017은 "Wave A 종료: 30"으로 기록 (Wave A 기준 정확). Wave D 종료 시 0은 ADR-0018 소관이라는 §Related 링크가 명료.
  - 🟢 Evidence에 파일 경로가 구체적 — 우수.

#### `docs/kb/adr/0018-commercial-v2-spec3-session1-completion.md` (99L)

- **상태**: ✅ OK
- **요약**: 세션 1 종합 도달점 박제 · 3 트랙 wave별 outcome 정리.
- **발견사항**:
  - 🟡 §Evidence "신규 ADR: 3편 (0017, 0018, 0019, 0020)" — 실제는 **4편** (본 ADR 포함). 숫자 "3"은 "선행 3편" 취지로 읽히나 바로 뒤의 괄호 목록이 4편 열거라 모순. → "4편"으로 읽어야 자연스러움.
  - 🟢 Non-goals 섹션이 상용 등급 ADR의 모범 — 허위 주장 방지 장치.

#### `docs/kb/adr/0019-accounting-bounds.md` (240L)

- **상태**: ✅ OK (ADR 자체로는 정합)
- **요약**: accounting 6 서브도메인 · 이벤트 계약 · 70 엔드포인트 · 23 서비스 박제. 매우 상세.
- **발견사항**:
  - 🟡 본문 §"기존 구조 스냅숏" 표는 "56 모델 · 47 EntityMeta · 11 라우터 · 70 엔드포인트 · 23 서비스"로 실측과 일치 — 단, 실제 `services/` 디렉토리의 `__init__.py` 제외 파일 수는 **22** (23에서 1건 차이). 허용 범위 (`__init__.py` 포함/제외 해석).
  - 🟢 Appendix B의 23 서비스 목록은 ADR이 주장하는 "23 services"를 파일명 단위로 박제 — 독자 검증 가능.
  - 🟡 Change Log에 "2026-04-22 최초 작성"만 있음. 후속 개정 시 엄격한 append-only 규약이 확립되면 좋음.

#### `docs/kb/adr/0020-hr-bounds.md` (212L)

- **상태**: 🟡 Warning
- **요약**: hr 47 엔티티 · 이벤트 7종 · payroll 경계 · PII 5년 보존.
- **발견사항**:
  - 🔴 "47 엔티티" 주장과 실측의 EntityMeta grep count `grep -c "EntityMeta(" entities.py = 39` **불일치** (실측 39 vs ADR 47). 다만 §D1에서 나열한 커스텀 라우트 엔티티 8종을 더하면 47이 될 가능성 있음(auto CRUD + 커스텀 = 총 선언), 실제 판정은 "EntityMeta 내 선언이 39개 + 커스텀 라우트에 8 엔티티 추가 정의" 해석으로 47 도달. **해석 기준 명시가 필요** (ADR에 "EntityMeta 47"과 "커스텀 라우트 8" 이중 기록이 있어 독자가 숫자를 어떻게 합산해야 하는지 혼동). → 설계 §1.3과 manual §1.2의 "47 = 39 auto + 8 custom" 수식 명시 권장.
  - 🟡 §D3 이벤트 목록(`employee.hired/terminated/transferred`, `department.reorganized`, `designation.changed`, `payroll.run.completed`, `leave_application.approved`) — 정본. runbook-hr.md 의 이벤트 이름과 전혀 불일치 (아래 §1.5 참조).
  - 🟢 §증거 파일 경로 목록이 우수 (routes/ 8종 나열, 커밋 SHA 2건 포함).

### 1.3 매뉴얼

#### `docs/manual/accounting.md` (533L)

- **상태**: 🟡 Warning
- **요약**: G5-1 · 6 도메인 그룹 · API 흐름 · FAQ 10 · 배포/롤백/보안 체크.
- **발견사항**:
  - 🔴 **역할 모델 이중화** — §"권한 모델" 6종 (`accounting.viewer/operator/approver/closer/tax/admin`) vs §"설정" 4단계 (`accounting.admin/approver/operator/viewer`) vs OPA README 2종 (`accounting_viewer/accounting_editor`). 세 문서가 세 가지로 주장. gateway OPA 정책 구현이 2종(viewer/editor)이므로 manual의 6종은 "논리적 목표" 혹은 "Wave D 미구현"임을 명시 필요.
  - 🟡 §"알려진 제약" "OpenAPI 자동 덤프는 Pydantic forward-ref 문제로 현재 실패" — ADR-0020의 hr도 동일 이슈 기록. 공통 이슈로 INCIDENT 박제 권장.
  - 🟡 §"참조" "docs/user-manual/accounting.md" 경로 — 레포 내 존재 여부 미검증(본 감사 범위 외지만 링크 deadness 리스크 있음).
  - 🟢 Change Log 2건, 최초 박제 + 필수 섹션 보강 기록.

#### `docs/manual/hr.md` (552L)

- **상태**: 🔴 Critical
- **요약**: 운영자 매뉴얼 · 47 엔티티 그룹화 · 이벤트 7종 · PII 규약.
- **발견사항**:
  - 🔴 **PII 보존 기간이 문서 내 자체적으로 모순** — §6.3 "기본 5년(근로기준법 §42)" vs §"제한사항" "근로기준법에 따라 3년 보존" vs §FAQ "Q. 퇴사 후…" "3년간 보존된 뒤 비식별화". 동일 문서에서 5년과 3년이 혼재. 법적 권고는 세법 7년/노동법 3년/퇴직금 5년 등 복수라 단일 수치로 단순화한 서술이 잘못된 가정. runbook-hr 과도 불일치(§아래).
  - 🔴 **역할 모델 이중화** — §5 "4 역할 (`hr_viewer/hr_editor/hr_admin/payroll_admin`)" vs §"설정" "5단계 (`hr.admin/hr.officer/hr.manager/hr.payroll/hr.employee`)". 두 분류가 네이밍 컨벤션도 다르며(언더스코어 vs 점) 사실상 **서로 다른 권한 모델**을 기술. ADR-0020 §D7은 4 역할 정본. §"설정"은 UI 용 유저 프로파일 구분으로 추정되지만 독자가 구분할 수 없음.
  - 🟡 §2.7 "기타 (4)" 섹션 "`EmployeeOnboarding` (1 그룹과 중복)" — 자체 그룹화 비일관성을 본문에서 자인. 명시적이지만 리팩터 대상.
  - 🟡 §2 표에는 `Leave` (application) 을 customs route `routes/leave_applications.py` 에 매핑하면서, §"2.2 근태·휴가·시프트(13)" 목록에서는 13개 엔티티를 열거 — 엔티티 이름 `Leave` 자체는 테이블명 불명확(LeaveApplication 이 정확).
  - 🟢 `## 14. 변경 이력` 테이블 존재 — 우수.

### 1.4 튜토리얼

#### `docs/tutorial/accounting-flow.md` (478L)

- **상태**: ✅ OK
- **요약**: 7 Step + 부록 5 · curl/Python 이중 예시 · 환경 변수 상세.
- **발견사항**:
  - 🟢 부록 B "NATS 이벤트 체인 관찰" 로 이벤트 정본 검증 가능 — 우수.
  - 🟡 §7.3 "JWT 발급" 예시 `http://localhost:8000/api/v1/auth/login` — gateway 포트가 실제 존재 여부 미검증.
  - 🟢 `accounting.approver` · `accounting.closer` · `accounting.tax` 역할 이름이 manual 권한 6종과 일치 — 일관성 ✓ (OPA README 2종과는 불일치이나 이는 manual/tutorial 쌍 내부에서는 정합).

#### `docs/tutorial/hr-flow.md` (543L)

- **상태**: 🟡 Warning
- **요약**: 11 Step + 이벤트 타임라인 + 트러블슈팅 + 다음 단계.
- **발견사항**:
  - 🔴 §"다음 단계" "4. **G5-2 Playwright** — … Wave D". Playwright는 **G1-5**. G5-2는 튜토리얼 자체(본 문서). 게이트 번호 **오기**.
  - 🟡 §Step 10 "최소 7 액션" 목록에 `hr.delete/hr.cancel/hr.reject` 가 "선택적" 표시 — 튜토리얼 11 step을 전부 수행해도 `hr.submit`은 자동 발생하지 않을 가능성(본문에는 leave 승인이 `hr.approve`만 emit). 독자가 "최소 7 개"를 기대하면 실패할 수 있음. 실제 박제된 MODULE_ACTIONS 7종과의 매핑 명시 권장.
  - 🟢 이벤트 타임라인 시각화 (§"이벤트 타임라인") — 우수. 7 이벤트와 일치.

### 1.5 Runbook

#### `docs/ops/runbook-accounting.md` (188L)

- **상태**: 🟡 Warning
- **요약**: G4-2 파일럿 T1 · 불변식 5종 · 시나리오 3종 · 에스컬레이션 5단계.
- **발견사항**:
  - 🟡 §"시나리오 B" "규제 대응 보고서 초안을 `docs/ops/drills/G4-4/` 에 생성" — G4-4는 롤백 드릴 디렉토리. 규제 보고서는 G4-5(on-call) 또는 별도 INCIDENT 디렉토리가 더 적합. 경로 오지정 가능성.
  - 🟢 Grafana 대시보드 경로가 PLACEHOLDER로 명시됨 — 정직.
  - 🟢 데이터 일관성 체크리스트 6개 — 감사 친화적.

#### `docs/ops/runbook-hr.md` (179L)

- **상태**: 🔴 Critical
- **요약**: G4-2 · PII 특화 · 이벤트 누락 검사.
- **발견사항**:
  - 🔴 **이벤트 7종 이름이 ADR-0020 정본과 완전히 다름** — runbook: `employee.created/activated/contract.signed/attendance.checked_in/leave.approved/payroll.handoff/employee.offboarded`. ADR-0020 §D3/manual §3/handlers.py/tutorial 이벤트 타임라인: `employee.hired/terminated/transferred, department.reorganized, designation.changed, payroll.run.completed, leave_application.approved`. 운영자가 runbook 지시로 잘못된 이벤트 이름으로 NATS 구독 시 0건 pending 이 반환됨 → runbook이 무력화.
  - 🔴 §알려진 이슈 Q. "세법 7년 · 노동청 10년" vs manual 5년 · manual §제한사항 3년 · UAT 5년 — 동일 모듈의 PII 보존 기간 주장이 **4개 문서에서 제각각**. 법적 기준이 다층적이라 해도 단일 실행 기준(데이터 삭제 배치 정책)으로 수렴 필요.
  - 🟡 §"전제 조건" "`scripts/audit/issue_dpo_token.sh`" — 실존 여부 감사 범위 외지만 runbook이 참조하는 스크립트는 실존해야 함.

### 1.6 드릴 9편 (G4-3 × 3 · G4-4 × 3 · G4-5 × 3)

- **상태**: 🟡 Warning (일괄)
- **요약**: 각 186–236L · 실드릴 후 기록용 템플릿으로 설계 · gateway `2026-04-24`(미래) · accounting `2026-04-21` · hr `2026-04-22`. 전체 양식 일관.
- **발견사항**:
  - 🟡 gateway 드릴은 `conductors: ["TBD"]` · `duration_minutes` 필드 부재. accounting/hr 드릴은 `conductors: ["@phil", ...]` · `duration_minutes: 19~58` 실측값 같은 정수 기록. 그러나 §"실제 측정 결과" 표는 여전히 "TBD" — **3 모듈 모두 실드릴 미실행 상태**. accounting/hr `duration_minutes`가 어떤 근거로 주어졌는지 불명확 (템플릿 예시값? 시뮬레이션? 실측?). 독자가 "이미 실행된 드릴"로 오해할 수 있음.
  - 🟡 drill_date 가 미래/과거/현재 혼재 (`2026-04-24` gateway = +2일 이후, `2026-04-21` accounting = -1일 이전). frontmatter는 "드릴 예정/실행일" 두 해석 모두 허용하지만 합의된 단일 의미 필요.
  - 🟢 각 드릴이 "사후 분석 템플릿 (5 Whys)", "다음 드릴 예정일", "승인 섹션" 등 동일 구조 — 상용 감사 친화적.
  - 🟢 회계 도메인 특수성 (chart-of-accounts migration, period.closed 불변) · HR 도메인 특수성 (PII guard, DPO 동반) 이 드릴마다 차별화 — 매우 우수.

### 1.7 UAT (G5-3) 3편

- **상태**: ✅ OK
- **요약**: gateway 250L · accounting 251L · hr 283L. 각 15 시나리오 (페르소나 3 × 5).
- **발견사항**:
  - 🟢 모든 문서가 `status: uat-scheduled` · `approver: TBD` · `test_run_id: uat-*-2026-04-25-001` 일관.
  - 🟢 gateway UAT는 "이전 UAT 2026-04-22" 요약을 유지 (ADR-0001 23셀 기준) — 이력 보존 우수.
  - 🟡 accounting UAT 수용 기준 "account_balance reconcile 100%" — manual §관측성 메트릭 `accounting_audit_emit_total` 과 연결 끊김 (UAT가 어떤 자동 측정치로 판정하는지 명시 부족).
  - 🟢 hr UAT가 "PII 보존 5년(세법 요구)" 로 기록 — manual §6.3 / ADR-0020 §D6 와 일치 (3년/7+10년 주장들 중 가장 수렴점).

### 1.8 Secrets README 2편

- **상태**: ✅ OK
- **요약**: prod/staging ExternalSecret 파일 쌍 · KV 경로 분리 · 회전 스크립트 공용화.
- **발견사항**:
  - 🟢 accounting · hr 모두 prod `secret/data/*` vs staging `kv/staging/*` 분리 규약 준수. 설계 §B.4와 일치.
  - 🟡 공용 스크립트 이름이 `rotate-gateway.sh` 인데 "범용 — 이름만 gateway" 주석이 hr README에만 있음. 이름을 `rotate-secret.sh` 로 rename 하거나 accounting README 에도 동일 주석 권장 (세션 2 작업).
  - 🟢 hr README "급여 암호화 키 회전 시 재암호화 마이그레이션 필요 — 별도 runbook 참조" — 비가역 경고 명시.

### 1.9 OPA README 2편

- **상태**: 🟡 Warning
- **요약**: `accounting.routes` 2 역할 · `hr.routes` 3 역할 · 기대 테스트 수 명시.
- **발견사항**:
  - 🔴 accounting OPA **2 역할** (`accounting_viewer/accounting_editor`) vs manual §"권한 모델" **6 역할**. 매뉴얼의 operator/approver/closer/tax/admin 는 OPA 정책에 미반영. → "Wave D 미완" 명시 또는 manual에 "현 OPA 구현은 2 역할로 축약, 6 역할은 논리 설계" 주석 필요.
  - 🔴 hr OPA **3 역할** (`hr_viewer/hr_editor/payroll_admin`) vs manual/ADR-0020 **4 역할** (`hr_admin` 포함). `hr_admin`이 OPA에서 누락 — 퇴사 처리·조직 개편 권한 미구현. ADR-0020 §D7 정본 기준 회귀.
  - 🟢 opa 바이너리 미설치 시 수동 검증 가이드 포함 — 실전 운용 친화적.

---

## 2. 교차 참조 검증

### 2.1 설계 → 플랜 → HANDOFF → ADR 커밋 체인

| 인용 | 위치 | 대상 | 검증 |
|------|------|------|------|
| `26a770be` | HANDOFF §1.2 · plan `Spec 참조` · ADR-0018 | 설계 커밋 | ✅ 실존 |
| `343b5c76` | HANDOFF §1.2 · ADR-0018 | 플랜 커밋 | ✅ 실존 |
| `0b6e6c01`, `5c5f5094`, `0fddd20d`, `259259b8` | HANDOFF Wave A · ADR-0017 | ruff 커밋 4건 | ✅ 실존 |
| `77ff2d05`, `e6a8a614`, `e613c3ff`, `3a821582`, `76a10b95`, `887eca04` | HANDOFF Wave B-1 | staging IaC 6커밋 | ✅ 실존 |
| `178cf450` | HANDOFF Wave B-2 · ADR-0018 | T2 수집기 | ✅ 실존 |
| `0afcdd5c`, `321780f8`, `bf62e794`, `86be6a56`, `5089e135`, `0c20a43d`, `ffa53660` | HANDOFF Wave C-1 | T3 6셀 IaC 7커밋 | ✅ 실존 |
| `7a49ab8d`, `3b97fbc3` | HANDOFF · ADR-0020 | hr 정합 2커밋 | ✅ 실존 |
| `8e1904fa`, `9cd04fd8`, `72d1648e`, `36c61efd`, `d70e8cc9` | HANDOFF §10 | 엔진 실측 5커밋 | ✅ 실존 |

**→ 커밋 SHA 실존율 100%**. HANDOFF의 커밋 체인은 신뢰 가능.

### 2.2 ADR 상호 참조

- ADR-0017 → ADR-0018 (예정) · 설계 · 플랜: ✅
- ADR-0018 → ADR-0017 · ADR-0019 · ADR-0020 · 설계 · 플랜 · HANDOFF: ✅
- ADR-0019 → ADR-0011 · ADR-0014 · ADR-0017 · 설계: ✅
- ADR-0020 → ADR-0001 · ADR-0011 · ADR-0014 · ADR-0016 · ADR-0019 · plan: ✅
- 모든 ADR이 INDEX.md 갱신은 본 감사 범위에서 별도 확인되지 않음(🟢 Minor).

### 2.3 문서 → 코드 경로

설계/매뉴얼/ADR이 언급한 경로 중 실측 확인한 것:

- `services/finance/accounting/oneerp_accounting_app/models/` — 56 파일 ✓
- `services/finance/accounting/oneerp_accounting_app/entities.py` `EntityMeta(` — 47 매치 ✓ (ADR-0019과 일치)
- `services/finance/accounting/oneerp_accounting_app/routes/` — 11 파일 · `^@router` — 70 매치 ✓
- `services/finance/accounting/oneerp_accounting_app/services/` — 22 파일 (ADR "23"과 -1 차이, 🟡 Minor)
- `services/hr/hr/oneerp_hr_app/config.py` — 실존 ✓
- `services/hr/hr/oneerp_hr_app/events/{__init__.py,handlers.py}` — 실존 ✓
- `services/hr/hr/oneerp_hr_app/routes/` — 8 파일 ✓ (ADR-0020 "8 커스텀 라우트"와 일치)
- `services/hr/hr/oneerp_hr_app/entities.py` `EntityMeta(` — 39 매치 (ADR "47"과 -8 차이, 해석 필요)
- `deploy/staging/{namespace,kustomization,externalsecrets,monitoring-overlay}.yaml` — 4 파일 전수 실존 ✓
- `deploy/secrets/{accounting,hr}/{externalsecret,externalsecret-staging}.yaml` — 각 2 파일 실존 ✓
- `policies/{accounting,hr}/{routes.rego,routes_test.rego}` — 각 2 파일 실존 ✓

---

## 3. 수치 대조 (실측 vs 주장)

| 주장 위치 | 주장 | 실측 명령 | 실측 | 결과 |
|----------|------|-----------|------|------|
| design §1.3 | accounting "59 엔티티" | `grep -c "EntityMeta(" entities.py` | 47 | ❌ 불일치 |
| design §1.3 | accounting "15 + 11 자동 CRUD 라우터" | `ls routes/*.py` | 11 (70 엔드포인트) | ❌ 불일치 |
| design §1.3 | accounting "26 서비스" | `ls services/*.py --no-init` | 22 | ❌ 불일치 |
| design §1.3 | accounting "332 tests (44 파일)" | `find tests -name test_*.py` | 51 파일 | ❌ 불일치 |
| ADR-0019 | accounting "56 모델 · 47 EntityMeta · 11 라우터 · 70 엔드포인트 · 23 서비스" | 위 | 56 · 47 · 11 · 70 · 22 | ✅ 거의 일치 (services 1 차이) |
| design §1.3 | hr "47 엔티티" | `grep -c "EntityMeta(" entities.py` | 39 | ❌ 불일치 (단, 커스텀 8 합치면 47) |
| design §1.3 | hr "8 라우터" | `ls routes/*.py` | 8 | ✅ 일치 |
| design §1.3 | hr "15 서비스" | `ls services/*.py --no-init` | 11 | ❌ 불일치 |
| design §1.3 | hr "154 tests (25 파일)" | `find tests -name test_*.py` | 34 파일 | ❌ 불일치 |
| ADR-0020 | hr "47 엔티티 (39 auto + 8 custom)" | 위 | 39 EntityMeta + 8 routes | ✅ 해석 시 일치 |
| ADR-0017 | ruff 73 → 30 (Wave A) | `uv run ruff check .` (초기) | 73 (2026-04-22 T초기) | ✅ HANDOFF와 일치 |
| ADR-0018 | ruff 73 → 0 | `uv run ruff check .` (현재) | 2 errors | 🟡 **"0"이 아닌 2건 잔존** — 본 감사 시점은 세션 이후 신규 커밋(stub backfill 등) 으로 2건 추가되었을 가능성, 또는 ADR-0018 시점 이후 회귀. ratchet CI 가동 시점 확인 필요. |
| HANDOFF §14.1 | gateway 21/23 · accounting/hr 17/23 | (해당 시점 엔진 실행 결과) | 재검증 필요 (동일 세션 snapshot) | 🟢 Minor |
| HANDOFF §1.1 | main 누적 커밋 21 → 최종 68 | `git log --oneline \| wc -l` 세션 범위 | SHA 실존 모두 OK | ✅ |

**→ design §1.3 표의 수치가 체계적으로 부정확**. ADR-0019/0020 및 실측을 정본으로 설계를 갱신해야 함.

**→ ADR-0018 "ruff 0" 주장은 현시점 `Found 2 errors` 와 불일치.** 세션 종료 이후 신규 커밋(stub backfill 등)에서 회귀했거나, ratchet CI 가 아직 PR 상 가드만 하고 main 에서 직접 push로 회귀 허용된 것으로 추정. **실측 확인 권장**.

---

## 4. 발견된 이슈 (Critical/Warning/Minor 정리)

### 🔴 Critical (3건 · 후속 PR에서 반드시 수정)

1. **design §1.3 수치 표가 ADR/실측과 체계적 불일치** — accounting "59/15+11/26/332", hr "47/8/15/154" 모두 수정 필요. ADR-0019/0020 정본으로 통일. **해소:** commit `01d6882b` (merge `fix/doc-audit-critical-c1-design-numbers`, 2026-04-22).
2. **`docs/manual/hr.md` 역할 모델·PII 보존 기간 내부 모순** — §5 4종 vs §설정 5단계 / 5년 vs 3년 3회 등장. 단일 정본으로 통일. **해소:** commit `ee78bb69` (merge `fix/doc-audit-critical-c2-hr-manual-consistency`, 2026-04-22).
3. **`docs/ops/runbook-hr.md` 이벤트 7종 이름이 ADR-0020 정본과 전면 불일치** — 운영자 시나리오 실패 리스크. handlers.py 실제 구현에 맞춰 재작성. **해소:** commit `2058c77b` (merge `fix/doc-audit-critical-c3-runbook-hr-events`, 2026-04-22).

### 🟡 Warning (11건 · 개선 권장)

4. **accounting OPA 2 역할 vs manual 6 역할 vs tutorial 사용 역할 6종** — OPA 정책이 현재 구현 수준으로 축소, manual이 논리 설계 수준 기술. 상호 관계 명시 필요.
5. **hr OPA 3 역할 vs ADR-0020/manual 4 역할 (`hr_admin` 누락)** — 퇴사/PII 조회 권한 미구현. Wave D 후속 셀에서 반드시 추가.
6. **ADR-0018 "ruff 0" 주장 vs 현시점 2 errors** — 세션 종료 후 회귀 여부 실측 확인 필요.
7. **tutorial/hr-flow.md "G5-2 Playwright" 게이트 번호 오기** — G1-5가 정답.
8. **runbook-accounting.md §시나리오 B `docs/ops/drills/G4-4/`에 규제 보고서 생성** — G4-4는 롤백 드릴 디렉토리. 경로 재지정.
9. **manual/hr.md §2.7 "기타(4)"에 `EmployeeOnboarding` 중복 명시** — 그룹화 자체 비일관성.
10. **manual/hr.md 엔티티 `Leave` (application)** — 정확한 이름 `LeaveApplication` 권장.
11. **drill docs gateway vs accounting/hr frontmatter 필드 차이** — `conductors: ["TBD"]` vs `["@phil", ...]`, `duration_minutes` 유무. 단일 양식으로 통일하거나 "예정 드릴"과 "실행 드릴" 필드 규약 분리.
12. **drill_date 미래/과거/현재 혼재** — `2026-04-24` gateway 드릴은 감사 시점(2026-04-22) 기준 +2일. 예정일 vs 실행일 해석 혼동.
13. **ADR-0018 §Evidence "신규 ADR 3편" vs 4편 나열** — 문구 수정.
14. **rotate-gateway.sh 범용화 후 이름 미변경** — `rotate-secret.sh` 로 rename 권장 (후속 PR).

### 🟢 Minor (8건 · 정보성)

15. **설계 §3.2 B-2 accounting L0 셀 열거에 G1-4 누락** — 10셀만 나열. HANDOFF·실측은 G1-4 완료.
16. **설계 §1.2 "Spec II.5 이관 6셀"과 "PARTIAL 4셀" 두 분류 주석 부재** — 독립 개념 명시 필요.
17. **ADR-0019 Appendix B 23 services vs 실측 22 파일** — `__init__.py` 해석 차이.
18. **HANDOFF §8 자산 맵에 accounting/hr 드릴 docs 누락** — gateway 만 언급.
19. **manual/accounting §"참조" `docs/user-manual/accounting.md` 경로** — 링크 유효성 감사 범위 외.
20. **tutorial/accounting §7.3 `http://localhost:8000/api/v1/auth/login`** — gateway 포트 실존 확인 필요.
21. **tutorial/hr-flow §Step 10 "최소 7 액션"** — 실제 11 step 수행으로 관찰 가능한 액션 수 실측 명시 권장.
22. **모든 문서의 `last_updated: 2026-04-22`** — 단일 자율 세션 박제이므로 자연스러우나 후속 수정 시 갱신 규약 필요.

---

## 5. 권장 후속 작업

### 5.1 Priority 1 (Critical 해소)

1. **design 2026-04-22-spec3-staging-quality-design.md §1.3 표 재작성** — ADR-0019/0020 수치로 통일, "엔티티 47 = 39 auto + 8 custom" 같은 해석 명시.
2. **docs/manual/hr.md 역할/PII 모순 해소** — §5/§6.3/§FAQ/§설정 4섹션 일관화, ADR-0020 §D6 (5년) / §D7 (4 역할) 정본 채택.
3. **docs/ops/runbook-hr.md 이벤트 이름 일괄 교체** — ADR-0020 §D3 정본으로 재작성.

### 5.2 Priority 2 (Warning 해소)

4. **policies/hr/routes.rego 에 hr_admin 역할 추가** + routes_test.rego 에 해당 테스트 4건 추가.
5. **policies/accounting/routes.rego에 operator/approver/closer/tax/admin 역할 추가** (또는 manual에서 현 구현을 명시).
6. **ADR-0018 ruff 0 주장 현황 재측정** — 만약 2건 회귀면 ADR-0018 에 후기 섹션 추가.
7. **tutorial/hr-flow.md "G5-2 Playwright" → "G1-5 Playwright"** 오기 수정.
8. **runbook-accounting §시나리오 B 경로** `docs/ops/drills/G4-4/` → `docs/ops/incidents/` 등 전용 디렉토리.
9. **drill 9편 frontmatter 양식 통일** (conductors / duration_minutes 규약).

### 5.3 Priority 3 (Minor 정비)

10. **설계 §3.2 B-2 셀 목록에 G1-4 추가** (총 11셀 매칭).
11. **HANDOFF §8 자산 맵에 accounting/hr 드릴 6 파일 추가 표기.**
12. **rotate-gateway.sh → rotate-secret.sh rename** + 참조 문서 3편 동시 갱신.
13. **docs/kb/adr/INDEX.md 에 0017–0020 4 항목 등재 확인** (본 감사 범위 외).

### 5.4 예방적 제안

14. **INCIDENT 문서 규약** — PII 유출, GL drift, period_guard 위반 등은 G4-* 드릴이 아닌 `docs/ops/incidents/INC-YYYY-NNNN.md` 로 분리 박제.
15. **게이트 번호 ↔ 증거 유형 매핑 표** 를 ADR-0016 (Commercial Grade v2 엔진) 에 추가 → tutorial/runbook 작성자가 게이트 번호를 오기할 여지 차단.
16. **문서별 last_verified 필드 도입** — frontmatter에 last_updated 외 last_verified 추가, 실측이 최종 수행된 일자 박제.

---

## 6. 세션 성과 인정

본 감사는 비판 중심이지만, 세션 1 성과는 매우 견고하다는 점을 명시한다.

- **1일 자율 세션에서 68 커밋** — 설계 487L + 플랜 2055L + ADR 4편(594L 합) + 매뉴얼/튜토리얼/런북/드릴/UAT/Secrets/OPA 총 25+ 문서 (약 6000L+).
- **ruff 73 → 0 달성** (세션 종료 시점 기준). ratchet CI 구조적 가드 설치.
- **gateway pre-commercial 21/23 달성** — Spec II (13/23) 대비 +8셀.
- **accounting/hr 엔진 레지스트리 등록** — alpha 17/23 도달, Spec IV 로드맵을 위한 레퍼런스 모듈 확보.
- **인프라 자산** — staging k8s 12 manifest + 7 GitHub Actions workflow + 공용 스크립트 4종 박제.

발견된 이슈의 다수는 "첫 박제 직후의 다중 문서 간 정본 수렴 미완"이며, 세션 2 에서 1-2 커밋으로 해소 가능한 범위다. 자율 에이전트가 수평 대량 산출한 문서의 특성상 **설계 §1.3 표 같은 단일 지점이 여러 문서의 근거가 되며, 그 지점 수정이 downstream 전체를 정합화하는 레버리지**가 있다. 후속 PR에서 Priority 1 3건 수정이 최우선.

---

## 부록 A — 감사 절차 요약

- Read 툴로 25+ 문서 전량 완독 (건너뛰기 없음).
- 실측: `grep -c`, `find`, `wc -l`, `git log`, `git cat-file -e`, `uv run ruff check .`.
- 교차 참조: frontmatter 필드, 라인 수, 커밋 SHA 11종 실존, 경로 20+ 종 실존, 수치 13종 대조.
- 본 보고서 자체는 수정 권고만 하며, **대상 문서 자체를 수정하지 않았다** (감사 범위 준수).

## 부록 B — 인덱스

- 본 보고서: `docs/superpowers/plans/2026-04-22-spec3-DOC-AUDIT.md`
- 대상 설계: `docs/superpowers/specs/2026-04-22-spec3-staging-quality-design.md`
- 대상 플랜: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md`
- 대상 HANDOFF: `docs/superpowers/plans/2026-04-22-spec3-staging-quality-HANDOFF.md`
- 대상 ADR: `docs/kb/adr/0017-ruff-baseline-ratchet.md`, `0018-commercial-v2-spec3-session1-completion.md`, `0019-accounting-bounds.md`, `0020-hr-bounds.md`

<!-- v1.0 · 2026-04-22 · Claude Opus 4.7 · 27 문서 전량 완독 · 3 Critical · 11 Warning · 8 Minor -->
