# 웨이브 진입/완료 현황 (자동 생성)

> 근거: ADR-0012 §2 웨이브 분류 + §6 진입/완료 조건 + §10 실행 항목.
> 생성: `scripts/audit/wave_entry_check.py`.

**활성 웨이브: Wave 1**

## 웨이브별 상태

| Wave | 모듈 수 | pre-commercial+ | commercial-ready | 진입? | 완료? |
|------|---------|------------------|-------------------|-------|--------|
| Wave 1 | 12 | 3/12 | 3/12 | ✅ | ❌ |
| Wave 2 | 13 | 0/13 | 0/13 | ⏳ | ❌ |
| Wave 3 | 14 | 0/14 | 0/14 | ⏳ | ❌ |
| Wave 4 | 8 | 0/8 | 0/8 | ⏳ | ❌ |

### Wave 1
- 라벨 분포: alpha=9 / beta=0 / pre-commercial=0 / commercial-ready=3
- 필수 commercial-ready 모듈(❌): selling, buying, stock, accounting
- 진입 조건 체크리스트(수동 포함):
  - [ ] ADR-0008 관측성 인프라 가동 (Prometheus/Loki/Tempo) — 수동
  - [ ] ADR-0006 authorize() 코어 구현 — 수동
  - [ ] ADR-0005 TenantScopedRepository 강제 — 수동
- 모듈 라벨:
  - `gateway` — (현재 라벨은 commercial_readiness.py 참조)
  - `directory` — (현재 라벨은 commercial_readiness.py 참조)
  - `accounting` — (현재 라벨은 commercial_readiness.py 참조)
  - `hr` — (현재 라벨은 commercial_readiness.py 참조)
  - `payroll` — (현재 라벨은 commercial_readiness.py 참조)
  - `selling` — (현재 라벨은 commercial_readiness.py 참조)
  - `buying` — (현재 라벨은 commercial_readiness.py 참조)
  - `stock` — (현재 라벨은 commercial_readiness.py 참조)
  - `expenses` — (현재 라벨은 commercial_readiness.py 참조)
  - `projects` — (현재 라벨은 commercial_readiness.py 참조)
  - `crm` — (현재 라벨은 commercial_readiness.py 참조)
  - `portal` — (현재 라벨은 commercial_readiness.py 참조)

### Wave 2
- 라벨 분포: alpha=13 / beta=0 / pre-commercial=0 / commercial-ready=0
- 진입 조건 체크리스트(수동 포함):
  - [ ] Wave 1 전수 pre-commercial+
- 모듈 라벨:
  - `manufacturing` — (현재 라벨은 commercial_readiness.py 참조)
  - `quality` — (현재 라벨은 commercial_readiness.py 참조)
  - `assets` — (현재 라벨은 commercial_readiness.py 참조)
  - `maintenance` — (현재 라벨은 commercial_readiness.py 참조)
  - `ecommerce` — (현재 라벨은 commercial_readiness.py 참조)
  - `pos` — (현재 라벨은 commercial_readiness.py 참조)
  - `subscriptions` — (현재 라벨은 commercial_readiness.py 참조)
  - `integration-hub` — (현재 라벨은 commercial_readiness.py 참조)
  - `calendar` — (현재 라벨은 commercial_readiness.py 참조)
  - `documents` — (현재 라벨은 commercial_readiness.py 참조)
  - `mail` — (현재 라벨은 commercial_readiness.py 참조)
  - `messenger` — (현재 라벨은 commercial_readiness.py 참조)
  - `board` — (현재 라벨은 commercial_readiness.py 참조)

### Wave 3
- 라벨 분포: alpha=14 / beta=0 / pre-commercial=0 / commercial-ready=0
- 진입 조건 체크리스트(수동 포함):
  - [ ] Wave 2 전수 pre-commercial+
- 모듈 라벨:
  - `consolidation` — (현재 라벨은 commercial_readiness.py 참조)
  - `esg` — (현재 라벨은 commercial_readiness.py 참조)
  - `compliance` — (현재 라벨은 commercial_readiness.py 참조)
  - `clm` — (현재 라벨은 commercial_readiness.py 참조)
  - `ehs` — (현재 라벨은 commercial_readiness.py 참조)
  - `plm` — (현재 라벨은 commercial_readiness.py 참조)
  - `tms` — (현재 라벨은 commercial_readiness.py 참조)
  - `fleet` — (현재 라벨은 commercial_readiness.py 참조)
  - `advanced-planning` — (현재 라벨은 commercial_readiness.py 참조)
  - `marketing` — (현재 라벨은 commercial_readiness.py 참조)
  - `marketing-automation` — (현재 라벨은 commercial_readiness.py 참조)
  - `gtm` — (현재 라벨은 commercial_readiness.py 참조)
  - `lms` — (현재 라벨은 commercial_readiness.py 참조)
  - `workreport` — (현재 라벨은 commercial_readiness.py 참조)

### Wave 4
- 라벨 분포: alpha=8 / beta=0 / pre-commercial=0 / commercial-ready=0
- 진입 조건 체크리스트(수동 포함):
  - [ ] Wave 3 전수 pre-commercial+
  - [ ] ADR-0007 v1 stable
- 모듈 라벨:
  - `analytics` — (현재 라벨은 commercial_readiness.py 참조)
  - `rpa` — (현재 라벨은 commercial_readiness.py 참조)
  - `iot` — (현재 라벨은 commercial_readiness.py 참조)
  - `knowledge` — (현재 라벨은 commercial_readiness.py 참조)
  - `wiki` — (현재 라벨은 commercial_readiness.py 참조)
  - `survey` — (현재 라벨은 commercial_readiness.py 참조)
  - `reservation` — (현재 라벨은 commercial_readiness.py 참조)
  - `rental` — (현재 라벨은 commercial_readiness.py 참조)


