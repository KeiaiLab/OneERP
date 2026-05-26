---
title: RALPH-LOOP-PROMPT (보관 · 폐기됨)
status: archived
deprecated_on: 2026-04-22
superseded_by: /commercial-engine
owner: ops-automation-wg
---

# RALPH-LOOP-PROMPT (보관 · 폐기됨)

> **본 문서는 폐기 완료 되었다 (2026-04-22).**
> 실제 실행은 `/commercial-engine` 슬래시 커맨드가 대체한다.
> 본 문서는 v1 계약의 **역사적 계약 명세** 를 남겨 회귀 테스트
> `tests/unit/test_ralph_loop_total_commercialization_docs.py` 가 지시하는 계약
> 조항을 보존한다. 새로운 작업은 본 문서가 아니라 `/commercial-engine` 을 사용한다.

## 1. 상용 완성 계약 (역사적)

- 대상 범위: **47모듈** × 23 게이트 = 총 **1,081** 셀
- 완성 정의: 전 모듈 전 게이트 PASS · 전원 `commercial-ready` 라벨
- 판정 게이트: `scripts/ci/run_total_commercial_gate.sh`
- 증거 구조: `.reports[]` 배열에 모듈별 23 게이트 판정 결과 적재

## 2. 본 문서가 **명시하지 않는** 것

- 구체적 반복 횟수 · 타임라인 · 파일럿 분류 (v2 `/commercial-engine` 이 재정의)
- Wave 단위 전수 PASS 로의 중간 성공 선언 (정직 모드에서 폐기)

## 3. 보존 사유

- Spec I 종결 시점의 계약 문구를 검색·추적 가능하게 보존한다.
- 회귀 테스트는 본 문서를 계약 정본으로 참조하되, 실행 로직은 `/commercial-engine` 을 사용한다.

## 4. 참조

- 폐기 기록: `PROGRESS.md` 의 "v1 Ralph-Loop 시대 (보존)" 섹션
- 후속 엔진: `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md`
- 후속 플랜: `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md`
