---
module: hr
tier: T1
gate: G5-1
version: 0.1.0
last_updated: 2026-04-22
---

# OneERP HR 모듈 매뉴얼

본 문서는 OneERP `hr` 서비스의 **운영자/관리자 매뉴얼** 이다. 기본 개요는 `docs/user-manual/05-hr.md` 에 간략 버전이 존재하며, 본 문서는 상용 등급(Commercial Grade v2 · G5-1) 완성본으로서 47 엔티티·이벤트 체인 7종·권한 모델·개인정보 처리 규약까지 포괄한다.

> **Scope** — T1 (오프라인 근거) 수준. 라이브 환경 SLO/대시보드는 G2-1/G4-1 문서 참조.

---

## 1. 개요

### 1.1 hr 모듈이란

hr 서비스는 OneERP 에서 **사람과 조직** 에 관한 단일 진실 원천(SSOT) 이다. 직원 마스터, 조직 구조, 근태·휴가, 평가·인재개발, 채용, 안전·건강, 오프보딩까지 인사(人事) 업무 전 생애주기를 다룬다. 급여 계산/지급은 별도 `payroll` 서비스가 담당하며, hr 와는 이벤트 체인 2방향으로만 연결된다 (ADR-0020 §D4 참조).

### 1.2 기술 스택

| 항목 | 스택 |
|---|---|
| 언어/런타임 | Python 3.14 |
| 프레임워크 | FastAPI + Pydantic v2 |
| DB | FerretDB (MongoDB 프로토콜) |
| 패키지 관리 | uv workspace |
| 라우팅 구성 | 8 커스텀 라우터 + 39 EntityMeta 자동 CRUD = **47 엔티티** |

### 1.3 관련 문서

