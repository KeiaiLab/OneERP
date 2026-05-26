---
owner: Wave 3 Owner
last_updated: 2026-04-16
stale_after_days: 90
audience: engineering
wave: 3
module_count: 14
---

# 모듈 집단 3 — 지원·전문 (14 모듈)

> 운영 확산(2차 집단) 이후 활성화되는 집단. 특화 업무·산업별 요구에 대응.

## 1. 포함 모듈

<!-- wave-module-table:3 -->
_Wave 3 의 14 모듈. 정본: ADR-0012 §6. 자동 렌더._

| 모듈 | 현재 라벨 | 통과 | 실패 | 구현 | /23 |
|---|---|---|---|---|---|
| `calendar` | **alpha** | 10 | 13 | 23 | /23 |
| `board` | **alpha** | 10 | 13 | 23 | /23 |
| `mail` | **alpha** | 6 | 17 | 23 | /23 |
| `messenger` | **alpha** | 6 | 17 | 23 | /23 |
| `wiki` | **alpha** | 10 | 13 | 23 | /23 |
| `knowledge` | **alpha** | 11 | 12 | 23 | /23 |
| `analytics` | **alpha** | 8 | 15 | 23 | /23 |
| `rental` | **alpha** | 10 | 13 | 23 | /23 |
| `fleet` | **alpha** | 9 | 14 | 23 | /23 |
| `tms` | **alpha** | 9 | 14 | 23 | /23 |
| `marketing` | **alpha** | 11 | 12 | 23 | /23 |
| `marketing-automation` | **alpha** | 7 | 16 | 23 | /23 |
| `gtm` | **alpha** | 10 | 13 | 23 | /23 |
| `clm` | **alpha** | 8 | 15 | 23 | /23 |
<!-- /wave-module-table:3 -->

정본: [ADR-0012 §6](../../../../governance/adr/0012-commercialization-wave-mapping.md).

## 2. 진입 / 완료 조건

- 진입: 2차 집단의 80% 모듈이 23/23 기준 통과
- 완료: 14 모듈 중 80% 이상이 23/23 기준 통과

## 3. 진행률 임베드

<!-- status-auto-embed:wave-3-progress -->
- 집단 3: 125 / 322 기준 통과 (38.8%)
- 모듈 수: 14
- 최고 통과 모듈: knowledge (11/23)
<!-- /status-auto-embed:wave-3-progress -->

## 4. 주요 위험

<!-- status-auto-embed:wave-3-risks -->
_위험 등록부 태그 `wave:N` 필터 결과. (데이터 소스 연결 대기)_
<!-- /status-auto-embed:wave-3-risks -->

## 5. 완료 모습

```bash
uv run python3 scripts/audit/wave_entry_check.py --wave 3 --assert commercial-ready
```

## 6. 참조 블록

- [ADR-0012 모듈 분류](../../../../governance/adr/0012-commercialization-wave-mapping.md)
- [자동 생성 모듈 ERD 인덱스](../../../../generated/INDEX.md)
