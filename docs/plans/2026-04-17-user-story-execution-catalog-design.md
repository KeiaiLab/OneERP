# OneERP 사용자 스토리 실행 카탈로그

## 목적

OneERP의 화면 설계, Playwright E2E, visual-log 증거를 모듈이 아니라 사용자 스토리 단위로 정렬하기 위한 정본이다.

이 문서는 다음을 고정한다.

- 사용자 스토리 ID
- 스토리 타입과 표준 화면 묶음
- 핵심 액션
- 검증 가능한 완료 기준
- Playwright 시나리오 키
- visual snapshot 키

## 적용 원칙

- 모든 신규 기능은 먼저 사용자 스토리 ID에 귀속된다.
- 모든 사용자 스토리는 하나의 주 스토리 타입을 가진다.
- 모든 사용자 스토리는 visual 6상태를 기본 계약으로 가진다.
- 완료 정의는 코드 머지가 아니라 `Playwright 시나리오 통과 + visual snapshot 확보 + a11y 통과`다.

## visual 6상태 기본 계약

| 상태 | 기본 계약 |
|---|---|
| 정상 | 사용자가 목표를 끝까지 완료할 수 있어야 한다. |
| 빈 상태 | 데이터 없음과 검색 결과 없음이 분리되어야 하고 다음 행동 CTA가 있어야 한다. |
| 오류 | 실패 이유, 재시도, 영향 범위가 표시되어야 한다. |
| 로딩 | 스켈레톤 또는 진행 표시가 있고 레이아웃 점프가 없어야 한다. |
| 권한 없음 | 접근 불가 사유와 요청 가능한 다음 행동이 있어야 한다. |
| 모바일 | 단일 컬럼 우선, sticky action, 핵심 필드 우선 노출을 보장해야 한다. |

## 스토리 타입과 표준 화면 묶음

| 타입 | 의미 | 표준 화면 묶음 |
|---|---|---|
| A | 기준정보 등록/조회 | `List + Detail/Form + Settings/Admin` |
| B | 거래 문서 작성/확정 | `List + Detail/Form` |
| C | 승인/대기열/예외 처리 | `Inbox + Detail/Form + List` |
| D | 분석/모니터링/경영 조회 | `Dashboard + Report + List` |
| E | 운영 워크스페이스형 실행 | `Workspace + List + Detail/Form` |
| F | 포털/셀프서비스 | `Workspace + Detail/Form + List` |
| G | 정책/권한/시스템 운영 설정 | `Settings/Admin + List + Detail/Form` |
| H | 문서/지식/콘텐츠 운영 | `Workspace + List + Detail/Form` |
| I | 정산/대사/결산/세무 | `Report + Detail/Form + Dashboard` |

## 자동화 키 규칙

- Playwright 시나리오 키: `story_us_<3자리 id>_<short_name>`
- visual snapshot 키: `us-<3자리 id>-<short-name>`
- visual 6상태 파일 예시:
  - `normal.png`
  - `empty.png`
  - `error.png`
  - `loading.png`
  - `forbidden.png`
  - `mobile.png`

## 사용자 스토리 카탈로그

### 1. 온보딩/기본 운영

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-001 | 관리자는 테넌트와 회사를 개설하고 기본 운영 컨텍스트를 만든다 | G | 테넌트 생성, 회사 등록, 기본 통화/회계연도 연결 | 활성 회사 컨텍스트가 저장되고 관리자 홈으로 진입한다 | `story_us_001_tenant_company_setup` | `us-001-tenant-company-setup` |
| US-002 | 관리자는 사용자, 역할, 권한을 설정해 업무별 접근을 부여한다 | G | 사용자 생성, 역할 생성, 권한 매핑, 사용자 할당 | 대상 사용자가 허용된 메뉴만 접근한다 | `story_us_002_user_role_permission_setup` | `us-002-user-role-permission-setup` |
| US-003 | 사용자는 로그인 후 대시보드에서 내 할 일과 핵심 지표를 확인한다 | D | 로그인, 대시보드 진입, 승인/지표/알림 확인 | 개인 대시보드와 주요 KPI가 정상 표시된다 | `story_us_003_login_dashboard_overview` | `us-003-login-dashboard-overview` |
| US-004 | 관리자는 채번 규칙, 워크플로우, 시스템 설정을 운영 기준에 맞게 조정한다 | G | naming series, workflow, locale/system 설정 변경 | 신규 문서와 승인 흐름에 설정이 반영된다 | `story_us_004_system_rule_configuration` | `us-004-system-rule-configuration` |

