---
title: OneERP 프로젝트 상태 (STATUS)
status: active
owner: core-team
date: 2026-04-22
---

# OneERP 프로젝트 상태 (STATUS)

> 실시간 진행 상황과 활성 Wave/Phase 좌표의 **단일 진입점**.
> 상세 통계는 `docs/product/roadmap/status.md` (자동 렌더) 를 참조한다.

## 현재 활성 좌표

- 활성 Wave: Wave 1 (게이트웨이 14 셀 · Spec II)
- 활성 Phase: Phase 1 — 이벤트 체인 안정화
- 감사 체계: Commercial Grade v2 (Strict Evidence)
- 기준 베이스 커밋: `256855f4`

## 최근 이정표

- 2026-04-22 — Spec I 종결 · v1 Ralph-Loop 폐기 · v2 baseline 0/1081 리셋 완료
- 2026-04-22 — Spec II wave-001 · gateway 10/14 PASS 기록
- 2026-04-17 — user-story 실행 카탈로그 설계 문서 착수

## 트러블슈팅

`make smoke` 실패 시 증상별 처방은 아래 가이드를 참고한다.

- 의존성 문제: `uv sync --all-packages --all-groups` 재실행
- 타입 오류: `uv run ty check .` 출력 확인
- 테스트 실패: `uv run pytest -m "not integration and not e2e" -q` 로 로컬 재현

## 관련 문서

- `docs/INDEX.md` — 문서 인덱스 전체
- `docs/product/roadmap/status.md` — 자동 렌더 로드맵 상태
- `docs/product/scope/MODULE-SERVICE-MAP.md` — 모듈 ↔ 서비스 매핑
- `HANDOFF.md` — 세션 핸드오프
- `PROGRESS.md` — 상용화 진척 로그