- ADR-0020 hr-bounds: `docs/kb/adr/0020-hr-bounds.md`
- 간략 매뉴얼: `docs/user-manual/05-hr.md`
- 튜토리얼: `docs/tutorial/hr-flow.md`
- OpenAPI 스텁: `services/hr/hr/openapi.yaml`
- Plan: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md` §Wave C-2

---

## 2. 도메인 모델 (47 엔티티)

hr 모듈은 여덟 개 도메인 그룹으로 47 엔티티를 구성한다. 각 그룹은 독립적인 업무 기능이 있지만 `Employee` 엔티티를 축으로 모두 연결된다.

### 2.1 직원·조직 (11)

| 엔티티 | 책임 | 커스텀 라우트 |
|---|---|---|
| `Employee` | 직원 마스터 (재직/휴직/퇴사 상태) | `routes/employees.py` |
| `EmployeeGroup` | 직원 그룹화 (예: "계약직", "경영진") | auto |
| `EmployeeTransfer` | 발령 이력 | `routes/employee_transfers.py` |
| `EmployeeOnboarding` | 온보딩 체크리스트 | auto |
| `EmployeeOffboarding` | 오프보딩 절차 + `data_retention_until` | auto |
| `EmployeeReferral` | 사내 추천 | auto |
| `EmployeeSkillMap` | 스킬 매트릭스 | auto |
| `EmployeeDocumentExpiry` | 비자/자격증 만료 알림 | auto |
| `EmployeeEngagementSurvey` | 조직 서베이 | auto |
| `Department` | 부서 계층 | `routes/departments.py` |
| `Designation` | 직급 체계 | `routes/designations.py` |

### 2.2 근태·휴가·시프트 (13)

| 엔티티 | 책임 | 커스텀 라우트 |
|---|---|---|
| `Attendance` | 일별 출근/퇴근 | `routes/attendances.py` |
| `ShiftType` | 시프트 유형 (주/야) | auto |
| `ShiftAssignment` | 시프트 배정 | auto |
| `ShiftRequest` | 시프트 변경 요청 | auto |
| `OvertimeEntry` | 초과근무 기록 | auto |
| `OvertimePolicy` | 초과근무 정책 | auto |
| `Leave` | 휴가 신청 | `routes/leave_applications.py` |
| `LeaveType` | 연차/병가/경조 등 | `routes/leave_types.py` |
| `LeavePolicy` | 휴가 정책 | auto |
| `LeavePolicyAssignment` | 정책 대상 지정 | auto |
| `LeavePeriod` | 휴가 회계기 | auto |
| `LeaveBalance` | 잔액 | `routes/leave_balances.py` |
| `CompensatoryLeaveRequest` | 대체 휴가 | auto |

### 2.3 평가·목표·역량 (5)

- `Appraisal` · `AppraisalCycle` · `AppraisalTemplate` · `GoalSetting` · `CompetencyFramework`

### 2.4 인재개발·교육 (6)

- `LearningCourse` · `LearningEnrollment` · `LearningCertification` · `TrainingEvent` · `TalentDevelopmentPlan` · `SuccessionPlan`

### 2.5 채용 (5)

- `JobOpening` · `JobApplicant` · `InterviewRound` · `InterviewFeedback` · `OfferLetter`

### 2.6 안전·건강 (3)

- `SafetyTraining` · `SafetyIncident` · `HealthCheckup`

### 2.7 기타 (4)

- `EmployeeOnboarding` (1 그룹과 중복), `Appraisal` 외 세부 엔티티들은 도메인 맵 ADR-0020 에 전체 목록 박제.

전체 엔티티 합은 47. 신규 엔티티 추가 시 반드시 ADR-0020 을 개정한다.

---

## 3. 이벤트 체인 7종 흐름

hr 는 외부 시스템과 이벤트 기반으로 통신한다. 7 종이 공식 이벤트이며 `events/handlers.py` 에서 구독 등록된다.

### 3.1 `employee.hired`

**트리거** — `POST /employees/` 성공 + 상태 `active`
**후속 처리** — 온보딩 체크리스트 생성, 계정 프로비저닝 (gateway `auth` 서비스), payroll 등록
**구현 위치** — `events/handlers.py:on_employee_hired`

```
POST /employees/  →  emit(employee.hired)
    ├─→ EmployeeOnboarding 자동 생성
    ├─→ gateway.users 생성 (SCIM off 시)
    └─→ payroll.employee_master 동기화
```

### 3.2 `employee.terminated`

**트리거** — `POST /employees/{id}/terminate` 또는 `EmployeeOffboarding.status=completed`
**후속 처리** — 오프보딩 워크플로, 계정 회수, 최종 정산, PII 보존 기간 설정
**구현 위치** — `events/handlers.py:on_employee_terminated`

### 3.3 `employee.transferred`

**트리거** — `PUT /employee-transfers/{id}` 로 상태 `approved`
**후속 처리** — 조직도 재계산, 보고라인 재매핑, 결재권 갱신

### 3.4 `department.reorganized`

**트리거** — 부서 `create/update/delete`, 또는 `Department.parent_id` 변경
**후속 처리** — 조직도 캐시 무효화, BI 보고 갱신

### 3.5 `designation.changed`

**트리거** — 직원의 `designation_id` 변경 또는 Designation 자체 변경
**후속 처리** — payroll 등급 재매핑, 결재권 재매핑

### 3.6 `payroll.run.completed`

**트리거** — **외부 payroll 서비스** 가 emit. hr 는 소비자.
**후속 처리** — 명세서 알림, `LeaveBalance` 보정 (무급휴가 반영), 회계 분개 트리거

### 3.7 `leave_application.approved`

**트리거** — `PUT /leave-applications/{id}` 상태 `approved`
**후속 처리** — `LeaveBalance` 차감, `Attendance` 자동 생성 (휴가일 표시), 대체 인력 통보

### 3.8 구독 등록 시점

hr 는 accounting 과 달리 FastAPI 기동 시점 명시 호출 패턴을 사용한다.

```python
# services/hr/hr/oneerp_hr_app/main.py
from .events import event_registry
from .events.handlers import register_handlers

