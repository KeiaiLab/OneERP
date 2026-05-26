# 자산 모듈 (Assets Module)

## 개요 (Overview)

자산 모듈은 고정자산 등록 (Asset Registration), 분류 (Classification), 감가상각 계산 (Depreciation Calculation), 자산 이동/처분 (Movement/Disposal), 유지보수 (Maintenance), 차량 관리 (Vehicle Management) 등 기업 자산 관리를 지원한다.

## 사전 조건 (Prerequisites)

- Assets, Accounting 서비스와 자산 마스터가 준비되어 있어야 한다.
- 감가상각과 처분 흐름을 볼 권한이 필요하다.
- 회계 분개와의 연계를 확인할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- 자산 등록, 상각, 이동, 처분 흐름을 설명할 수 있다.
- 자산 가치 변동과 회계 반영을 확인할 수 있다.
- 다음 제조 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [제조 모듈](./10-manufacturing.md)

## 주요 기능 (Key Features)

- 자산 등록 (Asset Registration)
- 자산 분류 (Asset Category)
- 감가상각 (Depreciation): 정액법 (Straight Line) / 정률법 (Declining Balance)
- 자산 이동 (Asset Movement)
- 자산 처분 (Asset Disposal)
- 자산 재평가 (Asset Revaluation)
- 유지보수 (Maintenance)
- 차량 관리 (Vehicle Management)

## 업무 흐름 (Workflow)

```
자산 등록           감가상각 처리         이동/재평가          처분
(Asset Reg.)   → (Depreciation)    → (Move/Revalue)   → (Disposal)
```

## 상세 기능 (Detailed Features)

### 자산 등록 (Asset Registration)

#### 생성 (Create)
1. **자산 (Assets) > 자산 (Asset)** 메뉴에서 **"신규 (New)"** 를 클릭한다.
2. 자산명 (Asset Name), 자산 분류 (Asset Category), 취득일 (Acquisition Date), 취득원가 (Acquisition Cost)를 입력한다.
3. 감가상각 방법 (Depreciation Method: 정액법 Straight Line/정률법 Declining Balance)과 내용연수 (Useful Life)를 선택한다.
4. 설치 위치 (Location), 관리 부서 (Department)를 지정한다.
5. **"저장 (Save)"** 을 클릭한다.

### 자산 분류 (Asset Category)

1. **자산 (Assets) > 자산 분류 (Asset Category)** 에서 분류 체계를 설정한다. (Set up the classification hierarchy.)
2. 분류별 기본 감가상각 방법 (Default Depreciation Method), 내용연수 (Useful Life), 계정과목 (Account)을 설정한다.
3. 새 자산 등록 시 분류에 따라 자동으로 설정이 적용된다. (Settings are auto-applied based on category when registering new assets.)

### 감가상각 (Depreciation)

#### 감가상각 처리 (Process Depreciation)
1. **자산 (Assets) > 감가상각 분개 (Depreciation Journal)** 에서 대상 기간 (Period)을 선택한다.
2. **"일괄 처리 (Batch Process)"** 를 클릭하면 모든 자산의 감가상각이 계산된다.
3. 분개 결과를 확인하고 **"확정 (Confirm)"** 한다.
4. 회계 분개 (Journal Entry)가 자동 생성된다.

#### 감가상각 비교 (Depreciation Comparison)
1. **자산 (Assets) > 감가상각비교 (Depreciation Comparison)** 에서 정액법 (Straight Line)/정률법 (Declining Balance) 등 다양한 방법의 결과를 비교한다.

### 자산 이동 (Asset Movement)

#### 생성 (Create)
1. **자산 (Assets) > 자산 이동 (Asset Movement)** 에서 **"신규 (New)"** 를 클릭한다.
2. 이동 대상 자산 (Asset)을 선택한다.
3. 출발 (From)/도착 (To) 위치 (부서 Department 또는 물리적 위치 Physical Location)를 입력한다.
4. **"제출 (Submit)"** 하면 자산 위치가 갱신된다.