### 2. CRM/마케팅

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-005 | 마케팅 담당자는 캠페인과 자동화 규칙을 설정해 리드 유입을 운영한다 | E | 캠페인 생성, 리스트 연결, 자동화 규칙 활성화 | 캠페인 상태와 실행 대상이 워크스페이스에 보인다 | `story_us_005_campaign_automation_run` | `us-005-campaign-automation-run` |
| US-006 | 영업 담당자는 리드와 잠재고객을 등록하고 우선순위를 분류한다 | E | 리드 등록, 점수/출처 확인, 후속 액션 지정 | 우선순위 큐에서 추적 대상이 명확해진다 | `story_us_006_lead_capture_prioritization` | `us-006-lead-capture-prioritization` |
| US-007 | 영업 담당자는 기회를 단계별 파이프라인으로 관리한다 | E | 기회 생성, 단계 이동, 담당자/예상금액 갱신 | 파이프라인 보드와 상세 상태가 일치한다 | `story_us_007_opportunity_pipeline_progress` | `us-007-opportunity-pipeline-progress` |
| US-008 | 영업 관리자는 팀별 목표와 실적을 대시보드에서 본다 | D | 팀/영업사원 필터, 목표 대비 실적 조회 | 목표 대비 달성률과 위험 구간이 표시된다 | `story_us_008_sales_target_dashboard` | `us-008-sales-target-dashboard` |

### 3. 견적/가격 정책

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-009 | 영업 담당자는 고객, 고객그룹, 세그먼트를 등록해 영업 기준정보를 유지한다 | A | 고객 등록, 그룹/세그먼트 지정, 상세 조회 | 영업 문서에서 고객 기준정보를 바로 사용할 수 있다 | `story_us_009_customer_master_maintenance` | `us-009-customer-master-maintenance` |
| US-010 | 영업 운영자는 가격표, 가격규칙, 쿠폰, 로열티 정책을 설정한다 | G | 가격표 생성, 룰 적용, 쿠폰/로열티 활성화 | 견적/POS에서 정책이 자동 적용된다 | `story_us_010_pricing_policy_configuration` | `us-010-pricing-policy-configuration` |
| US-011 | 영업 담당자는 견적서를 작성해 고객에게 발송하고 응답을 추적한다 | B | 견적 작성, PDF/메일 발송, 응답 상태 확인 | 발송 이력과 수락/거절 상태가 기록된다 | `story_us_011_quotation_create_send_track` | `us-011-quotation-create-send-track` |
| US-012 | 영업 담당자는 수락된 견적을 판매주문으로 전환한다 | B | 견적 선택, 주문 전환, 납기/조건 확정 | 판매주문 초안이 생성되고 출고 준비가 가능하다 | `story_us_012_quote_to_sales_order` | `us-012-quote-to-sales-order` |

### 4. 주문-출고-청구-수금

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-013 | 물류 담당자는 판매주문 기준으로 피킹, 패킹, 출고 준비를 수행한다 | C | 주문 큐 조회, 피킹리스트 확인, 패킹 상태 갱신 | 출고 가능한 주문만 큐에 남는다 | `story_us_013_pick_pack_execution` | `us-013-pick-pack-execution` |
| US-014 | 출하 담당자는 납품서를 생성하고 실제 출고를 확정한다 | B | 납품서 생성, 창고 확인, 출고 제출 | 재고 차감과 납품 상태가 반영된다 | `story_us_014_delivery_note_submit` | `us-014-delivery-note-submit` |
| US-015 | 회계 담당자는 주문 또는 납품 기준으로 매출 송장을 발행한다 | B | 송장 생성, 세금/만기 확인, 제출 | AR와 회계분개가 자동 생성된다 | `story_us_015_sales_invoice_issue` | `us-015-sales-invoice-issue` |
| US-016 | 수금 또는 매장 담당자는 수금, POS 거래, 마감 전표를 처리한다 | B | 결제 등록, POS 영수증 발행, 마감 처리 | 미수금이 소거되고 마감 전표가 생성된다 | `story_us_016_payment_pos_closing` | `us-016-payment-pos-closing` |