app = create_service_app(...)
register_handlers(event_registry)  # 7 handlers subscribe
```

---

## 4. 주요 API

### 4.1 인증

모든 요청은 `Authorization: Bearer <JWT>` 헤더와 `X-Tenant-Id` 헤더가 필요하다. gateway 가 JWT 검증·tenant 라우팅을 선행한 뒤 hr 에 전달한다.

### 4.2 직원

- `GET /employees/` — 직원 목록 (pagination)
- `GET /employees/directory` — 공개 디렉토리 (급여·주민번호 제외)
- `GET /employees/{id}` — 단건
- `POST /employees/` — 신규 등록
- `PUT /employees/{id}` — 업데이트
- `DELETE /employees/{id}` — 소프트 삭제 (상태 `terminated` 로 전이)

### 4.3 부서 / 직급

- `GET /departments/tree` — 재귀 계층 트리
- `GET /designations/hierarchy` — 직급 체계

### 4.4 근태

- `GET /attendances/report?period=YYYY-MM` — 월별 집계
- `GET /attendances/weekly-summary` — 주간 요약
- `POST /attendances/{id}/check-out` — 체크아웃

### 4.5 휴가

- `GET /leave-types/` — 활성 휴가 유형 카탈로그
- `POST /leave-applications/` — 휴가 신청
- `PUT /leave-applications/{id}` — 승인/반려
- `POST /leave-balances/grant-annual` — 연차 자동 부여 (관리자)
- `POST /leave-balances/carry-forward` — 이월 처리 (연말 배치)

---

## 5. 권한 모델

### 5.1 역할

| 역할 | 권한 요약 |
|---|---|
| `hr_viewer` | 디렉토리·조직도 조회. 급여·주민번호 등 민감 필드 차단 |
| `hr_editor` | 직원 CRUD, 발령/휴가 신청 작성, 근태 수정 |
| `hr_admin` | 퇴사 처리, 조직 개편, 급여 필드 접근, PII 조회 |
| `payroll_admin` | 월급·급여 등급 조회 한정 (hr 측 진입점 기준) |

### 5.2 민감 필드 차단

다음 필드는 `hr_admin` 또는 `payroll_admin` 만 조회 가능. 일반 역할은 응답에서 자동 제거.

- `Employee.national_id` (주민등록번호)
- `Employee.bank_account`
- `Employee.salary_grade`
- `Employee.payroll_* ` 모든 prefix

### 5.3 OPA 정책

역할 경계는 `policies/hr/routes.rego` (G3-3) 로 강제된다. 본 매뉴얼은 정책의 운영 설명, ADR-0020 §D7 이 정책의 설계 근거이다.

---

## 6. 개인정보 처리 규약

### 6.1 최소 수집 원칙

hr 는 마스터 데이터만 보관. 주민등록번호/은행계좌는 **payroll** 이 전담한다. hr 측 `Employee` 는 표시명·직책·연락처 수준만 가진다.

### 6.2 접근 통제

- hr_viewer: 업무 필드만
- hr_editor: 위 + 편집 권한
- hr_admin: 전체 + PII + 급여 뷰

모든 접근은 `audit_events` 로 기록. 감사 액션 화이트리스트는 `audit_hooks.MODULE_ACTIONS`.

### 6.3 보존 정책

`EmployeeOffboarding.data_retention_until` 필드가 보존 종료일을 명시. 기본값은 근로기준법 §42 에 따라 5년. 만료 시 `on_employee_terminated` 후속 배치 job 이 PII 를 익명화한다.

### 6.4 동의 관리

채용 단계에서 개인정보 처리 동의를 받아 `JobApplicant.consent_received_at` 에 저장. 동의 철회 시 `terminated` 처리 후 즉시 익명화 큐에 등록.

---

## 7. 퇴사 데이터 처리

### 7.1 절차

1. `POST /employees/{id}/terminate` 또는 `EmployeeOffboarding` 생성
2. 상태 전이: `active` → `offboarding` → `terminated`
3. `data_retention_until` 설정 (기본 today + 5y)
4. `employee.terminated` 이벤트 emit
5. 구독자(payroll, gateway) 가 각자 후속 처리
6. 배치 job 이 `retention_until` 만료 시 PII 익명화

### 7.2 즉시 익명화 케이스

- 채용 단계 탈락자: 탈락 확정 후 30일
- 동의 철회자: 즉시
- 법적 요청(GDPR Right to be Forgotten): 확인 후 30일 이내

### 7.3 보존 필드

퇴사 후에도 통계·감사 목적으로 다음은 보존:

- 재직기간·직급·부서 이력(익명화된 해시 키 기반)
- 급여 지급 이력(payroll 소관, hr 는 이벤트 로그만)

---

## 8. 감사 이벤트 (G3-4)

`audit_hooks.py` 의 `emit()` 헬퍼가 모든 변경을 기록한다.

```python
MODULE_ACTIONS = (
    "hr.create", "hr.update", "hr.delete",
    "hr.submit", "hr.approve", "hr.reject", "hr.cancel",
)
```

화이트리스트 외 액션은 `hr.unknown.<action>` 으로 강제 라벨링되어 감사 누락을 방지한다. 모든 emit 은 `actor · action · resource · tenant_id · details` 를 기록.

---

## 9. 설정 (HRSettings)

`HRSettings` 는 `CoreSettings` 를 상속하며 hr 고유 환경변수를 추가한다.

| 환경변수 | 기본값 | 설명 |
|---|---|---|
| `ONEERP_HR_LDAP_URL` | "" | LDAP 서버 URL (선택) |
| `ONEERP_HR_SCIM_ENABLED` | false | SCIM 동기화 on/off |
| `ONEERP_HR_PAYROLL_WEBHOOK` | "" | 외부 payroll 서비스 웹훅 |

기동 시 hr 는 SCIM 모드를 로그로 명시한다.

---

## 10. FAQ

### Q1. 직원 등록 후 gateway 계정이 자동 생성되지 않습니다.

A. `HRSettings.hr_scim_enabled=true` 인 경우 IdP 가 마스터이므로 gateway 계정은 IdP 프로비저닝을 통해 생성된다. off 모드에서만 hr→gateway 호출이 발생한다. 환경변수를 확인하라.

### Q2. 퇴사 처리 이후에도 급여 명세가 조회됩니다.

A. 정상이다. 퇴사 후에도 payroll 소관으로 지급 이력은 보존된다. hr 는 `employee.terminated` 이벤트만 emit 하며, payroll 의 보존 정책은 별도이다.

### Q3. 휴가 신청 승인 후 잔액이 즉시 차감되지 않습니다.

A. `leave_application.approved` 이벤트 핸들러가 비동기로 `LeaveBalance` 를 차감한다. 수 초 지연은 정상. 1분 이상 지연 시 `on_leave_approved` 로그를 확인하라.

### Q4. 부서 개편 후 보고라인이 그대로 입니다.

A. `department.reorganized` 이벤트 발생 후 조직도 캐시가 무효화되며, 직원의 보고라인은 `employee.transferred` 로만 갱신된다. 대량 개편 시 `POST /employees/bulk-reassign` 을 사용하라 (관리자 전용).

### Q5. SCIM 연동을 켜려면?

A. IdP 측 SCIM 엔드포인트 준비 후, `ONEERP_HR_SCIM_ENABLED=true` 설정. 기존 직원 데이터와의 충돌 해결은 운영 툴 `scripts/hr/scim-sync-dryrun.py` (ADR-0020 §D5) 로 선행 검증한다.

### Q6. G5-1 증거로 이 매뉴얼이 충분한가?

A. T1 수준(오프라인·코드 근거)으로 충분하다. T2/T3 는 G2-1 (SLO 실측)·G4-2 (런북)에서 박제된다.

---

## 11. 운영 절차 (Operational Playbook)

### 11.1 월말 마감 체크리스트

매월 말일 다음 순서로 수행한다.

1. 모든 미승인 근태 일괄 확인 — `GET /attendances/report?status=pending`
2. 미승인 휴가 일괄 처리 — `GET /leave-applications/?status=pending`
3. 월별 이상 근태 탐지 — 32시간 이상 초과근무자 리스트
4. 초과근무 승인 내역 — payroll 로 전달 (이벤트 `employee.transferred` 는 아님)
5. 직원 마스터 변경분 동기화 — SCIM on 모드인 경우 delta push

### 11.2 연차 부여 (연초)

회계연도 시작 시 `POST /leave-balances/grant-annual` 을 관리자 권한으로 1회 실행.

```
Body:
  {
    "period": "2026",
    "leave_type": "annual",
    "tenant_id": "<tenant>"
  }
