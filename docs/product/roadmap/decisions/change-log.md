---
owner: Product Lead
last_updated: 2026-04-16
audience: shared
---

# 로드맵 변경 이력

> 이 로그는 **로드맵 문서 자체**의 변경을 기록한다. 제품 전체의 결정 이력은 `docs/governance/adr/` 의 ADR 체계를 따른다.

## 2026-04-16 · 초기 신설 후 확장

- `docs/product/roadmap/` 16 문서 + `scripts/roadmap/` 4 스크립트 신설
- 4 축 좌표계 공식화 (Phase · Wave · Stream · Plane)
- 23 품질 기준 기반 단일 진행률 공식 `Σ g(m) / 1,081` 정의
- Executive ↔ Engineering 어휘 번역표 및 금지 어휘 CI 차단 도입
- 단일 mutable 데이터 `status.md` 원칙 확립
- 로드맵 → 원본 SoT 단방향 참조 원칙 확립 (`link_check.py --reverse` 로 차단)

## 2026-04-16 · 외부 CI 워크플로 의존성 제거

- 커밋 caec0a2 에서 추가되었던 외부 CI 설정 디렉토리 전수 삭제. 해당 `quality-gates.yml` 의 `roadmap-gate` job 도 함께 소멸.
- 로드맵 게이트는 **`Makefile` 의 `verify-roadmap` 타겟**만으로 실행된다. 외부 CI 시스템을 도입할 경우 동일 타겟을 호출하도록 연결.
- `scripts/audit/commercial_readiness.py` 의 G3-5 의존성 스캔 대상에서 해당 외부 CI 경로를 제거. 현재는 `.github/workflows/` 와 `scripts/ci/` 만 스캔.
- `engineering/phase-timeline.md` 의 Phase 3·4 경로를 실제 디렉토리명(`03-collab-sales-approval-ui`, `04-dashboard-reporting-ui`) 으로 교정하고, Phase 2~7 전 링크를 실제 존재하는 디렉토리로 연결.