### 5. 구매요청-발주-입고

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-017 | 현업 요청자는 구매요청을 등록하고 승인 상태를 확인한다 | C | 구매요청 작성, 결재 요청, 상태 추적 | 요청 상태와 다음 처리자가 보인다 | `story_us_017_purchase_request_submit_track` | `us-017-purchase-request-submit-track` |
| US-018 | 구매 담당자는 RFQ를 발행하고 공급업체 견적을 비교한다 | B | RFQ 생성, 공급업체 발송, 견적 비교 | 선정 공급업체가 확정된다 | `story_us_018_rfq_issue_compare` | `us-018-rfq-issue-compare` |
| US-019 | 구매 담당자는 승인 기준에 따라 발주를 확정한다 | B | 발주 생성, 승인 매트릭스 확인, 제출 | 발주 문서가 확정되고 입고 대기가 생성된다 | `story_us_019_purchase_order_submit` | `us-019-purchase-order-submit` |
| US-020 | 입고 담당자는 발주 기준으로 구매입고를 처리한다 | B | 입고 생성, 수량/창고 입력, 제출 | 재고원장과 재고빈 잔액이 갱신된다 | `story_us_020_purchase_receipt_submit` | `us-020-purchase-receipt-submit` |

### 6. 구매정산/공급업체 운영

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-021 | 매입 담당자는 구매입고 기준으로 매입 송장을 생성한다 | B | 송장 생성, 세금 확인, 제출 | AP와 회계분개가 자동 생성된다 | `story_us_021_purchase_invoice_issue` | `us-021-purchase-invoice-issue` |
| US-022 | 자금 담당자는 지급오더와 지급전표를 처리한다 | I | 지급 대상 조회, 지급 실행, AP 소거 확인 | 지급 완료와 채무 소거가 확인된다 | `story_us_022_payment_order_settlement` | `us-022-payment-order-settlement` |
| US-023 | 구매 관리자는 공급업체 그룹, 평가표, 실적을 관리한다 | A | 공급업체 등록, 그룹/평가 설정, 점수 조회 | 우선 협력업체와 저성과 업체가 구분된다 | `story_us_023_supplier_master_scorecard` | `us-023-supplier-master-scorecard` |
| US-024 | 구매 관리자는 반품, landed cost, 운송비를 반영해 실제 매입원가를 정산한다 | I | 반품 처리, landed cost 반영, 부대비용 배부 | 품목 원가와 매입 정산 결과가 일치한다 | `story_us_024_purchase_cost_settlement` | `us-024-purchase-cost-settlement` |

### 7. 재고 기준정보/창고 운영

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-025 | 창고 담당자는 품목, 품목군, 속성, UOM, 변형을 등록한다 | A | 품목 등록, 속성 연결, 변형 생성 | 판매/구매/생산에서 품목을 참조할 수 있다 | `story_us_025_item_master_maintenance` | `us-025-item-master-maintenance` |
| US-026 | 창고 관리자는 창고, bin, putaway rule, reorder level을 설정한다 | G | 창고 생성, bin 정책, 보충 기준 설정 | 입출고와 replenishment 기준이 활성화된다 | `story_us_026_warehouse_rule_configuration` | `us-026-warehouse-rule-configuration` |
| US-027 | 창고 담당자는 재고이동, 재고조정, 실사를 수행한다 | B | 이동/조정 문서 생성, 실사 수량 입력, 제출 | 차이 수량이 원장과 잔액에 반영된다 | `story_us_027_stock_adjustment_cycle_count` | `us-027-stock-adjustment-cycle-count` |
| US-028 | 창고 관리자는 재고잔액, 배치/시리얼, 안전재고, ATP를 조회한다 | D | 재고 대시보드 조회, ATP/안전재고 필터, 예외 확인 | 품절 위험과 가용 재고가 즉시 파악된다 | `story_us_028_inventory_visibility_dashboard` | `us-028-inventory-visibility-dashboard` |

### 8. 물류/반품/렌탈

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-029 | 물류 담당자는 웨이브피킹과 배송 계획을 실행한다 | E | 웨이브 생성, 피킹 큐 확인, 배송 배차 | 출고 우선순위와 배차 상태가 정리된다 | `story_us_029_wave_picking_shipping_plan` | `us-029-wave-picking-shipping-plan` |
| US-030 | 물류 담당자는 선적, 배송추적, 드롭쉽 흐름을 관리한다 | E | 선적 문서 생성, 추적 업데이트, 드롭쉽 주문 확인 | 배송 상태와 고객 안내 정보가 최신화된다 | `story_us_030_shipment_tracking_dropship` | `us-030-shipment-tracking-dropship` |
| US-031 | CS 담당자는 RMA를 접수하고 반품검사 후 환불 또는 재입고를 결정한다 | C | RMA 접수, 검사 결과 입력, 처분 결정 | 환불/재입고 처리 결과가 문서에 남는다 | `story_us_031_rma_inspection_resolution` | `us-031-rma-inspection-resolution` |
| US-032 | 운영 담당자는 렌탈 품목의 대여, 회수, 연체, 손상 상태를 관리한다 | E | 렌탈 주문 생성, 회수 기록, 연체/손상 처리 | 렌탈 자산 상태와 청구 근거가 유지된다 | `story_us_032_rental_order_return_control` | `us-032-rental-order-return-control` |

