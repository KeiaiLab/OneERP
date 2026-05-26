---
status: Accepted
date: 2026-05-07
decision: 47개 상용 모듈의 책임 경계를 단일 카탈로그 ADR로 확정한다.
consequences: 모듈별 책임 변경은 이 ADR의 해당 섹션 또는 개별 *-bounds ADR 갱신 없이는 확정되지 않는다.
---

# ADR-0021: OneERP 모듈 경계 카탈로그

## 맥락

OneERP 상용 출시 게이트는 47개 모듈 모두에 대해 경계 결정 근거를 요구한다.
기존 `gateway`, `accounting`, `hr`처럼 개별 bounds ADR이 있는 모듈은 해당
ADR을 우선한다. 아직 개별 ADR이 없는 모듈은 본 카탈로그를 G1-1 정본
결정으로 사용한다.

본 ADR은 ADR-0014의 6-plane 런타임 모델과 ADR-0011의 코드 클러스터
구조를 바꾸지 않는다. 모듈은 제품 책임 경계이며, 배포 단위와 코드
디렉토리는 기존 SoT를 따른다.

## 결정

- 모듈별 API, 데이터 소유권, 운영 런북, 보안 증거는 아래 책임 경계를 기준으로 작성한다.
- 공통 마스터 데이터는 중복 소유하지 않고, 원천 모듈 또는 platform/gateway 계약을 통해 참조한다.
- 경계가 겹치는 기능은 먼저 이벤트/API 계약으로 연결하고, 데이터 소유권 이전은 별도 ADR로 확정한다.
- 본 ADR은 누락된 개별 ADR의 대체 정본이며, 더 구체적인 개별 bounds ADR이 있으면 개별 ADR이 우선한다.

## consequences — 공통 영향

- commercial readiness G1-1은 이 파일의 모듈별 섹션을 모듈 경계 결정 증거로 인정한다.
- 신규 기능 구현 시 module/service mapping과 runbook, OpenAPI, 테스트 증거가 같은 모듈명으로 정렬되어야 한다.
- 모듈명을 바꾸거나 병합하려면 release catalog, docs, deploy chart, evidence 경로를 함께 갱신해야 한다.

## gateway — API 게이트웨이 경계

결정: gateway는 인증 진입점, tenant routing, 공통 API 프록시, rate-limit, cross-module facade만 소유한다.
영향: 업무 데이터 원장은 gateway에 두지 않고 각 도메인 API로 위임한다.

## accounting — 회계 경계

결정: accounting은 전표, 예산, 회계기간, 세무 마감과 재무 원장 정합성을 소유한다.
영향: 판매/구매/급여 이벤트는 accounting에 회계 이벤트로 전달되며 원거래는 원천 모듈에 남는다.

## hr — 인사 경계

결정: hr은 직원, 부서, 직책, 근태 기준, 인사 프로필의 원천 데이터를 소유한다.
영향: payroll, learning, workreport는 HR 식별자를 참조하지만 인사 원장을 복제하지 않는다.

## directory — 조직 디렉터리 경계

결정: directory는 회사, 사업장, 공통 연락처, 조직 검색 인덱스의 참조 경계를 소유한다.
영향: CRM 고객과 HR 직원은 directory 식별자를 참조하되 업무별 상태는 각 모듈에 둔다.

## selling — 판매 경계

결정: selling은 견적, 판매주문, 출하요청, 매출청구, 반품 승인까지 order-to-cash 전단을 소유한다.
영향: 재고 출고와 회계 전표는 stock/accounting 이벤트로 연결하고 판매 원장은 selling에 남긴다.

## buying — 구매 경계

결정: buying은 구매요청, 구매주문, 입고요청, 매입청구, 수입 신고 연결까지 procure-to-pay 전단을 소유한다.
영향: 입고 수량과 원가 반영은 stock/accounting에 위임하고 구매 상태는 buying이 관리한다.

## stock — 재고 경계

결정: stock은 품목 재고, lot/serial, bin, 재고조정, 출고/입고 ledger를 소유한다.
영향: 판매/구매/제조는 stock ledger를 직접 수정하지 않고 stock API 또는 이벤트로 요청한다.

## payroll — 급여 경계

결정: payroll은 급여 계산, 공제, 지급 명세, 급여 회계 이벤트를 소유한다.
영향: 직원 원천 정보는 hr에서 참조하고 회계 전표는 accounting으로 발행한다.

## portal — 포털 경계

결정: portal은 임직원/거래처 셀프서비스 화면, 알림 진입점, 업무 요청 라우팅을 소유한다.
영향: 포털은 업무 원장을 소유하지 않고 각 모듈의 상태를 조회/요청한다.

## projects — 프로젝트 경계

결정: projects는 프로젝트, 태스크, 마일스톤, 프로젝트 원가/진행률 상태를 소유한다.
영향: 자원 배정은 HR/자산을 참조하고 회계 반영은 accounting 이벤트로 분리한다.