### 자산 처분 (Asset Disposal)

#### 생성 (Create)
1. **자산 (Assets) > 자산 처분 (Asset Disposal)** 에서 **"신규 (New)"** 를 클릭한다.
2. 처분 대상 자산 (Asset), 처분 방법 (Disposal Method: 매각 Sale/폐기 Scrap/기증 Donation)을 선택한다.
3. 매각의 경우 매각 금액 (Sale Amount)을 입력한다.
4. **"제출 (Submit)"** 하면 처분 손익 (Gain/Loss on Disposal)이 계산되고 회계 분개 (Journal Entry)가 생성된다.

### 자산 재평가 (Asset Revaluation)

1. **자산 (Assets) > 자산재평가 (Asset Revaluation)** 에서 재평가 대상 자산을 선택한다.
2. 재평가 금액 (Revaluation Amount)을 입력한다.
3. **"제출 (Submit)"** 하면 장부가액 (Book Value)이 변경되고 관련 분개가 생성된다.

### 유지보수 (Maintenance)

#### 유지보수 계획 (Maintenance Schedule)
1. **자산 (Assets) > 유지보수 계획 (Maintenance Schedule)** 에서 자산별 정기 점검 일정을 설정한다. (Set periodic inspection schedules per asset.)
2. 점검 주기 (Frequency), 담당자 (Assignee)를 지정한다.

#### 유지보수 요청 (Maintenance Request)
1. **자산 (Assets) > 유지보수 요청 (Maintenance Request)** 에서 수리 (Repair)/점검 (Inspection)을 요청한다.
2. 긴급도 (Urgency), 증상 (Symptoms)을 기록한다.
3. 담당자가 배정되어 처리한다. (An assignee is assigned for processing.)

#### 유지보수 로그 (Maintenance Log)
1. **자산 (Assets) > 유지보수 로그 (Maintenance Log)** 에서 수행된 유지보수 이력을 기록한다.
2. 비용 (Cost), 소요 시간 (Duration), 교체 부품 (Replaced Parts) 등을 기록한다.

### 차량 관리 (Vehicle Management)

1. **자산 (Assets) > 차량 (Vehicle)** 에서 차량을 등록한다 (차종 Model, 번호판 License Plate, 연식 Year 등).
2. **자산 (Assets) > 차량배정 (Vehicle Assignment)** 에서 직원에게 차량을 배정한다.
3. **자산 (Assets) > 차량운행일지 (Vehicle Log)** 에서 운행 기록을 관리한다.
4. **자산 (Assets) > 연료입력 (Fuel Entry)** 에서 주유 기록을 입력한다.
5. **자산 (Assets) > 차량유지보수 (Vehicle Maintenance)** 에서 정비 이력을 관리한다.

### 자산 실사 (Asset Physical Verification)

1. **자산 (Assets) > 자산 실사 (Asset Physical Verification)** 에서 정기 (Periodic)/수시 (Ad-hoc) 실사를 진행한다.
2. 자산별 실물 확인 결과 (Physical Verification Result)를 기록한다.
3. 대장 (Register)과 실물 (Physical)의 불일치를 파악하고 처리한다.

## 관련 보고서 (Related Reports)

- 자산 대장 (Asset Register)
- 감가상각 현황 (Depreciation Status)
- 자산 이동 이력 (Asset Movement History)
- 유지보수 비용 분석 (Maintenance Cost Analysis)

## FAQ

- **Q: 정액법 (Straight Line)과 정률법 (Declining Balance)의 차이는 무엇인가요?**
  A: 정액법은 매년 동일한 금액을 상각하고, 정률법은 초기에 더 많이 상각합니다. (Straight Line depreciates equally each year; Declining Balance depreciates more in earlier years.)

- **Q: 자산 처분 (Disposal) 시 장부가액 (Book Value)보다 높게 매각하면?**
  A: 차액이 처분이익 (Gain on Disposal)으로 회계 처리됩니다. (The difference is recorded as gain on disposal.)
