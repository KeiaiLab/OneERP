# 품질 모듈 (Quality Module)

## 개요 (Overview)

품질 모듈은 품질 검사 (Quality Inspection), 검사 템플릿 (Inspection Template), 부적합 관리 (Non-Conformance Management), 시정예방조치 (CAPA, Corrective and Preventive Action), 품질 목표/지표 (Quality Objectives/Metrics), 분석 성적서 (Certificate of Analysis, COA) 등 품질 관리 업무를 지원한다.

## 사전 조건 (Prerequisites)

- Quality 서비스와 검사 템플릿이 준비되어 있어야 한다.
- 부적합과 CAPA 흐름을 볼 권한이 필요하다.
- 제조/재고 문서와의 연계를 확인할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- 검사, 부적합, CAPA 흐름을 설명할 수 있다.
- 품질 목표와 지표를 확인할 수 있다.
- 다음 전자결재 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [전자결재 모듈](./13-approval.md)

## 주요 기능 (Key Features)

- 검사 템플릿 (Inspection Template)
- 품질 검사 (Quality Inspection)
- 부적합 관리 (Non-Conformance)
- 시정예방조치 (CAPA)
- 품질 목표 (Quality Objective)
- 분석 성적서 (Certificate of Analysis, COA)
- 반품 검사 (Return Inspection)
- 품질 회의 (Quality Meeting)

## 업무 흐름 (Workflow)

```
검사 실행          합격/불합격 판정      부적합 보고         CAPA
(Inspection)  → (Pass/Fail)       → (Non-Conformance) → (CAPA)
                                                            ↓
                                                      효과성 검증
                                                   (Effectiveness Review)
```

## 상세 기능 (Detailed Features)

### 검사 템플릿 (Inspection Template)

#### 설정 (Setup)
1. **품질 (Quality) > 검사 템플릿 (Inspection Template)** 에서 검사 기준을 정의한다. (Define inspection criteria.)
2. 검사 항목 (Inspection Item), 측정 방법 (Measurement Method), 합격 기준 (Acceptance Criteria: 상한 Upper Limit/하한 Lower Limit)을 설정한다.
3. 검사 유형 (Inspection Type: 입고검사 Incoming/공정검사 In-process/출하검사 Outgoing)을 지정한다.

### 품질 검사 (Quality Inspection)

#### 실행 (Execute)
1. **품질 (Quality) > 품질 검사 (Quality Inspection)** 에서 **"신규 (New)"** 를 클릭한다.
2. 검사 대상 (Inspection Target: 입고 전표 Purchase Receipt, 작업지시 Work Order, 출하 전표 Delivery Note 등)을 선택한다.
3. 검사 템플릿 (Inspection Template)이 자동 적용된다.
4. 검사 항목별 측정값 (Measured Value)을 입력한다.
5. 합격 (Pass)/불합격 (Fail)이 자동 판정된다.
6. **"제출 (Submit)"** 하면 검사 결과가 확정된다.

#### 검사 결과 조회 (View Results)
1. **품질 (Quality) > 검사 결과 (Inspection Result)** 에서 검사 이력을 조회한다.
2. 합격률 (Pass Rate) 추이, 불합격 원인별 (Failure Cause) 통계를 확인한다.

### 부적합 관리 (Non-Conformance Management)

#### 보고 (Report)
1. **품질 (Quality) > 부적합 (Non-Conformance)** 에서 **"신규 (New)"** 를 클릭한다.
2. 부적합 유형 (NC Type), 발생 공정 (Process), 관련 품목 (Item)을 입력한다.
3. 부적합 상세 내용 (Details), 사진/증거 (Photos/Evidence)를 첨부한다.
4. **"제출 (Submit)"** 하면 담당자 (Assignee)에게 배정된다.

#### 처리 (Resolve)
1. 담당자는 원인 (Root Cause)을 분석한다.
2. 처리 방법 (Disposition: 재작업 Rework/폐기 Scrap/특채 Use As-Is)을 결정한다.
3. 처리 결과를 기록하고 **"종료 (Close)"** 한다.

### 시정예방조치 (CAPA)

#### 등록 (Create)
1. **품질 (Quality) > 시정예방조치 (CAPA)** 에서 **"신규 (New)"** 를 클릭한다.
2. CAPA 유형 (Type: 시정조치 Corrective Action/예방조치 Preventive Action)을 선택한다.
3. 관련 부적합 (Non-Conformance), 원인 분석 결과 (Root Cause Analysis)를 연결한다.
4. 조치 계획 (Action Plan), 담당자 (Assignee), 완료 예정일 (Due Date)을 입력한다.

#### 추적 (Track)
1. 조치 진행 상황을 주기적으로 갱신한다. (Update action progress periodically.)
2. 완료 후 효과성 (Effectiveness)을 검증한다.
3. 효과적이면 **"종료 (Close)"**, 아니면 추가 조치를 진행한다. (Close if effective; proceed with additional actions if not.)

### 품질 목표 (Quality Objective)

1. **품질 (Quality) > 품질 목표 (Quality Objective)** 에서 부서별 (Department)/품목별 (Item) 품질 목표를 설정한다.
2. 예 (Example): 불량률 (Defect Rate) 1% 이하, 검사 합격률 (Inspection Pass Rate) 99% 이상
3. 실적을 주기적으로 추적한다. (Track performance periodically.)

### 분석 성적서 (Certificate of Analysis, COA)

1. **품질 (Quality) > 분석 성적서 (COA)** 에서 출하 품목의 품질 성적서를 생성한다. (Generate quality certificates for shipped items.)
2. 검사 결과 데이터 (Inspection Data)가 자동으로 반영된다.
3. 고객 (Customer)에게 성적서를 발행한다.

### 반품 검사 (Return Inspection)

1. **품질 (Quality) > 반품 검사 (Return Inspection)** 에서 반품된 제품의 검사를 진행한다. (Inspect returned products.)
2. 불량 원인 (Defect Cause)을 분석하고 처리 방법 (Disposition)을 결정한다.

### 품질 회의 (Quality Meeting)

1. **품질 (Quality) > 품질 회의 (Quality Meeting)** 에서 정기 품질 회의록을 관리한다. (Manage periodic quality meeting minutes.)
2. 회의 안건 (Agenda), 참석자 (Attendees), 결정 사항 (Decisions)을 기록한다.
3. 후속 조치 사항 (Follow-up Actions)을 추적한다.

## 관련 보고서 (Related Reports)

- 품질 검사 합격률 (Inspection Pass Rate)
- 부적합 현황 (Non-Conformance Status)
- CAPA 진행 현황 (CAPA Progress)
- 품질 목표 달성률 (Quality Objective Achievement)

## FAQ

- **Q: CAPA에서 시정조치 (Corrective Action)와 예방조치 (Preventive Action)의 차이는?**
  A: 시정조치는 발생한 문제를 해결하고, 예방조치는 잠재적 문제를 사전에 방지합니다. (Corrective actions address existing problems; preventive actions prevent potential problems.)

- **Q: 검사 합격 기준 (Acceptance Criteria)은 누가 설정하나요?**
  A: 품질 관리자가 검사 템플릿 (Inspection Template)에서 설정합니다. (Quality managers set criteria in Inspection Templates.)
