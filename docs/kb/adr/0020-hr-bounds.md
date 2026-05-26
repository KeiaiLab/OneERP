---
status: accepted
date: 2026-04-22
gate: G1-1
module: hr
tier: T1
decision: hr cluster 의 범위·엔티티·이벤트 체인 7종·권한 모델을 확정하고 payroll/finance 와의 경계를 명시한다
consequences: hr-payroll 분리 유지 · SCIM/LDAP 선택적 통합 · 개인정보/퇴사 데이터 보존 규약 고정 · 이벤트 체인 7종 이후 확장 시 본 ADR 개정 필요
---

# ADR-0020 — hr 모듈 범위 확정 (Commercial Grade v2 · G1-1)

## 배경

OneERP 의 `hr` 모듈은 47 개 도메인 엔티티를 가진 가장 넓은 운영 모듈 중 하나이다. Spec III Wave C-2 에서 hr 를 Commercial Grade v2 두 번째 수직 완성 후보로 선정함에 따라, 본 문서로 **hr cluster 의 범위·책임 경계·인접 모듈과의 계약**을 박제한다. ADR-0019 (accounting-bounds) 과 동일 목적을 hr 에 적용한다.

### hr 모듈이 해결하는 문제

1. **직원 마스터 (Employee Master)** — 채용부터 퇴사까지 전 생애주기의 단일 진실 원천(SSOT).
2. **조직 구조 (Org Graph)** — 부서(Department) · 직급(Designation) · 보고라인(Reporting Line) · 직원 그룹(Employee Group).
3. **근태·휴가 (Attendance & Leave)** — 체크인/아웃, 시프트, 휴가 유형·정책·잔액·승인.
4. **인재 개발 (Talent)** — 교육(Learning Course/Enrollment), 인증, 역량 프레임워크, 후계자 계획.
5. **평가 (Performance)** — 평가 사이클·템플릿·목표 설정, 개별 평가 실행.
6. **채용 (Recruitment)** — 채용 공고, 지원자, 면접 라운드, 오퍼 레터, 직원 추천.
7. **안전·건강 (Safety & Health)** — 안전 교육, 건강 검진, 산업 재해 보고.
8. **오프보딩 (Offboarding)** — 퇴사 절차, 정산, 장비 반납, 데이터 삭제 예약.

## 결정 사항

### D1. 엔티티 범위 (47 건)

`services/hr/hr/oneerp_hr_app/entities.py` 의 `ENTITY_METAS` 선언 + `routes/` 하위 커스텀 라우트 엔티티를 모두 hr cluster 범위로 고정한다.

**직원/조직**
- `Employee`, `EmployeeGroup`, `EmployeeTransfer`, `EmployeeOnboarding`, `EmployeeOffboarding`,
  `EmployeeReferral`, `EmployeeSkillMap`, `EmployeeDocumentExpiry`, `EmployeeEngagementSurvey`
- `Department`, `Designation`

**근태/휴가/시프트**
- `Attendance`, `ShiftType`, `ShiftAssignment`, `ShiftRequest`,
  `OvertimeEntry`, `OvertimePolicy`
- `Leave`, `LeaveType`, `LeavePolicy`, `LeavePolicyAssignment`, `LeavePeriod`, `LeaveBalance`
- `CompensatoryLeaveRequest`

**평가/목표/역량**
- `Appraisal`, `AppraisalCycle`, `AppraisalTemplate`, `GoalSetting`, `CompetencyFramework`

**인재개발/교육**
- `LearningCourse`, `LearningEnrollment`, `LearningCertification`, `TrainingEvent`,
  `TalentDevelopmentPlan`, `SuccessionPlan`

**채용**
- `JobOpening`, `JobApplicant`, `InterviewRound`, `InterviewFeedback`, `OfferLetter`

**안전/건강**
- `SafetyTraining`, `SafetyIncident`, `HealthCheckup`

상기 목록 외 엔티티는 hr cluster 에 속하지 않는다. 추가 시 본 ADR 을 개정한다.

### D2. 커스텀 라우트 vs 자동 CRUD

`routes/` 에 커스텀 라우트가 존재하는 엔티티는 도메인 로직(워크플로·워크벤치·집계)이 붙는 엔티티로 한정한다.