```

이 호출은 모든 재직자에게 연차 기본량을 부여한다. 중복 호출은 멱등(`idempotent`) 으로 설계 — 동일 period 에 2번째 호출은 no-op.

### 11.3 연말 이월

회계연도 종료 시 `POST /leave-balances/carry-forward` 를 1회 실행. 이월 한도는 `LeavePolicy.max_carry_forward` 에 따른다. 한도 초과 분은 소멸.

### 11.4 직원 대량 이동

부서 통폐합 등으로 수십 명을 동시에 이동시킬 때는 단건 `EmployeeTransfer` 를 반복하면 이벤트 폭주가 발생한다. 대신 관리자 엔드포인트 `POST /employees/bulk-reassign` (hr_admin only) 을 쓴다. 이 엔드포인트는 내부적으로 `department.reorganized` 1회 + `employee.transferred` batch 를 emit 한다.

### 11.5 오프보딩

1. `EmployeeOffboarding` 생성 (사유·마지막 근무일·장비 반납 체크리스트)
2. 오프보딩 체크리스트 완료
3. `PUT /employees/{id}` 로 상태 `terminated`
4. `employee.terminated` 이벤트 → payroll 정산 + gateway 계정 회수 + 보존 타이머 시작

---

## 12. 문제 해결

### 12.1 흔한 오류

| 증상 | 원인 | 조치 |
|---|---|---|
| `403 민감 필드 접근 거부` | 역할 미부여 | hr_admin 위임 받거나 필드 제거 |
| `409 휴가 잔액 부족` | 잔액 < 신청일수 | `GET /leave-balances/{emp_id}/summary` 확인 |
| `422 부서 순환 참조` | `Department.parent_id` 가 자기 자신 또는 후손 | tree 재설계 |
| `500 forward-ref not fully defined` | pydantic v2 model_rebuild 미완 | 모델에 `model_rebuild()` 호출 추가 |

### 12.2 로깅

hr 서비스 로그는 `ONEERP_LOG_LEVEL` 로 제어. 이벤트 핸들러는 모두 `logger.debug` 로 수신 확인 로그를 남긴다. 운영환경에서는 `INFO` 로 충분. 디버그 시에만 `DEBUG`.

### 12.3 핸들러 장애 대응

이벤트 핸들러 실패 시 DLQ(Dead Letter Queue) 로 전달. `audit_events` 컬렉션에서 `action=hr.unknown.*` 검색 시 실패 사례 집계 가능. G3-4 gate 가 이를 mutation test 로 박제한다.

---

## 13. 참조 명령어 요약

```bash
# 서비스 기동
uv run --package oneerp-hr --directory services/hr/hr \
  uvicorn oneerp_hr_app.main:app --port 8083

