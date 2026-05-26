---
title: OneERP 제품 범위 · Source of Truth
date: 2026-04-22
status: active
owner: product-scope-wg
---

# Source of Truth

본 문서는 OneERP 제품 범위 정의의 **단일 진실원(Single Source of Truth)** 이다.
경쟁 제품 대비 역량 커버리지는 `04-competitive-capability-matrix.md` 를 참조한다.

## 공식 레퍼런스

- `01-module-catalog.csv` — 모듈 · 서비스 · doctype 매핑 카탈로그
- `03-phase-roadmap.md` — 단계별 서비스 배치 로드맵
- `04-competitive-capability-matrix.md` — 공식 경쟁사 역량 매트릭스

## 의존성 정책

- 본 문서는 **경쟁사 매트릭스(`04-competitive-capability-matrix.md`)** 를 참조한다.
- 구(舊) 확장 목록(`modules/` 하위의 과거 확장 카탈로그)에 의존하지 않는다.
  과거의 중복 엔티티 표(PaymentReconciliation · TerritoryManagement · KnowledgeArticle 등)는
  본 Source of Truth 체계에서 제거되었다.

## 변경 절차

1. 카탈로그 CSV 또는 매트릭스 문서를 먼저 수정한다.
2. 본 문서는 인덱스/참조만 보관하며, 엔티티 개별 정의는 포함하지 않는다.
3. 변경 시 회귀 테스트 `core/tests/unit/test_product_scope_docs.py` 를 통과해야 한다.

## 카탈로그 집계 스냅샷

> 출처: `01-module-catalog.csv` (자동 집계 기준). 변경 시
> `core/tests/unit/test_doc_consistency.py::test_source_of_truth_스냅샷은_카탈로그_집계와_일치한다`
> 가 회귀를 차단한다.

| 지표 | 값 |
|------|----|
| 기본 capability 묶음 | 13 |
| 하위 capability 묶음 | 0 |
| 한국 특화 엔티티 | 3 |