## expenses — 경비 경계

결정: expenses는 개인/법인카드 경비, 영수증, 승인, 정산 요청을 소유한다.
영향: 지급 및 전표는 payroll/accounting과 연계하되 증빙 수명주기는 expenses가 관리한다.

## crm — 고객관계 경계

결정: crm은 lead, opportunity, campaign response, 고객 접점 이력을 소유한다.
영향: 확정 거래는 selling으로 전환하며 회계/재고 원장은 CRM에 두지 않는다.

## advanced-planning — 고급계획 경계

결정: advanced-planning은 수요계획, 공급계획, 생산/구매 제안의 계획 결과를 소유한다.
영향: 실행 주문은 manufacturing/buying/selling으로 발행하고 계획 시뮬레이션은 독립 보존한다.

## analytics — 분석 경계

결정: analytics는 지표 모델, 리포트 데이터셋, 집계 뷰, 분석 권한을 소유한다.
영향: 분석 모듈은 원천 거래를 수정하지 않고 읽기 모델과 집계 산출물만 관리한다.

## assets — 자산 경계

결정: assets는 고정자산, 이동, 감가상각, 수리 이력, 처분 요청을 소유한다.
영향: 회계 반영은 accounting으로 이벤트를 발행하고 물리 위치는 directory/projects를 참조한다.

## board — 게시판 경계

결정: board는 공지, 사내 게시글, 댓글, 공개 범위, 게시 승인 상태를 소유한다.
영향: 문서 보관은 documents에 위임하고 게시 노출 정책은 board가 관리한다.

## calendar — 캘린더 경계

결정: calendar는 일정, 참석자, 자원 예약, 업무 캘린더 구독 상태를 소유한다.
영향: 프로젝트/HR 이벤트는 calendar에 표시되지만 원천 상태는 해당 모듈에서 유지한다.

## clm — 계약수명주기 경계

결정: clm은 계약 초안, 검토, 갱신, 의무사항, 계약 리스크 상태를 소유한다.
영향: 계약 파일은 documents와 연결하고 매출/구매 실행은 selling/buying으로 분리한다.

## compliance — 컴플라이언스 경계

결정: compliance는 정책, 통제, 감사 체크리스트, 위반/개선 조치 추적을 소유한다.
영향: 각 모듈의 증거는 compliance에 참조되지만 업무 원장은 원천 모듈에 남는다.

## consolidation — 연결회계 경계

결정: consolidation은 연결 조정, 내부거래 제거, 세그먼트 보고, K-IFRS 매핑을 소유한다.
영향: 개별 법인 원장은 accounting에 두고 consolidation은 연결 산출물을 관리한다.

## documents — 문서 경계

결정: documents는 파일 메타데이터, 버전, 보관 정책, 문서 권한과 링크를 소유한다.
영향: 업무 문서의 비즈니스 상태는 원천 모듈에 있고 파일 수명주기는 documents가 관리한다.

## ecommerce — 이커머스 경계

결정: ecommerce는 온라인 주문 수집, 채널 매핑, 상품 노출, 외부몰 동기화 상태를 소유한다.
영향: 확정 주문은 selling으로 전달하고 재고 가용성은 stock에서 조회한다.

## ehs — 환경보건안전 경계

결정: ehs는 안전점검, 사고, 위험물, 교육 이수, 개선 조치의 운영 상태를 소유한다.
영향: 자산/인사 참조는 assets/hr에서 가져오며 규제 보고는 compliance와 연결한다.

## esg — ESG 경계

결정: esg는 탄소, 사회, 지배구조 지표와 공시 데이터 수집/승인 상태를 소유한다.
영향: 회계/운영 데이터는 읽기 모델로 수집하고 원천 거래는 수정하지 않는다.

## fleet — 차량 경계

결정: fleet은 차량, 운행, 정비, 유류비, 배차 상태를 소유한다.
영향: 고정자산 반영은 assets/accounting으로 연결하고 운행 업무 상태는 fleet이 관리한다.

## gtm — 시장진입 경계

결정: gtm은 출시 캠페인, 가격 패키지, 세일즈 playbook, go-to-market 실행 상태를 소유한다.
영향: 리드와 매출 실행은 crm/selling으로 연결하고 GTM 계획 산출물은 gtm에 남긴다.

## integration-hub — 통합허브 경계

결정: integration-hub는 외부 커넥터, 매핑, 재처리 큐, 통합 실패 관측을 소유한다.
영향: 외부 데이터가 업무 원장으로 승격될 때는 대상 모듈 API 계약을 통과해야 한다.

## iot — IoT 경계

결정: iot는 장치, 텔레메트리 수집, 상태 이벤트, 장치 알림을 소유한다.
영향: 생산/자산 업무 상태는 manufacturing/assets로 이벤트를 전달하고 raw telemetry는 iot에 둔다.

## knowledge — 지식관리 경계