# 단위 테스트
uv run pytest services/hr/hr/tests/unit/ -v

# 보안 테스트 (G3-1)
uv run pytest services/hr/hr/tests/security/ -v

# 린트
uv run ruff check services/hr/hr/

# 의존성 감사 (G3-5)
uv run pip-audit --format json --progress-spinner off --skip-editable

# OpenAPI 덤프 (pydantic 이슈 해결 후)
uv run --package oneerp-hr --directory services/hr/hr \
  python -c "from oneerp_hr_app.main import app; import json; print(json.dumps(app.openapi()))"
```

---

## 개요

HR 모듈은 조직·인사·근태·급여·퇴사 라이프사이클을 다루는 핵심 도메인이다. 본 섹션은 상단 `## 1. 개요` 를 요약한 사용자 관점 개요이며, 상세 도메인 설계는 `## 2. 도메인 모델` 이하를 참조한다.

- **적용 범위** — 정규직 · 계약직 · 외부 인력 프로파일, 조직도, 근태, 급여(`payroll` 모듈 연동), 퇴사·이직 프로세스.
- **대상 사용자** — HR 담당자 · 조직장 · 전체 임직원(본인 정보 조회) · 급여 담당 · 감사.
- **핵심 원칙** — 개인정보 최소수집 · 목적 제한 · 접근 로깅 의무(`## 6. 개인정보 처리 규약`).
- **연관 모듈** — payroll(급여) · approval(결재) · directory(조직) · documents(서명 문서).

