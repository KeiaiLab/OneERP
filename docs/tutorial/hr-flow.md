---
module: hr
tier: T1
gate: G5-2
audience: 개발자 / 운영 관리자
estimated_time: 45분
last_updated: 2026-04-22
---

# OneERP HR — 직원 생애주기 튜토리얼

이 튜토리얼은 **신규 입사자 등록 → 부서 배치 → 근태 기록 → 급여 연동 이벤트 → 퇴사 처리** 의 전 체인을 step-by-step 으로 실행한다. 단위 테스트/통합 테스트 작성 전에 hr API 의 실제 동작과 이벤트 흐름을 체화하는 것이 목표이다.

> **Scope** — T1 (오프라인 · curl 예시 중심) 수준. 실제 staging 요청 로그는 G2-1 (T2) 에서 박제된다.
> 본 튜토리얼은 로컬 개발 환경에서 실행 가능하다. gateway 를 경유하지 않고 hr 에 직접 호출하는 예시를 제공하며, 실제 배포 시에는 gateway 를 거쳐야 한다.

---

## 사전 준비

### 환경

```bash
export ONEERP_JWT_SECRET="test-jwt-secret-32bytes-minimum-value-local-dev-only-0123456789"
export ONEERP_DEBUG=true
export ONEERP_TENANT_ID=tenant-demo
export HR_BASE_URL="http://localhost:8083"
export AUTH_TOKEN="eyJhbGc...[hr_admin 역할 JWT]"
```

### 서비스 기동

```bash
uv run --package oneerp-hr --directory services/hr/hr \
  uvicorn oneerp_hr_app.main:app --port 8083 --reload
```

### 공통 헤더

```bash
H_AUTH="Authorization: Bearer ${AUTH_TOKEN}"
H_TENANT="X-Tenant-Id: ${ONEERP_TENANT_ID}"
H_JSON="Content-Type: application/json"
```

이후 모든 `curl` 예시는 위 세 헤더를 사용한다.

---

## Step 1 — 부서 및 직급 사전 등록

신규 입사자를 등록하려면 부서·직급 레코드가 먼저 존재해야 한다.

### 1.1 부서 생성

```bash
curl -sX POST "${HR_BASE_URL}/departments/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "name": "엔지니어링",
    "code": "ENG",
    "parent_id": null,
    "manager_id": null
  }'
```

**예상 응답**

```json
{
  "_id": "DEPT-0001",
  "name": "엔지니어링",
  "code": "ENG",
  "parent_id": null,
  "manager_id": null,
  "created_at": "2026-04-22T10:00:00Z"
}
```

### 1.2 하위 부서 생성

```bash
curl -sX POST "${HR_BASE_URL}/departments/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "name": "플랫폼팀",
    "code": "ENG-PLATFORM",
    "parent_id": "DEPT-0001"
  }'
```

### 1.3 직급 생성

```bash
curl -sX POST "${HR_BASE_URL}/designations/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "name": "시니어 엔지니어",
    "code": "SE",
    "level": 5
  }'
```

### 1.4 계층 확인

```bash
curl -s "${HR_BASE_URL}/departments/tree" -H "${H_AUTH}" -H "${H_TENANT}"
curl -s "${HR_BASE_URL}/designations/hierarchy" -H "${H_AUTH}" -H "${H_TENANT}"
```

`department.reorganized` 이벤트가 emit 되었는지 서버 로그에서 확인:

```
DEBUG department.reorganized 수신 event_id=evt_... payload={...}
```

---

## Step 2 — 신규 직원 등록

### 2.1 직원 생성

```bash
curl -sX POST "${HR_BASE_URL}/employees/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "employee_code": "EMP-2026-0001",
    "name": "김개발",
    "email": "kim.dev@example.com",
    "phone": "+82-10-1234-5678",
    "department_id": "DEPT-0002",
    "designation_id": "DSG-0001",
    "hire_date": "2026-05-01",
    "status": "active"
  }'
```

**응답**

