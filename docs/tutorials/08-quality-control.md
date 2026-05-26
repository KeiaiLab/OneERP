# 튜토리얼: Quality Control (품질관리) / Tutorial: Quality Control

## 개요 (Overview)

품질 검사 (Inspection) 생성에서 불합격 시 부적합 (Non-Conformance, NC) 자동 생성,
심각도 에스컬레이션 (Escalation), NC 해결, 시정예방조치 (CAPA) 생성과 마감까지의
전체 품질관리 흐름을 단계별로 실습한다.
이 시나리오는 Quality 서비스의 `InspectionAutomationService`, `NonConformanceService`,
`CAPAService`를 활용한다.

This tutorial covers the full Quality Control flow — from inspection creation,
automatic NC generation on failure, severity escalation, NC resolution,
to CAPA creation and closure.

## 사전 조건 (Prerequisites)

- Quality 서비스가 로컬에서 기동되어 있어야 한다.
- 검사 템플릿과 관련 입고/생산 문서가 준비되어 있어야 한다.
- NC와 CAPA 흐름을 확인할 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 검사, NC, CAPA 흐름이 완료된다.
- 합격/불합격 판정과 후속 조치를 확인할 수 있다.
- 다음 CRM 파이프라인 튜토리얼로 이동할 수 있다.

## 다음 단계 (Next Step)

- [CRM 파이프라인 튜토리얼](./09-crm-pipeline.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# Quality (포트 8012 / Port 8012)
uv run --package oneerp-quality --directory services/quality \
    uvicorn app.main:app --port 8012 --reload
```

### 환경 변수 (Environment Variables)

```bash
export ONEERP_DEBUG=true
export ONEERP_FERRETDB_URI=mongodb://localhost:27017
export ONEERP_DATABASE_NAME=oneerp_dev
```

---

## Step 1: 입고 검사 자동 생성 (Trigger Incoming Inspection)

`InspectionAutomationService.trigger_incoming_inspection()` — 입고 시 자동 검사를 생성한다.
입고전표 (Purchase Receipt) 제출 시 이벤트로 자동 트리거된다.

```bash
curl -s -X POST http://localhost:8012/api/v1/inspections/trigger-incoming \
  -H "Content-Type: application/json" \
  -d '{
    "reference_no": "PREC-0001",
    "item_code": "RAW-A"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "inspection_id": "QI-0001",
  "inspection_type": "incoming"
}
```

### 공정 중 검사 (In-Process Inspection)

제조 공정 중에도 검사를 생성할 수 있다.

```bash
curl -s -X POST http://localhost:8012/api/v1/inspections/trigger-in-process \
  -H "Content-Type: application/json" \
  -d '{
    "reference_no": "STE-0005",
    "item_code": "FG-BRACKET"
  }' | jq
# 응답 (Response): {"inspection_id": "QI-0002", "inspection_type": "in_process"}
```

---

## Step 2: 검사 수행 + 결과 기록 (Perform Inspection + Record Result)

검사원이 검사를 수행하고 결과를 기록한다.

```bash
# 합격 사례 (Pass case)
curl -s -X PUT http://localhost:8012/api/v1/inspections/QI-0001 \
  -H "Content-Type: application/json" \
  -d '{
    "result": "accepted",
    "readings": [
      {"parameter": "인장강도", "standard": "400 MPa", "actual": "420 MPa", "status": "pass"},
      {"parameter": "표면결함", "standard": "없음", "actual": "없음", "status": "pass"}
    ]
  }' | jq

# 불합격 사례 (Fail case)
curl -s -X PUT http://localhost:8012/api/v1/inspections/QI-0002 \
  -H "Content-Type: application/json" \
  -d '{
    "result": "rejected",
    "readings": [
      {"parameter": "치수 공차", "standard": "+-0.05mm", "actual": "+-0.12mm", "status": "fail"},
      {"parameter": "표면 조도", "standard": "Ra 1.6", "actual": "Ra 3.2", "status": "fail"}
    ]
  }' | jq
```

---

## Step 3: 불합격 시 NC 자동 생성 (Auto-Create NC on Failure)

`InspectionAutomationService.auto_create_nc_on_failure()` — 불합격 검사에 대해
NC를 자동 생성한다. 합격이면 `null`을 반환한다.

```bash
# 합격 검사 — NC 생성 불필요 (Passed inspection — no NC needed)
curl -s -X POST http://localhost:8012/api/v1/inspections/QI-0001/check-nc | jq
# 응답 (Response): null

# 불합격 검사 — NC 자동 생성 (Failed inspection — auto-create NC)
curl -s -X POST http://localhost:8012/api/v1/inspections/QI-0002/check-nc | jq
```

### 기대 결과 (Expected Result)

```json
{
  "nc_id": "NC-0001",
  "inspection_id": "QI-0002"
}
```

NC 문서에 자동으로 검사 참조, 품목 코드, 설명이 설정된다.

---

## Step 4: NC 심각도 에스컬레이션 (Escalate NC Severity)

`NonConformanceService.escalate()` — 심각도를 상향한다.
minor -> major -> critical 순서로만 가능하며 하향은 불가하다.

```bash
curl -s -X POST http://localhost:8012/api/v1/non-conformances/NC-0001/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "new_severity": "major"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "nc_id": "NC-0001",
  "previous": "minor",
  "new": "major"
}
```

```bash
# 추가 에스컬레이션 (Further escalation)
curl -s -X POST http://localhost:8012/api/v1/non-conformances/NC-0001/escalate \
  -H "Content-Type: application/json" \
  -d '{"new_severity": "critical"}' | jq