### 9. 회계 기본 운영

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-033 | 회계 담당자는 계정과목, 회계기간, 원가센터, profit center를 관리한다 | G | 마스터 등록, 기간 개설, 코스트 구조 정비 | 회계 문서가 올바른 기준값을 참조한다 | `story_us_033_accounting_master_configuration` | `us-033-accounting-master-configuration` |
| US-034 | 회계 담당자는 일반분개, 반복분개, 자동분개 결과를 검토하고 제출한다 | B | 분개 작성/생성, 승인 요청 또는 제출, 원장 반영 확인 | 차대변 일치와 원장 반영이 보장된다 | `story_us_034_journal_entry_processing` | `us-034-journal-entry-processing` |
| US-035 | 회계 담당자는 총계정원장과 주요 회계 리포트를 조회한다 | D | 계정/기간 필터, 원장 드릴다운, 비율 리포트 조회 | 필요한 회계 근거를 화면에서 추적할 수 있다 | `story_us_035_general_ledger_reporting` | `us-035-general-ledger-reporting` |
| US-036 | 회계 관리자는 예산, 예산버전, 예산이전 요청을 관리한다 | I | 예산 편성, 버전 비교, 이전 승인/반영 | 집행률과 잔여 예산이 정확히 보인다 | `story_us_036_budget_version_transfer` | `us-036-budget-version-transfer` |

### 10. 자금/세무/결산

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-037 | 자금 담당자는 은행거래를 가져와 은행대사를 완료한다 | I | 피드/명세 업로드, 자동 매칭, 미매칭 조정 | 장부 잔액과 은행 잔액 차이가 해소된다 | `story_us_037_bank_reconciliation_close` | `us-037-bank-reconciliation-close` |
| US-038 | 자금 담당자는 현금흐름 예측과 자금이체 우선순위를 관리한다 | D | 현금흐름 조회, 이체 후보 검토, 자금 계획 조정 | 부족/여유 자금 경고가 식별된다 | `story_us_038_cashflow_transfer_prioritization` | `us-038-cashflow-transfer-prioritization` |
| US-039 | 세무 담당자는 부가세, 원천세, 전자세금계산서를 처리한다 | I | 세금 자료 집계, 신고서 검토, 전자세금계산서 발행 | 신고 대상과 발행 상태가 일치한다 | `story_us_039_tax_filing_etax_processing` | `us-039-tax-filing-etax-processing` |
| US-040 | 회계 관리자는 기간마감, 외화평가, 연말결산을 수행한다 | I | 마감 체크리스트, 평가 분개, 결산 확정 | 마감 상태와 후속 보고 준비가 완료된다 | `story_us_040_period_close_year_end` | `us-040-period-close-year-end` |

### 11. 인사 핵심 운영

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-041 | HR 담당자는 직원, 부서, 직급, 직원그룹을 등록하고 조직을 관리한다 | A | 직원/조직 등록, 소속 변경, 상세 조회 | 조직도와 직원 카드가 최신 상태가 된다 | `story_us_041_employee_org_master` | `us-041-employee-org-master` |
| US-042 | HR 담당자는 온보딩과 오프보딩 체크리스트를 운영한다 | E | 온보딩 생성, 체크리스트 완료, 오프보딩 전환 | 입사/퇴사 절차 상태가 추적된다 | `story_us_042_onboarding_offboarding_run` | `us-042-onboarding-offboarding-run` |
| US-043 | 팀장은 근태, 교대, 초과근무, 대체휴가 요청을 승인한다 | C | 대기 요청 확인, 승인/반려, 사유 기록 | 팀원 요청 상태가 즉시 갱신된다 | `story_us_043_attendance_shift_overtime_approval` | `us-043-attendance-shift-overtime-approval` |
| US-044 | 구성원은 휴가신청, 근태정정, 교대 요청을 제출하고 결과를 확인한다 | F | 신청서 작성, 제출, 내 요청 상태 확인 | 승인 결과와 잔여 일수가 정확히 보인다 | `story_us_044_selfservice_leave_attendance_request` | `us-044-selfservice-leave-attendance-request` |