| 엔티티 | 라우트 파일 | 커스텀 사유 |
|---|---|---|
| `Employee` | `routes/employees.py` | 조직도 · 보고라인 · 상태 전이 |
| `EmployeeTransfer` | `routes/employee_transfers.py` | 발령 워크벤치 · 승인 흐름 |
| `Department` | `routes/departments.py` | 계층 tree · 재귀 쿼리 |
| `Designation` | `routes/designations.py` | 직급 체계 hierarchy |
| `Attendance` | `routes/attendances.py` | 체크인/체크아웃 · 주간 리포트 |
| `LeaveType` | `routes/leave_types.py` | 활성 카탈로그 · summary |
| `Leave` (application) | `routes/leave_applications.py` | 다단계 승인 워크플로 |
| `LeaveBalance` | `routes/leave_balances.py` | 연차 자동 부여 · 이월 · summary |

그 외 엔티티는 `EntityMeta` 기반 자동 CRUD 로 충분하며, 별도 라우트를 추가하려면 "자동 CRUD 에 커스텀 로직이 필요하다" 는 근거를 commit 에 남겨야 한다.

### D3. 이벤트 체인 7종

`services/hr/hr/oneerp_hr_app/events/` 에 구현된 7개 핸들러를 hr 도메인 이벤트 공식 집합으로 확정한다. 추가 이벤트는 본 ADR 개정 없이 도입 금지.

| 이벤트 | EventType | 트리거 | 주 소비자 |
|---|---|---|---|
| `employee.hired` | `EMPLOYEE_HIRED` | 신규 직원 등록 확정 | 온보딩 체크리스트 / 장비 요청 / 계정 프로비저닝 |
| `employee.terminated` | `EMPLOYEE_TERMINATED` | 퇴사 확정 | 오프보딩 워크플로 / 최종 정산 / 계정 회수 |
| `employee.transferred` | `EMPLOYEE_TRANSFERRED` | 발령 승인 완료 | 조직도 재계산 / 보고라인 업데이트 / 결재권 재매핑 |
| `department.reorganized` | `DEPARTMENT_REORGANIZED` | 부서 생성/통합/분할 | 조직도 캐시 무효화 / BI 보고 / 라우팅 |
| `designation.changed` | `DESIGNATION_CHANGED` | 직급 부여/회수 | payroll 등급 재매핑 / 결재권 재매핑 |
| `payroll.run.completed` | `PAYROLL_RUN_COMPLETED` | 외부 payroll 처리 완료 | 명세서 알림 / 회계 분개 트리거 / 잔액 조정 |
| `leave_application.approved` | `LEAVE_APPLICATION_APPROVED` | 휴가 승인 완료 | 휴가 잔액 차감 / 근태 자동 기록 / 대체 인력 통보 |

구독 등록 규칙은 `services/hr/hr/oneerp_hr_app/events/handlers.py:register_handlers()` 를 정본으로 한다. 직접 `event_registry.register_handler()` 를 모듈 전역에서 호출하는 accounting 방식과 달리, hr 는 FastAPI lifespan 시점 명시 호출 패턴을 채택한다 (main.py 참조). 의도적 차이이며 양쪽 모두 "구독 완료" 결과는 동일하다.

### D4. hr-payroll 경계

payroll 서비스는 hr 와 **별도 cluster** 로 남긴다. 이유:

1. **도메인 무결성 분리** — hr 는 인사 마스터와 조직 구조 · payroll 은 급여 계산/명세/지급 체인. 감사 경계가 다르다.
2. **컴플라이언스 등급 차이** — payroll 은 개인 금융 정보(은행계좌 · 세무 식별자) 를 다루며 감사 주기·접근 통제가 hr 보다 엄격하다.
3. **외부 연동 경로 분리** — hr 는 HRIS/SCIM/LDAP 방향 · payroll 은 국세청/은행/ERP 재무 방향.

hr ↔ payroll 상호작용은 **이벤트 체인 2건** 으로만 한다.

- hr → payroll: `employee.hired`, `employee.terminated`, `employee.transferred`, `designation.changed` (직원/급여 등급 마스터 동기화)
- payroll → hr: `payroll.run.completed` (hr 는 소비자로서 명세서 알림 트리거)

직접 DB 공유·crossing import 는 금지한다. 구현 시점에 교차 import 가 발견되면 blocker 로 간주한다.

### D5. SCIM/LDAP 통합 — 선택적 채택

`HRSettings.hr_scim_enabled` 와 `HRSettings.hr_ldap_url` 은 **런타임 스위치** 이다. 기본값 off.

