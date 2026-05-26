---
title: OneERP 모듈 ↔ 서비스 매핑
status: draft
owner: product-scope-wg
date: 2026-04-22
---

# OneERP 모듈 ↔ 서비스 매핑

> 제품 관점의 **모듈** 이 모노레포의 어떤 **서비스 디렉토리** 에 배치되는지를
> 단일 문서로 추적한다. CSV 원본은 `01-module-catalog.csv` 이며, 본 문서는
> 그룹별 가독성 요약이다.

## 범례

- **모듈**: 사용자 기능 단위 (매출·매입·회계·인사 등)
- **서비스**: `services/<group>/<service>/` 경로에 위치한 런타임 서비스
- **비고**: 공유 호스트·플랫폼 서비스와의 관계

## 재무 · 회계

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| accounting | `services/finance/accounting/` | GL 정본 |
| consolidation | `services/finance/consolidation/` | 그룹 연결 |
| treasury | `services/finance/treasury/` | 자금 (예정) |

## 인사 · 급여

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| hr-core | `services/hr/hr/` | 인사 코어 |
| payroll | `services/hr/payroll/` | 급여 |

## 판매 · CRM · 전자상거래

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| selling | `services/sales/selling/` | 판매 |
| crm | `services/sales/crm/` | CRM |
| pos | `services/sales/pos/` | POS |
| ecommerce | `services/sales/ecommerce/` | 이커머스 |
| subscriptions | `services/sales/subscriptions/` | 구독 |
| rental | `services/sales/rental/` | 렌탈 |

## 구매 · 재고 · 제조

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| buying | `services/scm/buying/` | 구매 |
| stock | `services/scm/stock/` | 재고 |
| manufacturing | `services/scm/manufacturing/` | 제조 |
| quality | `services/scm/quality/` | 품질 |
| plm | `services/scm/plm/` | PLM |
| advanced-planning | `services/scm/advanced-planning/` | APS |
| maintenance | `services/scm/maintenance/` | 설비 유지 |

## 자산 · 경비 · 물류

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| assets | `services/assets/assets/` | 자산 |
| expenses | `services/assets/expenses/` | 경비 |
| fleet | `services/logistics/fleet/` | 차량 |
| tms | `services/logistics/tms/` | 운송 |

## 프로젝트 · 분석 · ESG

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| projects | `services/collab/projects/` | 프로젝트 |
| analytics | `services/platform/analytics/` | 분석 |
| esg | `services/ehs/esg/` | ESG |
| ehs | `services/ehs/ehs/` | 환경·보건·안전 |
| iot | `services/platform/iot/` | IoT |

## 협업 · 문서 · 포털

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| documents | `services/collab/documents/` | 문서관리 |
| calendar | `services/collab/calendar/` | 캘린더 |
| mail | `services/collab/mail/` | 내부 메일 |
| messenger | `services/collab/messenger/` | 메신저 |
| wiki | `services/collab/wiki/` | 위키 |
| knowledge | `services/collab/knowledge/` | 지식 |
| board | `services/collab/board/` | 게시판 |
| survey | `services/collab/survey/` | 설문 |
| workreport | `services/collab/workreport/` | 업무 보고 |
| portal | `services/portal/portal/` | 포털 |
| directory | `services/platform/directory/` | 디렉토리·SSO |

## 플랫폼 · 시스템

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| gateway | `services/platform/gateway/` | API 게이트웨이 |
| integration-hub | `services/platform/integration-hub/` | 통합 허브 |
| rpa | `services/platform/rpa/` | 자동화 |
| clm | `services/compliance/clm/` | 계약 라이프사이클 |
| compliance | `services/compliance/compliance/` | 컴플라이언스 |
| lms | `services/collab/lms/` | 학습 |
| reservation | `services/collab/reservation/` | 자원 예약 |

## 마케팅

| 모듈 | 서비스 경로 | 비고 |
|------|--------------|------|
| marketing | `services/marketing/marketing/` | 마케팅 코어 |
| marketing-automation | `services/marketing/marketing-automation/` | 마케팅 자동화 |
| gtm | `services/marketing/gtm/` | GTM |

## 관련 문서

- `docs/product/scope/00-source-of-truth.md`
- `docs/product/scope/01-module-catalog.csv`
- `docs/product/scope/IMPLEMENTATION-MASTER-PROMPT.md`
- `docs/governance/adr/0011-runtime-cluster-decomposition.md`
- `docs/governance/adr/0014-runtime-plane-decomposition.md`
