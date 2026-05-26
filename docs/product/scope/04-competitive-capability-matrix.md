---
title: OneERP 경쟁사 역량 매트릭스
date: 2026-04-22
status: active
owner: product-scope-wg
---

# Competitive Capability Matrix

OneERP 범위 정의의 외부 기준점이다. 주요 ERP 제품의 공식 제품 문서를 공식 출처로 한다.

## 공식 출처 (Official References)

| 제품 | 공식 레퍼런스 URL |
|------|-------------------|
| ERPNext | https://docs.erpnext.com/ |
| Odoo | https://www.odoo.com/documentation/ |
| SAP S/4HANA | https://help.sap.com/docs/SAP_S4HANA_CLOUD |
| Oracle Fusion Cloud ERP | https://docs.oracle.com/en/cloud/saas/financials/index.html |
| Microsoft Dynamics 365 | https://learn.microsoft.com/en-us/dynamics365/ |

## 역량 커버리지 (요약)

| 역량 | ERPNext | Odoo | SAP S/4HANA | Oracle Fusion Cloud ERP | Microsoft Dynamics 365 | OneERP 대응 |
|------|---------|------|-------------|-------------------------|------------------------|-------------|
| 회계/전표 | O | O | O | O | O | `accounting` 서비스 (P1) |
| 판매 주문 | O | O | O | O | O | `sales` (P1) |
| 구매/재고 | O | O | O | O | O | `scm` (P1) |
| 인사 | O | O | O | O | O | `hr` (P2) |
| 예산/재무 | 부분 | O | O | O | O | `finance` (P2) |
| 물류/출하 | O | O | O | O | O | `logistics` (P2) |
| 마케팅 | 부분 | O | 부분 | O | O | `marketing` (P3) |
| 협업 | 부분 | 부분 | 부분 | 부분 | O | `collab` (P3) |
| 컴플라이언스 | 부분 | 부분 | O | O | O | `compliance` (P3) |
| EHS | X | 부분 | O | O | 부분 | `ehs` (P3) |

## 고객 지원 역량

공식 경쟁사 대부분은 별도 "Service / Helpdesk / Support" 모듈을 제공하나,
OneERP 는 본 범위에서 **지원 전용 서비스를 제공하지 않는다**. 사용자 문의/티켓은
`collab` 워크스페이스 또는 외부 헬프데스크 연동(TBD — business ownership)으로 대체한다.