- **on 인 경우**: 외부 IdP 에서 직원 마스터를 주입받으며, hr 는 "읽기 우선" 동작. `employee.hired/transferred/terminated` 가 IdP 변경 이벤트와 idempotent 로 병행한다.
- **off 인 경우**: hr 가 직원 마스터의 유일한 원천. 계정 생성은 hr → gateway `auth` 서비스 호출로 이루어진다.

두 경로 모두 **감사 로그를 동일하게 남긴다** (actor=`scim-sync` 또는 `hr-api`).

### D6. 개인정보 처리 · 퇴사 데이터 보존

개인정보보호법/GDPR 대응을 위해 다음 규약을 hr 모듈에 고정한다.

1. **최소 수집 원칙** — `Employee` 모델은 마스터 데이터만 보관. 주민등록번호/은행계좌는 payroll 전담.
2. **접근 통제** — `hr_admin` 만 급여 관련 필드 조회 가능. 일반 `hr_viewer` 는 업무 필드만.
3. **퇴사 후 보존 기간** — `EmployeeOffboarding.data_retention_until` 필드로 보존 종료일을 명시. 기본 5년(근로기준법 §42). 만료 시 배치 job 이 `employee.terminated` 후속 처리로 PII 익명화.
4. **감사 필수 액션** — 모든 CRUD/상태전이는 `audit_hooks.emit()` 을 통해 `audit_events` 컬렉션에 기록한다. `MODULE_ACTIONS` 화이트리스트에 없는 액션은 `hr.unknown.<action>` 으로 강제 라벨링하여 누락을 막는다.

### D7. 권한 모델 (RBAC · G3-3 사전 근거)

hr 는 다음 4 개 역할을 공식 역할로 한다.

- `hr_viewer` — 직원/부서/직급/근태 조회 (공개 필드에 한함). 급여·개인정보 필드 차단.
- `hr_editor` — 직원 CRUD, 발령/휴가 신청 작성, 근태 수정.
- `hr_admin` — 퇴사 처리, 조직 개편, 급여 필드 접근, PII 조회.
- `payroll_admin` — payroll 서비스 권한. hr 에서는 **월급/급여 등급 조회만 허용**.

역할 경계는 G3-3 (policies/hr/routes.rego) 에서 OPA 로 강제되며, 본 ADR 은 정책의 소스 오브 트루스.

## 대안 비교

| 대안 | 장점 | 단점 | 결론 |
|---|---|---|---|
| **A. hr-payroll 분리 유지** (채택) | 감사 경계 명확 · 외부 연동 경로 분리 | 교차 이벤트 설계 비용 | ✅ 채택 |
| B. hr ↔ payroll 통합 cluster | 이벤트 수 감소 | 컴플라이언스 등급 혼재 · 감사 범위 비대 | 거부 |
| C. hr 를 2개 모듈로 분리 (core-hr + talent) | 개발 병렬화 | 이벤트 체인 중복 · 47 엔티티가 2 cluster 로 뭉쳐있어 ROI 낮음 | 거부 |
| D. SCIM/LDAP 필수화 | IdP 일원화 | 단독 배포 고객 대응 불가 | 거부 (선택적 유지) |

## 결과

### 즉각 영향 (Spec III Wave C-2 완료 시점)

- hr 모듈 L0 11 셀 PASS → 라벨 `none` → `alpha` 혹은 `beta`
- `scripts/commercial-engine score --module hr` 11/14 이상
- 본 ADR 이 G3-3 (OPA) · G5-1 (매뉴얼) · G5-2 (튜토리얼) 의 설계 기준점으로 작동

### 중기 영향 (Wave D2 L1 3셀 완료 시점)

- hr 최초로 `beta` → `commercial-ready` 근접
- payroll 과의 이벤트 경계가 실제 트래픽 로그로 검증됨
- SCIM/LDAP 통합 선택 고객에 대한 공식 지원 경로 확보

### 장기 영향

- 47 개 엔티티의 변경 이력이 `audit_events` 로 완전 추적
- PII 보존 정책이 코드(`EmployeeOffboarding.data_retention_until`) + 배치 job 으로 자동화
- 이벤트 체인 7종 이상 추가 필요 시 ADR 개정이 게이트가 되어 무분별 확장 방지

## 위험 및 완화