### 12. 채용/평가/인재개발

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-045 | 채용 담당자는 채용공고를 게시하고 지원자와 면접 라운드를 관리한다 | E | 공고 생성, 지원자 등록, 면접 피드백 수집 | 채용 단계와 후보 상태가 보드에 정리된다 | `story_us_045_recruiting_pipeline_run` | `us-045-recruiting-pipeline-run` |
| US-046 | HR 담당자는 평가주기와 평가템플릿을 운영하고 피드백을 수집한다 | E | 주기 생성, 템플릿 배포, 평가 회수 | 평가 진행률과 미완료 대상이 드러난다 | `story_us_046_appraisal_cycle_feedback` | `us-046-appraisal-cycle-feedback` |
| US-047 | 인사 관리자는 역량체계, 스킬맵, 교육과정을 관리한다 | E | 역량 정의, 스킬맵 갱신, 수강 등록/완료 | 인재개발 현황과 부족 역량이 보인다 | `story_us_047_competency_learning_management` | `us-047-competency-learning-management` |
| US-048 | 경영진은 승계계획과 참여도 결과를 검토한다 | D | 승계대상 조회, 참여도 결과 필터, 리스크 확인 | 핵심 인재 리스크와 후속 액션이 표시된다 | `story_us_048_succession_engagement_dashboard` | `us-048-succession-engagement-dashboard` |

### 13. 급여/복리후생/퇴직

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-049 | 급여 담당자는 급여구조, 급여항목, 급여개정 기준을 설정한다 | G | 급여구조 생성, 항목 연결, 개정안 저장 | 급여처리 전제 마스터가 확정된다 | `story_us_049_payroll_structure_configuration` | `us-049-payroll-structure-configuration` |
| US-050 | 급여 담당자는 급여처리를 실행해 급여명세와 회계분개를 생성한다 | I | 급여처리 실행, 결과 검토, 급여명세 발행 | 급여명세와 분개가 함께 생성된다 | `story_us_050_payroll_run_posting` | `us-050-payroll-run-posting` |
| US-051 | 급여 담당자는 4대보험, 원천세, 한국형 급여 조정을 처리한다 | I | 보험/세금 계산, 조정 입력, 신고 자료 검토 | 법정 공제와 신고 자료가 정합하다 | `story_us_051_payroll_tax_social_insurance` | `us-051-payroll-tax-social-insurance` |
| US-052 | HR 담당자는 직원대여금, 복리후생, 퇴직 정산을 관리한다 | B | 대여금/복지 청구 처리, 퇴직급여 계산, 확정 | 직원별 정산 상태와 금액이 저장된다 | `story_us_052_employee_benefit_retirement_settlement` | `us-052-employee-benefit-retirement-settlement` |

### 14. 경비/출장/전자결재

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-053 | 임직원은 경비청구를 작성하고 증빙을 첨부한다 | F | 경비청구 작성, 증빙 첨부, 제출 | 경비청구와 첨부 증빙이 저장된다 | `story_us_053_expense_claim_submit` | `us-053-expense-claim-submit` |
| US-054 | 재무 담당자는 법인카드 거래를 불러와 경비청구와 매칭한다 | I | 카드 거래 동기화, 청구 매칭, 예외 처리 | 미매칭 거래와 처리 결과가 구분된다 | `story_us_054_corporate_card_matching` | `us-054-corporate-card-matching` |
| US-055 | 임직원은 출장요청을 제출하고 정산까지 완료한다 | F | 출장 요청, 승인 추적, 비용 정산 | 출장 라이프사이클 상태가 끝까지 연결된다 | `story_us_055_travel_request_settlement` | `us-055-travel-request-settlement` |
| US-056 | 결재자는 내 결재함에서 승인, 반려, 위임, 전결을 처리한다 | C | 내 대기함 조회, 액션 선택, 코멘트 기록 | 결재 결과와 감사 이력이 남는다 | `story_us_056_approval_inbox_actions` | `us-056-approval-inbox-actions` |

### 15. 제조/생산 계획

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-057 | 생산기획자는 BOM, BOM revision, routing, ECO를 관리한다 | G | BOM 생성, 리비전 발행, routing 연결, ECO 승인 | 최신 제조 기준서가 생산에 반영된다 | `story_us_057_bom_routing_eco_configuration` | `us-057-bom-routing-eco-configuration` |
| US-058 | 생산기획자는 수요예측, 공급계획, MRP, capacity plan을 수립한다 | E | 예측 조회, MRP 실행, capacity 조정 | 부족 자재와 설비 병목이 드러난다 | `story_us_058_mrp_capacity_planning` | `us-058-mrp-capacity-planning` |
| US-059 | 생산 담당자는 작업지시와 job card 기준으로 생산실적을 기록한다 | E | 작업지시 확인, job card 입력, 실적 제출 | 생산수량과 공정 진행률이 반영된다 | `story_us_059_work_order_jobcard_execution` | `us-059-work-order-jobcard-execution` |
| US-060 | 생산 관리자는 생산원가, 공정손실, OEE를 분석한다 | D | 원가/손실/OEE 대시보드 조회, 기간 필터 | 비효율 공정과 수율 이슈가 식별된다 | `story_us_060_production_cost_oee_dashboard` | `us-060-production-cost-oee-dashboard` |

