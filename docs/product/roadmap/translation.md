---
owner: PM + Engineering Lead
last_updated: 2026-04-16
stale_after_days: 90
audience: shared
---

# 어휘 번역표 · 금지 어휘 목록

> 이 파일은 **Executive 레이어와 Engineering 레이어의 유일한 허용 중복**이다.
> 양쪽 레이어가 같은 현실을 서로 다른 단어로 가리키되, 번역 규칙이 흐려지지 않게 유지한다.

## 1. 핵심 번역 7쌍

| Executive 어휘 | Engineering 어휘 |
|---|---|
| 상용화 완료 | 47 모듈 전수 commercial-ready 라벨 (ADR-0001 §6 23 품질 기준 통과) |
| 핵심 업무 흐름 | FL1~FL7 E2E + 작업 흐름 1~4 outbox → NATS → handler → UI 체인 |
| 파일럿 가능 | v1.0 프로그램 Gate A 통과 (PILOT-READINESS.md §엔트리) |
| 이번 분기 목표 | 활성 모듈 집단의 pre-commercial N/47 + 작업 흐름 X~Y 품질 기준 진행률 |
| 경쟁 우위 작동 | Approval-Anywhere E2E + CRM → Selling 바인딩 + AI 경비 분류 KPI 측정 |
| 운영 기준선 | Gate B — 배포·관측·복구 문서·실행 결과 검증 완료 |
| AI가 시간 절감 | AI KPI 자동 입력 절감률 + 제안 채택률 파이프라인 가동 |

## 2. Executive 레이어 금지 어휘 (CI 차단)

다음 어휘가 `README.md`, `overview.md`, `milestones.md` 에 등장하면 `scripts/roadmap/forbidden_terms.py` 가 build fail 한다. 예외는 **본 `translation.md` 번역표 안의 인용**만.

- `Phase` / `phase`
- `게이트`
- `ADR-`
- `pre-commercial`
- `outbox`
- `NATS`
- `DoD`
- `Plane` / `plane`
- `Wave` / `wave` (단, "모듈 집단" 으로 번역해야 함 — 본 번역표와 matrix.md 는 예외)

## 3. Engineering 레이어 금지 어휘 (CI 차단)

다음 프레이즈가 `engineering/**/*.md` 에 등장하면 fail:

- `경쟁 우위가` / `경쟁에서`
- `이사회` / `투자자`
- `파일럿 고객` (단, 파일럿 절차 문서 링크는 허용)
- `고객 가치`
- `제품 약속`
- `북극성` (measurement 대신 "기준" 어휘 사용)

## 4. 예외 처리

- `translation.md` 자체와 `matrix.md` 는 양쪽 어휘를 **정의 목적**으로 포함할 수 있다.
- 번역표 내부의 코드 블록·표·인용은 스캔에서 제외한다 (`forbidden_terms.py` 가 frontmatter 기반으로 판단).
- 외부 원본 파일명·경로·링크 텍스트는 금지 어휘에 해당하지 않는다 (예: `docs/governance/adr/` 경로에 `ADR` 포함).

## 5. 갱신 절차

분기 1회 감사:

1. 지난 분기 문서에서 번역 번짐 사례 수집.
2. 두 방향 금지 어휘 목록 보강.
3. `forbidden_terms.py` 가 실제로 잡아내는지 재현 테스트.
4. `decisions/change-log.md` 에 개정 이력 기록.