## 시작하기

1. **로그인** — SSO(`https://erp.example.com`) 접속 후 사번·비밀번호·2FA. 신규 입사자는 채용 담당자가 생성한 임시 계정으로 최초 접속 시 비밀번호 변경 강제.
2. **권한 신청** — 기본 프로파일은 본인 정보 조회 + 자사 조직도 열람. HR 편집 역할(`hr_editor`), 급여 담당 역할(`payroll_admin`)은 상위 승인 필요. 퇴사 처리·PII 조회가 필요한 역할은 `hr_admin` 위임이 별도 필요하다. 역할 정본은 ADR-0020 §D7 · `policies/hr/routes.rego`.
3. **첫 접속 체크** — `HR > 마이페이지` 에서 인사정보·계좌·비상연락처 최신화. 누락 시 급여 지급·세액 공제 계산이 지연될 수 있다.
4. **모바일** — iOS/Android 앱(`OneERP Mobile`)에서 근태 체크인·전자결재 가능.
5. **헬프데스크** — 인사 문의 `#hr-support`, 시스템 장애 `#oncall-hr`.

## 주요 화면

핵심 화면 5종을 요약한다. (캡처는 `docs/images/hr/` 박제 예정)

| 화면 | 경로 | 역할 | 캡처 |
|------|------|------|------|
| 직원 조회 | `/hr/employees` | 조직도·검색·프로파일 열람 | `![직원조회](../images/hr/employees.png)` |
| 직원 상세 | `/hr/employees/:id` | 프로파일·경력·평가·근태 요약 | `![직원상세](../images/hr/employee-detail.png)` |
| 부서 관리 | `/hr/org` | 조직도 편집·보고라인 설정 | `![부서관리](../images/hr/org.png)` |
| 근태 | `/hr/attendance` | 출퇴근·휴가·연장근로 조회 | `![근태](../images/hr/attendance.png)` |
| 급여 | `/hr/payroll` | 급여명세·공제·지급내역 | `![급여](../images/hr/payroll.png)` |
| 퇴사 | `/hr/offboarding` | 퇴사 신청·자산 반납·인수인계 | `![퇴사](../images/hr/offboarding.png)` |

PII 접근 시 화면 우상단에 **"접근 로그 기록 중"** 배너가 표시된다.

## 자주 쓰는 작업

### 직원 조회
- 상단 검색바에 이름·사번·부서 입력. 조직장은 본인 하위 조직만, HR 담당은 전사 조회 가능.
- CSV 내보내기는 `hr_editor`/`hr_admin` 역할만 가능하며, 반드시 목적(감사 사유)을 입력해야 한다.