### 16. 품질/안전/컴플라이언스

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-061 | 품질 담당자는 품질절차와 검사템플릿을 정의하고 검사를 수행한다 | G | 절차 등록, 템플릿 설정, 검사 문서 실행 | 검사 기준과 결과가 연결된다 | `story_us_061_quality_template_inspection_setup` | `us-061-quality-template-inspection-setup` |
| US-062 | 품질 담당자는 부적합, RMA 검사, CAPA를 등록하고 종결한다 | C | 부적합 등록, 원인분석, CAPA 완료 | 시정/예방조치 이력이 닫힌다 | `story_us_062_nonconformance_capa_closure` | `us-062-nonconformance-capa-closure` |
| US-063 | EHS 담당자는 안전사고, 위험성평가, 안전교육 이수를 관리한다 | E | 사고 등록, 위험평가, 교육 이수 확인 | 안전 조치 현황과 미이수 대상이 보인다 | `story_us_063_safety_incident_training_run` | `us-063-safety-incident-training-run` |
| US-064 | 컴플라이언스 담당자는 내부통제와 규제 보고를 운영한다 | D | 체크리스트 조회, 통제 상태 확인, 보고서 생성 | 미준수 항목과 보고 상태가 파악된다 | `story_us_064_compliance_control_reporting` | `us-064-compliance-control-reporting` |

### 17. 자산/설비/차량

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-065 | 자산 담당자는 자산, 보험, 유지보수계획을 등록한다 | A | 자산 등록, 보험 연결, 유지보수 플랜 수립 | 자산 카드와 유지 계획이 생성된다 | `story_us_065_asset_master_plan_setup` | `us-065-asset-master-plan-setup` |
| US-066 | 자산 담당자는 감가상각, 재평가, 손상, 처분을 처리한다 | I | 자산 가치 이벤트 실행, 분개 확인, 상태 변경 | 자산 가치와 회계 반영이 일치한다 | `story_us_066_asset_valuation_disposal` | `us-066-asset-valuation-disposal` |
| US-067 | 운영 담당자는 자산이동, 실사, 수리이력, spare part 사용을 관리한다 | E | 이동 등록, 실사 점검, 수리 기록 | 자산 위치와 상태 이력이 최신화된다 | `story_us_067_asset_movement_audit_repair` | `us-067-asset-movement-audit-repair` |
| US-068 | 총무 담당자는 차량배정, 운행일지, 정비, 유류비를 관리한다 | E | 차량 배정, 운행 기록, 정비/유류 입력 | 차량 운영 이력과 비용이 추적된다 | `story_us_068_vehicle_operation_management` | `us-068-vehicle-operation-management` |

### 18. 프로젝트/계약

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-069 | PM은 프로젝트, WBS, 마일스톤, 태스크, 리스크를 관리한다 | E | 프로젝트 생성, WBS/마일스톤 설정, 리스크 기록 | 프로젝트 계획과 상태 보드가 유지된다 | `story_us_069_project_wbs_risk_run` | `us-069-project-wbs-risk-run` |
| US-070 | 구성원은 타임시트를 기록하고 자원배정 상태를 확인한다 | F | 타임시트 입력, 할당 확인, 제출 | 시간 기록과 잔여 할당량이 보인다 | `story_us_070_timesheet_resource_selfservice` | `us-070-timesheet-resource-selfservice` |
| US-071 | PM과 재무는 프로젝트 청구와 수익인식을 처리한다 | I | 프로젝트 청구 생성, 수익인식 실행, 상태 확인 | 프로젝트별 청구/인식 결과가 반영된다 | `story_us_071_project_billing_revenue_recognition` | `us-071-project-billing-revenue-recognition` |
| US-072 | 영업/운영 담당자는 계약과 계약갱신 일정을 관리한다 | B | 계약 생성, 조건 수정, 갱신 일정 추적 | 계약 상태와 갱신 예정이 보인다 | `story_us_072_contract_renewal_management` | `us-072-contract-renewal-management` |