```json
{
  "_id": "EMP-0001",
  "employee_code": "EMP-2026-0001",
  "name": "김개발",
  "department_id": "DEPT-0002",
  "designation_id": "DSG-0001",
  "status": "active",
  "hire_date": "2026-05-01"
}
```

### 2.2 이벤트 확인

서버 로그에 다음 2 라인이 나와야 한다.

```
DEBUG employee.hired 수신 event_id=evt_e... payload={...employee_id=EMP-0001...}
DEBUG designation.changed 수신 event_id=evt_d... payload={...}
```

### 2.3 디렉토리 조회 (hr_viewer 시점)

```bash
curl -s "${HR_BASE_URL}/employees/directory" -H "${H_AUTH}" -H "${H_TENANT}" | jq
```

응답에 `national_id`, `salary_grade`, `bank_account` 가 **포함되지 않아야 한다**. 포함되면 권한 모델이 깨진 것 — G3-3 OPA 테스트로 박제할 대상.

---

## Step 3 — 온보딩 체크리스트

`employee.hired` 이벤트 후속 처리로 `EmployeeOnboarding` 이 자동 생성된다 (Spec III 후속 로직 구현 예정). 현재는 수동 생성 예시.

```bash
curl -sX POST "${HR_BASE_URL}/employee-onboardings/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "employee_id": "EMP-0001",
    "checklist": [
      {"item": "노트북 지급", "done": false},
      {"item": "사번 발급", "done": false},
      {"item": "보안 교육 이수", "done": false}
    ]
  }'
```

### 3.1 체크리스트 업데이트

```bash
curl -sX PUT "${HR_BASE_URL}/employee-onboardings/ONB-0001" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "checklist": [
      {"item": "노트북 지급", "done": true},
      {"item": "사번 발급", "done": true},
      {"item": "보안 교육 이수", "done": false}
    ]
  }'
```

---

## Step 4 — 발령 (Transfer)

### 4.1 발령 요청 생성

```bash
curl -sX POST "${HR_BASE_URL}/employee-transfers/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "employee_id": "EMP-0001",
    "from_department_id": "DEPT-0002",
    "to_department_id": "DEPT-0001",
    "effective_date": "2026-07-01",
    "reason": "본부 직속 이관"
  }'
```

### 4.2 발령 승인

```bash
curl -sX PUT "${HR_BASE_URL}/employee-transfers/XFR-0001" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{"status": "approved"}'
```

**발생 이벤트** — `employee.transferred`
**후속 처리** — 조직도 재계산 · 보고라인 재매핑 · 결재권 재매핑

### 4.3 변경 확인

```bash
curl -s "${HR_BASE_URL}/employees/EMP-0001" -H "${H_AUTH}" -H "${H_TENANT}" | jq .department_id
# → "DEPT-0001"
```

---

## Step 5 — 근태 기록

### 5.1 체크인

```bash
curl -sX POST "${HR_BASE_URL}/attendances/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "employee_id": "EMP-0001",
    "date": "2026-05-01",
    "check_in": "09:00",
    "shift_type_id": "SHIFT-DAY"
  }'
```

### 5.2 체크아웃

```bash
curl -sX POST "${HR_BASE_URL}/attendances/ATT-0001/check-out" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{"check_out": "18:30"}'
```

### 5.3 주간 요약

```bash
curl -s "${HR_BASE_URL}/attendances/weekly-summary?employee_id=EMP-0001&week=2026-W18" \
  -H "${H_AUTH}" -H "${H_TENANT}" | jq
```

---

## Step 6 — 휴가 신청 및 승인

### 6.1 연차 잔액 조회

```bash
curl -s "${HR_BASE_URL}/leave-balances/?employee_id=EMP-0001" -H "${H_AUTH}" -H "${H_TENANT}" | jq
```

### 6.2 연차 부여 (없을 경우, 관리자)

```bash
curl -sX POST "${HR_BASE_URL}/leave-balances/grant-annual" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{"period": "2026", "leave_type": "annual", "employee_ids": ["EMP-0001"]}'
```

### 6.3 휴가 신청