결정: knowledge는 지식 문서, FAQ, 검색 태그, 지식 승인 흐름을 소유한다.
영향: 파일 저장은 documents와 연결할 수 있으나 지식 분류와 공개 상태는 knowledge가 관리한다.

## lms — 학습 경계

결정: lms는 과정, 수강, 평가, 이수 증명, 교육 캠페인을 소유한다.
영향: 직원 원천은 hr에서 참조하고 교육 이수 요구는 compliance/ehs와 연결한다.

## mail — 메일 경계

결정: mail은 업무 메일 계정, 메시지 메타데이터, 보관 정책, 메일 연계 상태를 소유한다.
영향: 메일 본문을 업무 원장으로 승격하려면 대상 모듈의 명시적 링크를 사용한다.

## maintenance — 정비 경계

결정: maintenance는 설비 정비, 작업지시, 예방보전, 고장 이력을 소유한다.
영향: 설비 자산은 assets를 참조하고 생산 영향은 manufacturing으로 이벤트를 발행한다.

## manufacturing — 제조 경계

결정: manufacturing은 BOM, 작업오더, 공정, 생산실적, 제조 원가 이벤트를 소유한다.
영향: 재고 이동은 stock, 회계 반영은 accounting으로 분리한다.

## marketing — 마케팅 경계

결정: marketing은 캠페인, 콘텐츠, 세그먼트, 마케팅 성과 상태를 소유한다.
영향: 영업 기회 전환은 crm으로 전달하고 실제 주문은 selling에서 관리한다.

## marketing-automation — 마케팅 자동화 경계

결정: marketing-automation은 자동 캠페인, journey, trigger, 발송 상태를 소유한다.
영향: 고객 원천은 crm/directory를 참조하고 발송 결과만 자동화 모듈에 보존한다.

## messenger — 메신저 경계

결정: messenger는 업무 채팅, 채널, 메시지 메타데이터, 알림 연결 상태를 소유한다.
영향: 업무 승인/요청은 원천 모듈 API로 연결하고 대화 로그는 messenger가 관리한다.

## plm — 제품수명주기 경계

결정: plm은 제품 구조, 변경요청, 승인, 릴리즈 상태를 소유한다.
영향: 생산 BOM 실행은 manufacturing으로 전달하고 설계 문서는 documents와 연결한다.

## pos — POS 경계

결정: pos는 매장 판매, 영수증, 현금 마감, 반품 접수, 오프라인 동기화 상태를 소유한다.
영향: 매출 확정은 selling/accounting으로 이벤트를 발행하고 재고 반영은 stock에서 처리한다.

## quality — 품질 경계

결정: quality는 검사, 부적합, CAPA, 품질 기준, 품질 승인 상태를 소유한다.
영향: 생산/입고 이벤트는 quality 검사를 요청하고 원거래는 manufacturing/buying/stock에 남긴다.

## rental — 렌탈 경계

결정: rental은 렌탈 계약, 출고, 반납, 연체, 렌탈 청구 상태를 소유한다.
영향: 재고/자산 상태는 stock/assets와 동기화하고 매출 이벤트는 selling/accounting으로 전달한다.

## reservation — 예약 경계

결정: reservation은 예약 가능성, 예약 요청, 확정, 취소, no-show 상태를 소유한다.
영향: 자원과 일정은 calendar/directory를 참조하고 예약 원장은 reservation에 둔다.

## rpa — RPA 경계

결정: rpa는 bot 정의, 실행, 큐, 실패 재시도, 자동화 감사 상태를 소유한다.
영향: bot이 업무 데이터를 변경할 때는 대상 모듈 API와 감사 정책을 따라야 한다.

## subscriptions — 구독 경계

결정: subscriptions는 구독 플랜, 갱신, 사용량, recurring invoice 요청을 소유한다.
영향: 청구 전표는 selling/accounting으로 연결하고 구독 상태 원장은 subscriptions가 관리한다.

## survey — 설문 경계

결정: survey는 설문, 응답, 점수, 배포 대상, 결과 집계를 소유한다.
영향: 응답자 원천은 hr/crm/directory를 참조하고 설문 결과 원장은 survey에 둔다.

## tms — 운송관리 경계

결정: tms는 운송계획, 배차, 운임, 추적, 배송 예외 상태를 소유한다.
영향: 출하 요청은 selling/stock에서 받고 운송 실행 상태는 tms가 관리한다.

## wiki — 위키 경계

결정: wiki는 내부 지식 페이지, 편집 이력, 링크 구조, 공개 범위를 소유한다.
영향: 공식 문서 파일은 documents와 연결할 수 있으나 페이지 구조는 wiki에 남긴다.

## workreport — 업무보고 경계

결정: workreport는 일일/주간 업무보고, 작업시간, 승인, 진행 요약을 소유한다.
영향: 프로젝트와 직원 원천은 projects/hr을 참조하고 보고 상태는 workreport가 관리한다.