# previous: "major" -> new: "critical"

# 하향 시도 (Downgrade attempt — fails)
curl -s -X POST http://localhost:8012/api/v1/non-conformances/NC-0001/escalate \
  -H "Content-Type: application/json" \
  -d '{"new_severity": "minor"}' | jq
# 에러 (Error): "심각도를 하향할 수 없습니다: critical → minor"
```

---

## Step 5: NC 해결 + CAPA 자동 생성 (Resolve NC + Auto-Create CAPA)

`NonConformanceService.resolve()` — NC를 해결하고 CAPA를 자동 생성한다.

```bash
curl -s -X POST http://localhost:8012/api/v1/non-conformances/NC-0001/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "corrective_action": "공정 파라미터 재설정: 절삭 속도 30% 감소, 이송 속도 20% 감소. CNC 프로그램 보정 완료."
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "nc_id": "NC-0001",
  "capa_id": "CAPA-0001"
}
```

NC의 corrective_action이 기록되고, CAPA가 자동으로 생성된다.

---

## Step 6: CAPA 상세 등록 (Register CAPA Details)

`CAPAService.create_capa_from_nc()` — NC로부터 상세 CAPA를 등록할 수도 있다.
담당자 (Responsible), 기한 (Due Date)을 설정한다.

```bash
curl -s -X POST http://localhost:8012/api/v1/capas \
  -H "Content-Type: application/json" \
  -d '{
    "nc_id": "NC-0001",
    "capa_type": "preventive",
    "corrective_action": "CNC 장비 정기 교정 주기를 월 1회로 변경. 작업자 재교육 실시.",
    "responsible": "EMP-0003",
    "due_date": "2026-04-15"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "capa_id": "CAPA-0002",
  "nc_id": "NC-0001",
  "capa_type": "preventive"
}
```

CAPA 유형:
- `corrective` — 시정조치 (발생한 문제를 해결)
- `preventive` — 예방조치 (재발 방지를 위한 조치)

---

## Step 7: CAPA 마감 (Close CAPA)

`CAPAService.close_capa()` — CAPA를 마감한다. corrective_action이 미기입이면 에러.

```bash
curl -s -X POST http://localhost:8012/api/v1/capas/CAPA-0001/close \
  -H "Content-Type: application/json" \
  -d '{
    "effectiveness_verified": true
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "capa_id": "CAPA-0001",
  "is_closed": true
}
```

---

## 검증 (Verification)

### 1. CAPA 통계 확인 (Check CAPA Statistics)

`CAPAService.get_capa_statistics()` — 총/열린/마감/초과 건수를 확인한다.

```bash
curl -s "http://localhost:8012/api/v1/capas/statistics" | jq
```

```json
{
  "total": 2,
  "open": 1,
  "closed": 1,
  "overdue": 0
}
```

### 2. 기한 초과 CAPA 조회 (Check Overdue CAPAs)

```bash
curl -s "http://localhost:8012/api/v1/capas/overdue" | jq
# due_date가 지난 미마감 CAPA 목록 (List of open CAPAs past due date)
```

### 3. NC 이력 확인 (Verify NC History)

```bash
curl -s "http://localhost:8012/api/v1/non-conformances/NC-0001" | jq
# severity: "critical", corrective_action 확인
```

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[Quality]
    |
  1. 입고/공정 검사 자동 생성
     Trigger Incoming/In-Process Inspection
    |
  2. 검사 수행 + 결과 기록
     Perform Inspection + Record Result
    |
    +-- 합격 (Pass) -> 종료
    |
    +-- 불합격 (Fail)
        |
      3. NC 자동 생성
         Auto-Create Non-Conformance
        |
      4. 심각도 에스컬레이션 (필요 시)
         Escalate Severity (minor -> major -> critical)
        |
      5. NC 해결 -> CAPA 자동 생성
         Resolve NC -> Auto-Create CAPA
        |
      6. CAPA 상세 등록 (예방조치)
         Register CAPA Details (Preventive)
        |
      7. CAPA 마감 (효과성 검증)
         Close CAPA (Effectiveness Verified)
        |
      통계/초과 모니터링
      Statistics / Overdue Monitoring
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 입고 검사 (Incoming) / 공정 중 검사 (In-Process) 자동 트리거
- 검사 불합격 시 부적합 (NC, Non-Conformance) 자동 생성
- 심각도 에스컬레이션 (Severity Escalation): minor -> major -> critical (단방향)
- NC 해결 시 CAPA (Corrective and Preventive Action) 자동 생성
- CAPA 유형: 시정 (Corrective) vs 예방 (Preventive)
- CAPA 마감 시 효과성 검증 (Effectiveness Verification) 플래그
- 기한 초과 (Overdue) CAPA 모니터링