### 부서 편집
1. `부서 관리 > 조직도` 에서 트리 드래그로 조직 이동.
2. 보고라인 변경은 **effective_date** 필수 입력.
3. 조직 개편은 결재 승인 후에만 반영된다.

### 근태 기록·수정
- 본인 체크인/아웃은 모바일 앱 권장. 누락은 `근태 > 수정 요청` 에서 사유 기재 후 관리자 승인.
- 연장근로·야간근로는 자동 집계되며 월말 마감 전 확정.

### 급여 확인
- `급여 > 명세서` 에서 월별 PDF 다운로드. 전자 서명된 PDF는 국세청 연말정산과 호환.
- 이상 금액 발견 시 **이의신청** 버튼으로 급여 담당자에게 케이스 생성.

### 퇴사 처리
1. `퇴사 > 신청` → 퇴사일·사유·인수인계 계획 입력.
2. 자산 반납(노트북·사원증) 체크리스트 자동 생성.
3. 최종 급여·퇴직금 계산 후 **근로자 서명** 필수.
4. 퇴사 확정 시 계정 비활성화·SSO 토큰 폐기 자동 실행.

### PII 접근
- HR 담당이 타 직원의 주민등록번호·계좌번호를 열람하는 모든 행위는 **접근 목적 필수 입력** + 감사 이벤트 기록(`audit.hr.pii.read`).

## 설정

관리자(`hr_admin`) 전용. 모든 변경은 감사 로그로 박제된다.

- **권한(Role)** — `hr_viewer` · `hr_editor` · `hr_admin` · `payroll_admin` 4 역할 (ADR-0020 §D7 · `policies/hr/routes.rego` 정본). 조직 scope 분리 지원. 과거 문서에 등장하던 `hr.officer`/`hr.manager`/`hr.payroll` 5단계 네이밍은 `hr_editor`/`hr_editor`/`payroll_admin` 로 매핑·폐기되었다.
- **조직/직무(Org/Position)** — 부서 트리, 직위·직책·호봉 테이블 관리.
- **근태 정책(Attendance Policy)** — 근무제 유형(표준/유연/재량), 주 52시간 한도 알림, 휴가 한도·이월 규칙.
- **급여 정책(Payroll Policy)** — 급여항목·공제항목·세율 연동(`payroll` 모듈과 공유).
- **PII 설정** — 수집 항목 · 보관 기간 · 암호화 키 로테이션(90일). 법정 의무 기간 경과 시 자동 폐기 스케줄.
- **알림(Notification)** — 입사·퇴사·평가·근태 이상 이벤트별 수신자 정의.

## 제한사항

- **동시 편집 제한** — 동일 직원 프로파일은 한 번에 한 사람만 편집 가능(낙관적 락). 충돌 시 재시도 안내.
- **PII 조회 한도** — HR 담당 1인당 주민등록번호 조회 300건/일, 계좌번호 500건/일 초과 시 승인 필요.
- **CSV 내보내기 제한** — 1회 최대 2만 행, 일일 5만 행 한도. PII 포함 export 는 DLP 태그 자동 부착.
- **퇴사 데이터 보존** — 근로기준법 §42 및 ADR-0020 §D6 에 따라 **5년** 보존, 이후 비식별화 처리. 복원 불가.
- **조직 개편 백데이트 한도** — effective_date 는 현재 기준 -90일 ~ +365일 범위.
- **API Rate Limit** — 사용자당 300 req/min, 조회 전용 엔드포인트는 1200 req/min.
- **첨부 파일** — 건당 20MB, 직원당 총 500MB.
- **모바일 기능 제한** — 부서 편집·권한 변경·퇴사 확정은 웹 전용.

## 장애 대응

장애 유형별 1차 대응. 상세 절차는 `## 12. 문제 해결` 및 `docs/runbooks/hr/` 참조.

