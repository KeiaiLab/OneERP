---
owner: QA Lead
last_updated: 2026-04-16
stale_after_days: 180
audience: shared
---

# 23 품질 기준 — 5 영역 요약

> 이 문서는 ADR-0001 의 **구조와 숫자**를 한 페이지로 소환한다. 각 기준의 판정 절차·측정 방법은 [ADR-0001 §2 · §6](../../../governance/adr/0001-commercial-grade-definition.md) 정본에 있다.
>
> 모듈 1개는 23 기준 전수 GREEN = **commercial-ready 라벨** = 출시 자격.

## 1. 영역별 기준 분포 (ADR-0001 §6 정본)

| 영역 | 기준 수 | 누적 | 주 관심 질문 | 게이트 |
|---|---|---|---|---|
| 기능 완전성 | 5 | 5 | ERD/API/CRUD/단위/UI 가 정의대로 동작하는가 | G1-1 ~ G1-5 |
| 비기능 품질 | 5 | 10 | SLO/부하/회귀/chaos/i18n 기준선 | G2-1 ~ G2-5 |
| 보안·컴플라이언스 | 5 | 15 | 인증/권한/테넌시/감사/의존성 통제 | G3-1 ~ G3-5 |
| 운영 준비 | 5 | 20 | 관측/runbook/backup/rollback/oncall | G4-1 ~ G4-5 |
| 사용자 가치 | 3 | 23 | 매뉴얼/튜토리얼/UAT | G5-1 ~ G5-3 |

합계 23 기준. 1 모듈 × 23 기준 = 23 판정 단위. 47 모듈 × 23 = **1,081** 판정 단위가 전체 분모.

## 2. 판정 절차 요약

| 단계 | 어디에 있는가 |
|---|---|
| 기준 정의 | [ADR-0001 §2](../../../governance/adr/0001-commercial-grade-definition.md#2-기준-정의) |
| 판정 주체 | [ADR-0001 §6.1](../../../governance/adr/0001-commercial-grade-definition.md#6-판정) |
| 증거 산출물 | [`docs/generated/commercial-status.md`](../../../generated/commercial-status.md) |
| 자동 검증 스크립트 | [`scripts/audit/commercial_readiness.py`](../../../../scripts/audit/commercial_readiness.py) |
| 집단 진입·완료 체크 | [`scripts/audit/wave_entry_check.py`](../../../../scripts/audit/wave_entry_check.py) |

## 3. 현재 진행률

<!-- status-auto-embed:gate-distribution -->
| 라벨 | 모듈 수 |
|------|---------|
| alpha | 46 |
| beta | 1 |
| pre-commercial | 0 |
| commercial-ready | 0 |
<!-- /status-auto-embed:gate-distribution -->

## 4. 기준 변경의 파급

기준 정의를 **추가·수정·삭제**하려면:

1. [ADR-0001](../../../governance/adr/0001-commercial-grade-definition.md) 에 대한 개정 PR 발의
2. `commercial_readiness.py` 의 기준 체크 로직 동기 변경
3. `docs/generated/commercial-status.md` 재생성
4. 본 문서의 `§1` 표 수치 갱신
5. 모든 [engineering/waves/wave-*.md](../engineering/waves/) 의 진행률 임베드 재렌더

이 5 단계가 한 PR 로 묶여 통과하지 않으면 기준 변경은 반영되지 않은 것으로 간주한다.