```bash
curl -sX POST "${HR_BASE_URL}/leave-applications/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "employee_id": "EMP-0001",
    "leave_type_id": "LT-ANNUAL",
    "start_date": "2026-06-10",
    "end_date": "2026-06-11",
    "reason": "개인 사유"
  }'
```

### 6.4 승인

```bash
curl -sX PUT "${HR_BASE_URL}/leave-applications/LA-0001" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{"status": "approved", "approved_by": "MGR-0001"}'
```

**발생 이벤트** — `leave_application.approved`
**후속 처리** — `LeaveBalance` 차감 · 해당 날짜 `Attendance` 자동 생성(휴가일)

### 6.5 잔액 재확인

```bash
curl -s "${HR_BASE_URL}/leave-balances/LB-0001/summary" -H "${H_AUTH}" -H "${H_TENANT}" | jq
```

잔액이 2일 차감되었는지 확인.

---

## Step 7 — 급여 연동 이벤트 (payroll → hr)

payroll 서비스에서 월 급여 처리 완료 시 `payroll.run.completed` 이벤트가 발생한다. hr 는 이 이벤트의 **소비자**.

### 7.1 이벤트 시뮬레이션 (개발 환경)

실제로는 payroll 서비스가 emit 하지만, 로컬에서 수동 트리거:

```bash
curl -sX POST "${HR_BASE_URL}/_internal/events/emit" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "event_type": "payroll.run.completed",
    "payload": {
      "period": "2026-05",
      "employee_ids": ["EMP-0001"],
      "total_amount": 5000000
    }
  }'
```

(실제 `_internal` 엔드포인트는 테스트 환경에서만 노출된다.)

### 7.2 핸들러 로그

```
DEBUG payroll.run.completed 수신 event_id=evt_p... payload={'period':'2026-05', ...}
```

hr 측 후속 로직(명세서 알림, 무급휴가 차감 등)은 Spec III 후속 셀에서 구현.

---

## Step 8 — 직급 변경

### 8.1 PUT 으로 designation 변경

```bash
curl -sX PUT "${HR_BASE_URL}/employees/EMP-0001" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{"designation_id": "DSG-0002"}'
```

**발생 이벤트** — `designation.changed`
**후속 처리** — payroll 등급 재매핑 · 결재권 재매핑

### 8.2 직급 체계 확인

```bash
curl -s "${HR_BASE_URL}/designations/hierarchy" -H "${H_AUTH}" -H "${H_TENANT}" | jq
```

---

## Step 9 — 퇴사 처리

### 9.1 오프보딩 레코드 생성

```bash
curl -sX POST "${HR_BASE_URL}/employee-offboardings/" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "employee_id": "EMP-0001",
    "last_working_day": "2026-12-31",
    "reason": "개인 사유",
    "equipment_return_required": true,
    "data_retention_until": "2031-12-31"
  }'
```

### 9.2 체크리스트 완료

```bash
curl -sX PUT "${HR_BASE_URL}/employee-offboardings/OFB-0001" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{
    "checklist": [
      {"item": "장비 반납", "done": true},
      {"item": "VPN 계정 회수", "done": true},
      {"item": "인수인계 문서", "done": true}
    ],
    "status": "completed"
  }'
```

### 9.3 직원 상태 `terminated` 로 전이

```bash
curl -sX PUT "${HR_BASE_URL}/employees/EMP-0001" \
  -H "${H_AUTH}" -H "${H_TENANT}" -H "${H_JSON}" \
  -d '{"status": "terminated", "terminated_at": "2026-12-31"}'
```

**발생 이벤트** — `employee.terminated`
**후속 처리**
1. gateway 계정 회수 (SCIM off 시)
2. payroll 최종 정산 트리거
3. `data_retention_until` 기반 PII 익명화 타이머 시작

### 9.4 로그 확인

```
DEBUG employee.terminated 수신 event_id=evt_t... payload={...}
```

---

## Step 10 — 감사 이벤트 확인

모든 변경은 `audit_events` 컬렉션에 기록되어야 한다.

```bash
# FerretDB shell 에서
use audit_db
db.audit_events.find({
  tenant_id: "tenant-demo",
  action: /^hr\./
}).sort({ created_at: -1 }).limit(10)
```