| 위험 | 발생 확률 | 영향 | 완화 |
|---|---|---|---|
| payroll 과의 교차 import 재발 | 중 | cluster 경계 파괴 | CI 에서 `ruff` TID251 규칙 · import 검사 스크립트 |
| 이벤트 체인 silent 실패 | 중 | 후속 처리 누락 | 각 핸들러가 logger.debug 로 수신 기록 · G3-4 감사 이벤트 emit |
| SCIM on/off 혼동 | 낮음 | 직원 마스터 중복 | `HRSettings` 기동 로그에 현재 모드 명시 |
| PII 보존 만료 배치 미수행 | 높음 | 규제 위반 | 만료일 필드 + 알람 + G4-2 런북 |

## 증거 파일 경로

- 엔티티 선언: `services/hr/hr/oneerp_hr_app/entities.py` (47 EntityMeta 선언 + 커스텀 라우트 8종)
- 커스텀 라우트: `services/hr/hr/oneerp_hr_app/routes/{employees,employee_transfers,attendances,departments,designations,leave_types,leave_applications,leave_balances}.py`
- 설정: `services/hr/hr/oneerp_hr_app/config.py` (HRSettings · `hr_ldap_url`, `hr_scim_enabled`, `hr_payroll_webhook`)
- 메인: `services/hr/hr/oneerp_hr_app/main.py` (app_factory + register_handlers 호출)
- 이벤트 레지스트리: `services/hr/hr/oneerp_hr_app/events/__init__.py`
- 이벤트 핸들러 7종: `services/hr/hr/oneerp_hr_app/events/handlers.py`
- 감사 훅: `services/hr/hr/oneerp_hr_app/audit_hooks.py`
- 테스트 154건: `services/hr/hr/tests/unit/`
- 관련 커밋: `7a49ab8d` (HRSettings 추가), `3b97fbc3` (event_registry + 7 handlers)

## 후속 작업 (Spec III Wave C-2 이후)

1. **G1-2 OpenAPI 스펙 고정** — pydantic forward-ref rebuild 이슈 해결 후 `services/hr/hr/openapi.yaml` 정식 덤프. 현재는 최소 스텁 yaml 로 대체 (본 ADR 은 스펙 고정의 설계 근거).
2. **G1-3 통합 테스트 보강** — 핵심 3 라우터(employees/leave/attendances) × 대표 시나리오 4 케이스 이상.
3. **G3-1 AuthN 7종** — gateway 패턴 미러. `tests/security/test_auth_*.py` 7 파일 신설. HR 특수 시나리오(역할 경계·급여 필드 차단) 강조.
4. **G3-3 OPA rego** — 본 ADR §D7 역할 4종을 `policies/hr/routes.rego` 로 구현, `routes_test.rego` 6 테스트 이상.
5. **G3-4 감사 mutation** — `audit_hooks.MODULE_ACTIONS` 전수 mutation 10건 이상.
6. **G5-1/G5-2 문서화** — `docs/manual/hr.md` 400L+, `docs/tutorial/hr-flow.md` 400L+.
7. **C2-14 집계** — `scripts/commercial-engine score --module hr` 11/14 이상 달성 확인.

## 트레이드오프·한계

본 ADR 은 "현재 구현된 47 엔티티를 hr cluster 로 박제"하는 결정이다. 이후 급격한 도메인 변화(예: 블록체인 기반 employee ID, 실시간 생체 근태) 가 등장하면 본 ADR 을 개정해야 한다. Living ADR 로 취급하되, 이벤트 체인 7종에 대한 변경은 payroll 과의 호환성 검증 없이는 merge 하지 않는다.

또한 본 ADR 은 **T1(오프라인/코드 근거) 수준**의 결정만을 담는다. 실제 라이브 환경에서의 SLO/가용성은 G2-1 (T2), T3 스테이징 드릴에서 별도 문서로 박제된다.

## 참조

- ADR-0001 Commercial Grade 23 기준 (특히 §6.3 G3-4 감사 · §6.2 G3-3 RBAC)
- ADR-0011 Runtime Cluster Decomposition (hr 가 standalone cluster 임을 선언)
- ADR-0014 Runtime Plane Decomposition (hr plane 배치 기준)
- ADR-0016 Commercial Grade v2 Evidence Engine
- ADR-0019 accounting-bounds (본 ADR 의 모본)
- Plan: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md` §Wave C-2
- Commit: `7a49ab8d` feat(hr): HRSettings 도입
- Commit: `3b97fbc3` feat(hr): event_registry + 7 handlers
