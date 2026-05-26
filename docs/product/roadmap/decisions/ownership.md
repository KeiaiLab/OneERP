---
owner: Product Lead
last_updated: 2026-04-16
stale_after_days: 120
audience: shared
---

# 로드맵 파일 오너·갱신 주기

> 16 개 문서 + 4 자동화 스크립트 각각의 **누가·언제·무엇을 근거로** 갱신하는지 한 페이지에 모은다.

## 1. 파일별 오너·주기

| 파일 | 오너 | 갱신 트리거 | stale TTL | 참조 원본 |
|---|---|---|---|---|
| `README.md` | Product Lead | status 전환 + 월 1회 | 30일 | `status.md`, `matrix.md` |
| `overview.md` | PM | 월 1회 + 분기 전환 | 35일 | `.planning/strategy/portfolio/*`, `.planning/program/*` |
| `milestones.md` | PM | 분기 시작 + 전환 | 90일 | 자체 + `status.md` |
| `status.md` | Engineering Lead (수동 섹션) | 자동 일 1회 · 수동 주 1회 | 2일 | `docs/generated/commercial-status.md`, `docs/generated/wave-status.md` |
| `matrix.md` | Architecture Lead | Wave/Phase/기준 정의 변경 시만 | 180일 | ADR-0001 / 0002 / 0012 / 0014, ROADMAP.md |
| `translation.md` | PM + Engineering Lead | 분기 감사 | 90일 | — |
| `glossary.md` | Architecture Lead | 신규 축 도입 시만 | 180일 | ADR 전체 |
| `engineering/README.md` | Engineering Lead | Phase 전환 | 60일 | `phase-timeline.md`, `waves/*.md` |
| `engineering/phase-timeline.md` | Engineering Lead | Phase 전환 | 60일 | `.planning/ROADMAP.md`, `.planning/phases/*/PLAN.md` |
| `engineering/waves/wave-1.md` | Wave 1 Owner | 집단 활성 전환 + 월 1회 | 30일 | ADR-0012 §6 · `wave-status.md` |
| `engineering/waves/wave-2.md` | Wave 2 Owner | 집단 활성 전환 + 월 1회 | 60일 | 〃 |
| `engineering/waves/wave-3.md` | Wave 3 Owner | 집단 활성 전환 + 월 1회 | 90일 | 〃 |
| `engineering/waves/wave-4.md` | Wave 4 Owner | 집단 활성 전환 + 월 1회 | 180일 | 〃 |
| `gates/README.md` | QA Lead | ADR-0001 개정 시만 | 180일 | [ADR-0001](../../../governance/adr/0001-commercial-grade-definition.md) |
| `decisions/ownership.md` | Product Lead | 분기 감사 | 120일 | — |
| `decisions/change-log.md` | Product Lead | 로드맵 수정마다 | 없음 | — |

## 2. 스크립트 오너

| 스크립트 | 오너 | 역할 |
|---|---|---|
| `scripts/roadmap/status_render.py` | Engineering Lead | `status.md` 자동 섹션 렌더 |
| `scripts/roadmap/stale_check.py` | Engineering Lead | frontmatter TTL 초과 시 배너 주입 |
| `scripts/roadmap/forbidden_terms.py` | PM + Engineering Lead | Executive/Engineering 어휘 번짐 CI 차단 |
| `scripts/roadmap/link_check.py` | Engineering Lead | forward/reverse 링크 검증 |

## 3. 리뷰 사이클

- **주간 리뷰 (월)**: Engineering Lead 가 `status.md` 수동 주간 섹션 갱신 + `waves/wave-*.md` 중 활성 집단 문서 검토
- **월간 리뷰 (월초)**: PM 이 `status.md` 수동 월간 섹션 + `overview.md` 일부 갱신
- **분기 감사 (분기 첫 주)**: 본 문서 + `translation.md` 감사, 번역 번짐 사례 검토

## 4. 역할 정의

이 문서는 **역할 이름**을 쓰고 사람 이름을 쓰지 않는다. 실제 인물 매핑은 내부 조직도로 유지한다 (드리프트 방지).

- **Product Lead** — 제품 로드맵 전체 책임. Executive 레이어 승인 주체.
- **PM** — Executive 서사·마일스톤·번역표 주 저자.
- **Engineering Lead** — 실행 레이어·자동화·주간 status 책임.
- **Architecture Lead** — 4축 좌표계·ADR 정합성.
- **Wave N Owner** — 각 모듈 집단의 실행 책임. Engineering 하위 직책.
- **QA Lead** — 23 품질 기준 정의·측정 정합성.