최소 다음 7 액션이 관찰되어야 한다.

- `hr.create` (부서/직급/직원/온보딩)
- `hr.update` (직원 업데이트, 발령 승인, 휴가 승인)
- `hr.submit` (휴가 신청)
- `hr.approve` (휴가 승인)
- `hr.delete` (선택적 — 본 튜토리얼 미사용)
- `hr.cancel` (선택적)
- `hr.reject` (선택적)

---

## Step 11 — 검증 (테스트 실행)

로컬에서 관련 테스트를 모두 실행하여 튜토리얼 flow 가 실제 구현과 일치하는지 확인.

```bash
# 단위 테스트 154건
uv run pytest services/hr/hr/tests/unit/ -v

# 보안 테스트 (G3-1)
uv run pytest services/hr/hr/tests/security/ -v

# 린트
uv run ruff check services/hr/hr/
```

---

## 이벤트 타임라인 시각화

본 튜토리얼 수행 시 발생하는 7개 이벤트의 시간적 순서는 다음과 같다.

```
T+00:00  POST /departments/          → department.reorganized
T+00:01  POST /designations/         → (이벤트 없음, 생성뿐)
T+00:02  POST /employees/            → employee.hired, designation.changed
T+00:10  PUT  /employee-transfers/X  → employee.transferred, department.reorganized
T+00:15  POST /attendances/{}/check-out (이벤트 없음)
T+00:20  PUT  /leave-applications/Y  → leave_application.approved
T+00:30  (외부) payroll 처리 완료    → payroll.run.completed (소비)
T+00:40  PUT  /employees/{id}        → designation.changed
T+00:50  PUT  /employees/{id} terminated → employee.terminated
```

총 7 종 이벤트 중 `payroll.run.completed` 를 제외한 6 개가 hr 내부에서 emit 되며, `payroll.run.completed` 는 외부에서 수신.

---

## 트러블슈팅

### T1. JWT 검증 실패

```
401 ONEERP_JWT_SECRET 검증 실패
```

→ `ONEERP_JWT_SECRET` 환경변수가 32바이트 이상인지 확인. 개발 기본값을 프로덕션에서 사용하면 기동 자체가 실패한다.

### T2. 이벤트 핸들러 미동작

로그에 `DEBUG ... 수신` 이 나오지 않는 경우:

1. `main.py` 의 `register_handlers(event_registry)` 호출이 살아있는지 확인
2. `ONEERP_LOG_LEVEL=DEBUG` 설정
3. accounting 방식(전역 데코레이터) 과 혼동하지 말 것 — hr 는 명시 호출

### T3. pydantic forward-ref 에러

```
PydanticUserError: `TypeAdapter[...LeavePeriodCreate...]` is not fully defined
```

→ 해당 모델 파일 끝에 `<Model>.model_rebuild()` 추가 필요. G1-2 OpenAPI 정식 덤프를 위해 반드시 해결해야 한다.

### T4. 권한 응답 403

```
403 Forbidden - 급여 필드 접근 거부
```

→ 현재 JWT 의 role 이 `hr_viewer` 일 수 있음. `hr_admin` 역할이 있는 토큰으로 재시도.

---

## 다음 단계

1. **G1-3 통합 테스트** — 본 튜토리얼의 10 단계를 pytest 로 자동화.
2. **G3-1 AuthN** — 본 튜토리얼의 각 호출에 대한 7종 JWT 공격 시나리오 테스트.
3. **G3-3 OPA** — 본 튜토리얼의 권한 경계를 rego 정책으로 박제.
4. **G5-2 Playwright** — 본 튜토리얼을 프론트엔드 UX 테스트로 확장 (Wave D).

---

## 참조

- 매뉴얼: `docs/manual/hr.md`
- ADR-0020: `docs/kb/adr/0020-hr-bounds.md`
- Plan: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md` §Wave C-2
- 이벤트 구현: `services/hr/hr/oneerp_hr_app/events/handlers.py`
- 감사 훅: `services/hr/hr/oneerp_hr_app/audit_hooks.py`
