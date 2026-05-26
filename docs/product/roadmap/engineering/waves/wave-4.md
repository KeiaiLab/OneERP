---
owner: Wave 4 Owner
last_updated: 2026-04-16
stale_after_days: 180
audience: engineering
wave: 4
module_count: 8
---

# 모듈 집단 4 — 차별화·고급 (8 모듈)

> 마지막 집단. 경쟁 차별화 기능 중심. 이 집단의 전수 23/23 통과 = **전체 상용 완성**.

## 1. 포함 모듈

<!-- wave-module-table:4 -->
_Wave 4 의 8 모듈. 정본: ADR-0012 §6. 자동 렌더._

| 모듈 | 현재 라벨 | 통과 | 실패 | 구현 | /23 |
|---|---|---|---|---|---|
| `advanced-planning` | **alpha** | 6 | 17 | 23 | /23 |
| `consolidation` | **alpha** | 9 | 14 | 23 | /23 |
| `esg` | **alpha** | 9 | 14 | 23 | /23 |
| `iot` | **alpha** | 9 | 14 | 23 | /23 |
| `rpa` | **alpha** | 10 | 13 | 23 | /23 |
| `lms` | **alpha** | 10 | 13 | 23 | /23 |
| `workreport` | **alpha** | 10 | 13 | 23 | /23 |
| `reservation` | **alpha** | 9 | 14 | 23 | /23 |
<!-- /wave-module-table:4 -->

정본: [ADR-0012 §6](../../../../governance/adr/0012-commercialization-wave-mapping.md).

## 2. 진입 / 완료 조건

- 진입: 3차 집단의 80% 모듈이 23/23 기준 통과
- 완료: 8 모듈 전부 23/23 기준 통과 → **전체 상용 완성 선언**

## 3. 진행률 임베드

<!-- status-auto-embed:wave-4-progress -->
- 집단 4: 72 / 184 기준 통과 (39.1%)
- 모듈 수: 8
- 최고 통과 모듈: lms (10/23)
<!-- /status-auto-embed:wave-4-progress -->

## 4. 주요 위험

<!-- status-auto-embed:wave-4-risks -->
_위험 등록부 태그 `wave:N` 필터 결과. (데이터 소스 연결 대기)_
<!-- /status-auto-embed:wave-4-risks -->

## 5. 완료 모습

```bash
uv run python3 scripts/audit/wave_entry_check.py --wave 4 --assert commercial-ready
uv run python3 scripts/audit/commercial_readiness.py --all --format summary
# → 47 모듈 × 23 기준 = 1,081 중 1,081 GREEN 확인
```

## 6. 참조 블록

- [ADR-0012 모듈 분류](../../../../governance/adr/0012-commercialization-wave-mapping.md)
- [자동 생성 모듈 ERD 인덱스](../../../../generated/INDEX.md)
