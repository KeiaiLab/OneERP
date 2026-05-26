---
owner: Wave 2 Owner
last_updated: 2026-04-16
stale_after_days: 60
audience: engineering
wave: 2
module_count: 13
---

# 모듈 집단 2 — 운영 확산 (13 모듈)

> 재무·운영 핵심(1차 집단) 이후 **이어지는** 집단. 활성 조건은 1차 집단의 80% 모듈이 23/23 기준 통과한 시점.

## 1. 포함 모듈

<!-- wave-module-table:2 -->
_Wave 2 의 13 모듈. 정본: ADR-0012 §6. 자동 렌더._

| 모듈 | 현재 라벨 | 통과 | 실패 | 구현 | /23 |
|---|---|---|---|---|---|
| `manufacturing` | **alpha** | 10 | 13 | 23 | /23 |
| `quality` | **alpha** | 10 | 13 | 23 | /23 |
| `assets` | **alpha** | 11 | 12 | 23 | /23 |
| `maintenance` | **alpha** | 10 | 13 | 23 | /23 |
| `ecommerce` | **alpha** | 9 | 14 | 23 | /23 |
| `pos` | **alpha** | 9 | 14 | 23 | /23 |
| `subscriptions` | **alpha** | 10 | 13 | 23 | /23 |
| `integration-hub` | **alpha** | 7 | 16 | 23 | /23 |
| `documents` | **beta** | 12 | 11 | 23 | /23 |
| `compliance` | **alpha** | 9 | 14 | 23 | /23 |
| `ehs` | **alpha** | 9 | 14 | 23 | /23 |
| `plm` | **alpha** | 10 | 13 | 23 | /23 |
| `survey` | **alpha** | 11 | 12 | 23 | /23 |
<!-- /wave-module-table:2 -->

정본: [ADR-0012 §6](../../../../governance/adr/0012-commercialization-wave-mapping.md).

## 2. 진입 / 완료 조건

- 진입: 1차 집단의 80% 모듈이 23/23 기준 통과 (ADR-0002 단일 활성 집단 원칙)
- 완료: 13 모듈 중 80% 이상이 23/23 기준 통과

## 3. 진행률 임베드

<!-- status-auto-embed:wave-2-progress -->
- 집단 2: 127 / 299 기준 통과 (42.5%)
- 모듈 수: 13
- 최고 통과 모듈: documents (12/23)
<!-- /status-auto-embed:wave-2-progress -->

## 4. 의존 작업 흐름 (선행 설계)

이 집단이 **활성이 되기 전** 에도 선행 설계 투자는 허용된다 (ADR-0012 개정 PR 등). 실행 자원 전환만 금지.

v1.0 파일럿 출시(M7) 이후 주 추진 흐름:

| 활동 | 내용 |
|---|---|
| 모듈 이관 | 1차 집단에서 합의된 이벤트 체인·공통 인프라를 그대로 활용 |
| 기능 영역 채움 | 각 모듈의 기능 기준 #1~#5 |
| 운영 영역 반영 | 1차 집단의 운영·배포 기준 그대로 적용 |

## 5. 주요 위험

<!-- status-auto-embed:wave-2-risks -->
_위험 등록부 태그 `wave:N` 필터 결과. (데이터 소스 연결 대기)_
<!-- /status-auto-embed:wave-2-risks -->

## 6. 완료 모습

```bash
uv run python3 scripts/audit/wave_entry_check.py --wave 2 --assert ready-to-enter
# → 1차 집단 80% 통과 확인 + 2차 집단 준비 상태 보고

uv run python3 scripts/audit/wave_entry_check.py --wave 2 --assert commercial-ready
# → 2차 집단 80% 이상 23/23 기준 통과 확인
```

## 7. 참조 블록

- [ADR-0012 모듈 분류](../../../../governance/adr/0012-commercialization-wave-mapping.md)
- [자동 생성 모듈 ERD 인덱스](../../../../generated/INDEX.md)