### 19. 서비스/문서/지식/포털

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-073 | 지원 담당자는 이슈, SLA, 서비스오더, 현장방문, 보증을 처리한다 | C | 이슈 접수, SLA 확인, 서비스오더 실행, 방문 종료 | 서비스 상태와 보증 처리 이력이 남는다 | `story_us_073_service_sla_warranty_run` | `us-073-service-sla-warranty-run` |
| US-074 | 문서 담당자는 문서분류, 버전, 보존정책, 전자서명을 관리한다 | H | 문서 등록, 버전 발행, 보존/서명 상태 관리 | 문서 정본과 배포 상태가 통제된다 | `story_us_074_document_lifecycle_governance` | `us-074-document-lifecycle-governance` |
| US-075 | 사용자는 지식베이스와 FAQ에서 해결 방법을 검색하고 열람한다 | H | 검색, 카테고리 탐색, 문서 열람 | 필요한 지식 문서를 빠르게 찾는다 | `story_us_075_knowledge_base_discovery` | `us-075-knowledge-base-discovery` |
| US-076 | 고객과 공급업체는 포털에서 주문, 송장, 배송, 문의 상태를 조회한다 | F | 포털 로그인, 문서 조회, 상태 확인 | 외부 사용자가 필요한 정보만 본다 | `story_us_076_customer_supplier_portal_view` | `us-076-customer-supplier-portal-view` |

### 20. 운영/통합/데이터 거버넌스

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-077 | 관리자는 KPI, 위젯, 커스텀 리포트를 구성한다 | D | KPI 정의, 위젯 배치, 리포트 실행 | 조직별 운영 대시보드가 완성된다 | `story_us_077_kpi_widget_custom_report` | `us-077-kpi-widget-custom-report` |
| US-078 | 운영 담당자는 외부 커넥터, 웹훅, 통합로그를 운영한다 | G | 커넥터 설정, 웹훅 점검, 재처리 실행 | 실패 통합과 정상 통합이 구분된다 | `story_us_078_integration_connector_webhook_ops` | `us-078-integration-connector-webhook-ops` |
| US-079 | 데이터 관리자는 감사로그, 개인정보 기록, 데이터소스를 관리한다 | G | 감사로그 조회, 개인정보 레지스터 점검, 데이터소스 설정 | 데이터 거버넌스 증빙이 유지된다 | `story_us_079_data_governance_audit_privacy` | `us-079-data-governance-audit-privacy` |
| US-080 | Super Admin은 플랜, 모듈 활성화, 멀티테넌트 격리를 운영한다 | G | 플랜 변경, 모듈 토글, 테넌트 상태 점검 | 플랜별 접근과 테넌트 경계가 유지된다 | `story_us_080_superadmin_plan_tenant_ops` | `us-080-superadmin-plan-tenant-ops` |

### 21. 무역/국제거래

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-081 | 물류 담당자는 수출신고, 선적, 통관, 운송추적을 관리한다 | E | 수출 문서 작성, 선적 연결, 통관/추적 갱신 | 수출 건별 진행 상태가 명확하다 | `story_us_081_export_shipping_clearance` | `us-081-export-shipping-clearance` |
| US-082 | 구매 담당자는 수입신고와 관세, 부대비용을 반영한다 | E | 수입 문서 작성, 관세 입력, 부대비용 반영 | 수입 원가와 통관 상태가 일치한다 | `story_us_082_import_duty_costing` | `us-082-import-duty-costing` |
| US-083 | 재무 담당자는 신용장과 무역금융 정산을 처리한다 | I | LC 생성, 조건 확인, 정산 처리 | 금융 상태와 지급 일정이 관리된다 | `story_us_083_letter_of_credit_settlement` | `us-083-letter-of-credit-settlement` |
| US-084 | 물류 관리자는 관세코드와 국제물류 기준정보를 유지한다 | G | 관세 코드, 운송사, 통관 기준값 관리 | 무역 문서 작성 기준이 통일된다 | `story_us_084_trade_master_configuration` | `us-084-trade-master-configuration` |