| 증상 | 1차 조치 | 에스컬레이션 | Runbook |
|------|---------|-------------|--------|
| SSO 로그인 실패 | 쿠키 삭제·재로그인, IAM 상태 확인 | `#iam-support` | [`sso-outage.md`](../runbooks/hr/sso-outage.md) |
| 프로파일 저장 실패 | 재시도·브라우저 로그 수집 | `#oncall-hr` | [`profile-save-error.md`](../runbooks/hr/profile-save-error.md) |
| 근태 집계 오류 | 근태 정책 재검증, 이벤트 재처리 | 근태 담당 | [`attendance-recalc.md`](../runbooks/hr/attendance-recalc.md) |
| 급여 계산 이상 | payroll 이벤트 체인 상태 확인 | 급여 담당 | [`payroll-mismatch.md`](../runbooks/hr/payroll-mismatch.md) |
| PII 접근 이상 감지 | 즉시 세션 차단·DPO 통보 | 개인정보보호책임자(DPO) | [`pii-breach.md`](../runbooks/hr/pii-breach.md) |
| 퇴사 프로세스 중단 | 인수인계 상태·결재 상태 확인 | HR 담당 | [`offboarding-stuck.md`](../runbooks/hr/offboarding-stuck.md) |

장애 신고 시 **사번 · 화면 경로 · 타임스탬프 · 스크린샷 · PII 포함 여부**를 전달한다. PII 관련 사고는 DPO에 24시간 이내 보고 의무.

## FAQ

상단 `## 10. FAQ` 의 사용자 관점 요약이다.

**Q. 주민등록번호는 왜 요구하나요?**
A. 원천징수·4대 보험 신고 법정 의무 항목이다. 수집 후 즉시 암호화되며, 열람은 감사 로그로 기록된다.

**Q. 퇴사 후 내 정보는 어떻게 되나요?**
A. 근로기준법 §42 및 ADR-0020 §D6 에 따라 **5년간** 보존된 뒤 비식별화 처리된다. 보존 기간 중 본인 요청 시 사본 제공 가능.

**Q. 조직장이 팀원 계좌번호를 볼 수 있나요?**
A. 기본 권한으로는 불가하다. 급여 담당(`payroll_admin`) 역할만 가능하며, 모든 열람은 기록된다.

**Q. 모바일에서 퇴사 신청을 완료할 수 있나요?**
A. 신청 접수는 가능하나, **최종 확정 서명·자산 반납 체크리스트** 는 웹에서만 처리한다.

**Q. 근태 수정은 언제까지 가능한가요?**
A. 해당 월 마감 전(익월 5영업일)까지 관리자 승인으로 수정 가능하다. 마감 이후는 인사팀 예외 승인 필요.

**Q. PII 접근 기록은 누가 볼 수 있나요?**
A. DPO · 내부감사 · HR admin 만 조회 가능하며, `audit.hr.pii.*` 이벤트로 WORM 저장소에 보존된다.

## 14. 변경 이력

| 날짜 | 버전 | 주요 변경 |
|---|---|---|
| 2026-04-22 | 0.1.0 | G5-1 최초 박제 · Spec III Wave C-2 · ADR-0020 병행 수립 |
| 2026-04-22 | 0.1.1 | 필수 섹션 보강 (개요/시작하기/주요 화면/자주 쓰는 작업/설정/제한사항/장애 대응/FAQ) · G5-1 엔진 요건 충족 |
| 2026-04-22 | 0.1.2 | DOC-AUDIT C2 해소 · 역할 네이밍 `hr_viewer/hr_editor/hr_admin/payroll_admin` 4종 통일 · PII 보존 5년 단일화 (ADR-0020 §D6/§D7 정본) |

<!-- DOC-AUDIT C2 해소: 2026-04-22 — 역할 5단계(hr.officer/manager/payroll/admin/employee)를 ADR-0020/OPA 정본 4 역할(hr_viewer/hr_editor/hr_admin/payroll_admin)로 통일 · PII 보존 3년→5년 단일화 -->
