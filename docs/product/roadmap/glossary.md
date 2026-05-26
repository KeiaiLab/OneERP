---
owner: Architecture Lead
last_updated: 2026-04-16
stale_after_days: 180
audience: shared
---

# 4축 용어 사전

> 이 사전은 로드맵의 **축 의미**를 한 페이지로 묶는다. 각 축은 자기만의 정본을 가지며, 이 문서는 그 정본의 색인이다.

## Phase (작업 흐름축)

| 번호 | 이름 | 한줄 목표 |
|---|---|---|
| 1 | 이벤트 체인 안정화 | Outbox → NATS → Handler 공통 전제 확보 |
| 2 | 핵심 운영 E2E 완성 | 구매·경비·급여·제조 흐름 자동화 검증 |
| 3 | 협업·영업 흐름 + 결재 UI | CRM → Selling · Approval-Anywhere · 결재 웹 UI |
| 4 | 대시보드·보고서 사용자 출력 | KPI 대시보드 · PDF 출력 |
| 5 | 파일럿 운영 인프라 | 게이트웨이 · 매니페스트 · 관측성 · 백업·복구 |
| 6 | 통합 QA·성능·보안 | API / UI E2E · 성능 · 보안 점검 |
| 7 | 문서·튜토리얼·파일럿 검증 | 시나리오 / 매뉴얼 / 파일럿 자료 최종화 |

정본: [.planning/ROADMAP.md](../../../.planning/ROADMAP.md)

## Wave (모듈 집단축)

| 번호 | 모듈 수 | 성격 |
|---|---|---|
| 1 | 12 | 재무·운영 핵심 (매출영향·의존성 기반 최우선) |
| 2 | 13 | 운영 확산 |
| 3 | 14 | 지원·전문 |
| 4 | 8 | 차별화·고급 |

총 47 모듈. 분류 근거는 4 점수 (매출 영향 · 의존성 · 리스크 · 빈도).
정본: [docs/governance/adr/0012-commercialization-wave-mapping.md](../../governance/adr/0012-commercialization-wave-mapping.md)

## Stream (가치축)

| 이름 | 의미 |
|---|---|
| ERP | 회계 · 구매 · 판매 · 재고 · 생산 · 급여 |
| Groupware | 결재 · 협업 · 문서 · 의사결정 |
| AI | 자동화 · 요약 · 추천 · 예측 · 이상 탐지 |

모듈은 **다중 Stream 라벨**을 가질 수 있다 (예: Approval 은 ERP ∩ Groupware).
정본: [.planning/strategy/](../../../.planning/strategy/)

## Plane (런타임축)

| 이름 | 트래픽 모양 |
|---|---|
| API | 요청·응답 · OpenAPI 계약 · 낮은 지연 |
| Realtime | WebSocket · 알림 · 실시간 피드 |
| Worker | 비동기 처리 · Outbox 소비자 · 배치 |
| Scheduler | 주기 실행 · 크론 · 타임윈도우 |
| Edge | CDN · 정적 자산 · 지역 캐시 |
| Extension | 외부 플러그인 · SDK · 마켓플레이스 |

모듈은 **다중 Plane 라벨**을 가질 수 있다 (예: Approval = API + Realtime + Worker).
정본: [docs/governance/adr/0014-runtime-plane-decomposition.md](../../governance/adr/0014-runtime-plane-decomposition.md)

## 품질 기준 (23 기준, 5 영역)

| 영역 | 기준 수 | 질문 |
|---|---|---|
| 기능 완전성 | 5 | ERD 일치 · API 명세 · CRUD · 테스트 커버리지 |
| 통합 | 3 | Outbox 일관성 · 트레이스 · Contract 테스트 |
| 배포 | 3 | buildx · OpenAPI drift · ArgoCD 승격 |
| 운영 | 5 | SLO · 관측 · 백업 RPO · 복구 RTO · 알림 |
| 보안 | 7 | RBAC · ABAC · 멀티테넌시 티어 · 감사 로그 · 시크릿 · 취약점 · 인증 |

정본: [docs/governance/adr/0001-commercial-grade-definition.md](../../governance/adr/0001-commercial-grade-definition.md)

## 모듈 (47 단위)

모듈은 `services/` 하나 또는 여러 서비스와 패키지의 조합으로 구성된다.
전체 목록과 ERD: [docs/generated/INDEX.md](../../generated/INDEX.md) — 47 `erd-*.md` 파일 각각이 모듈 1개에 대응.

## 관련 용어

| 용어 | 뜻 |
|---|---|
| commercial-ready | 모듈이 23 기준을 **모두** 통과한 상태. 출시 자격. |
| pre-commercial | 기능 영역 5 기준만 통과. 내부 사용 가능. |
| alpha | 기능 영역 일부만 통과. 47 모듈 현재 라벨 (2026-04-16 시점). |
| Gate A / B / C | v1.0 프로그램 게이트. PILOT-READINESS.md 참조. |