### 22. 구독/전자상거래

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-085 | 영업 운영자는 구독플랜과 청구 주기를 설계한다 | G | 플랜 생성, 주기/요율 설정, 활성화 | 구독 판매 기준값이 확정된다 | `story_us_085_subscription_plan_configuration` | `us-085-subscription-plan-configuration` |
| US-086 | 영업 운영자는 구독 계약의 시작, 갱신, 해지를 관리한다 | B | 구독 생성, 갱신/해지 처리, 상태 추적 | 계약 상태와 다음 청구 일정이 보인다 | `story_us_086_subscription_lifecycle_management` | `us-086-subscription-lifecycle-management` |
| US-087 | 운영 담당자는 e-commerce와 marketplace 주문을 ERP 주문으로 연동한다 | E | 채널 주문 수집, ERP 주문 생성, 예외 확인 | 외부 주문이 내부 주문으로 전환된다 | `story_us_087_channel_order_integration` | `us-087-channel-order-integration` |
| US-088 | CS/재무 담당자는 recurring invoice와 subscription invoice 예외를 처리한다 | I | 청구 예외 조회, 재발행/정정, 상태 확인 | 누락/실패 청구가 정리된다 | `story_us_088_recurring_invoice_exception` | `us-088-recurring-invoice-exception` |

### 23. 그룹회계/인터컴퍼니

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-089 | 재무 담당자는 관계회사 간 거래를 등록하고 정합성을 맞춘다 | B | 인터컴퍼니 거래 생성, 상대사 매칭, 상태 확인 | 양사 문서 참조와 금액이 일치한다 | `story_us_089_intercompany_transaction_entry` | `us-089-intercompany-transaction-entry` |
| US-090 | 재무 담당자는 intercompany billing과 elimination entry를 처리한다 | I | 청구 생성, 제거분개 작성, 결과 검토 | 연결조정 영향이 반영된다 | `story_us_090_intercompany_billing_elimination` | `us-090-intercompany-billing-elimination` |
| US-091 | 그룹회계 담당자는 consolidation group과 K-IFRS 매핑을 관리한다 | G | 연결그룹 설정, 계정 매핑, 기준값 점검 | 연결재무 생성 전 기준 매핑이 확정된다 | `story_us_091_consolidation_kifrs_mapping` | `us-091-consolidation-kifrs-mapping` |
| US-092 | CFO실은 연결 재무제표와 세그먼트 리포트를 검토한다 | D | 연결 리포트 조회, 세그먼트 필터, 이상값 확인 | 그룹 성과와 조정 결과를 확인한다 | `story_us_092_consolidated_segment_reporting` | `us-092-consolidated-segment-reporting` |

### 24. ESG/IoT/고급 운영

| ID | 스토리 | 타입 | 핵심 액션 | 완료 기준 | Playwright 키 | Visual 키 |
|---|---|---|---|---|---|---|
| US-093 | ESG 담당자는 ESG 지표, 탄소배출, 공시 데이터를 수집하고 보고한다 | D | 지표 수집, 배출량 확인, 공시 보고서 조회 | ESG 리포트와 원천 지표가 연결된다 | `story_us_093_esg_carbon_disclosure_dashboard` | `us-093-esg-carbon-disclosure-dashboard` |
| US-094 | 설비 담당자는 IoT 경보와 다운타임을 모니터링하고 대응한다 | D | 디바이스 상태 조회, 경보 확인, 다운타임 원인 분석 | 실시간 운영 이상과 영향 범위가 보인다 | `story_us_094_iot_alert_downtime_monitoring` | `us-094-iot-alert-downtime-monitoring` |
| US-095 | 운영 담당자는 유해물질, 폐기물, 보존 대상 운영 이력을 관리한다 | E | 대상 등록, 처리 이력 기록, 상태 추적 | 규제 대상 운영 이력이 누락 없이 남는다 | `story_us_095_hazard_waste_operational_tracking` | `us-095-hazard-waste-operational-tracking` |
| US-096 | 리스크 담당자는 리스크 평가, 규제 sandbox, 컴플라이언스 보고를 운영한다 | D | 리스크 목록 조회, sandbox 상태 확인, 보고서 검토 | 고위험 이슈와 규제 대응 상태가 파악된다 | `story_us_096_risk_sandbox_compliance_dashboard` | `us-096-risk-sandbox-compliance-dashboard` |

## 우선순위 제안

Wave 1에서 먼저 표준화할 후보는 아래 12개다.

- 테넌트/회사 개설
- 사용자/권한 설정
- 로그인/대시보드
- 견적 작성·발송
- 견적→판매주문 전환
- 납품 확정
- 매출 송장 발행
- 수금/POS 마감
- 구매요청 등록·상태 확인
- 발주 확정
- 구매입고 처리
- 승인함 처리

## 다음 문서화 단계

다음 단계에서는 위 카탈로그를 기준으로 각 스토리별로 아래 산출물을 분리한다.

1. 스토리별 사용자 시나리오 상세
2. 스토리별 화면 IA
3. Playwright 명세서
4. visual-log 캡처 체크리스트
5. a11y 체크리스트
