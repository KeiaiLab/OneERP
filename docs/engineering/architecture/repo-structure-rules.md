# 레포 구조/네이밍/소유권 정본

이 문서는 현재 OneERP 저장소의 **단일 참조원(canonical reference)** 이다.
구조/이름/소유권 판단이 필요하면 먼저 이 문서를 따른다.

## 1) 정본 top-level 구조

```text
OneERP/
├── core/
├── planes/
├── services/
├── deploy/catalog/
├── web/
├── docs/
├── tests/
└── scripts/
```

- `core/`: shared kernel 소유
- `planes/`: runtime assembly 소유
- `services/`: domain logic 소유
- `deploy/catalog/`: deployment SoT 소유
- `web/`: UI/capability wrapper 소유
- `docs/`: documentation SoT 소유
- `tests/`: 저장소 전체 테스트 소유
- `scripts/`: 검증/생성/개발 보조 스크립트 소유

## 2) 네이밍 규칙

### backend package

- 패턴: `oneerp_<domain>_app`
- 허용: `services/sales/selling/oneerp_selling_app/`
- 허용: `services/finance/payroll/oneerp_payroll_app/`
- 금지: `services/sales/selling/app/`
- 금지: `services/sales/selling/oneerp-selling-app/`

### plane

- canonical plane 이름: `api_plane`, `realtime_plane`, `worker_plane`, `scheduler_plane`, `edge_plane`, `extension_plane`
- 허용: `planes/api_plane/plane_api/main.py`
- 허용: `planes/worker_plane/plane_worker/main.py`
- 금지: `planes/api/`
- 금지: `planes/worker-plane/`

### docs path

- 문서 경로는 소문자 kebab-case를 우선한다.
- 아키텍처 문서는 `docs/engineering/architecture/*.md`
- 인벤토리 문서는 `docs/infra/inventory/*.md`
- 금지: `docs/Architecture/`
- 금지: canonical 문서를 복제한 루트 수준 설명 파일

### generated FE types

- generated 타입의 정본 경로는 `web/lib/types/generated/` 이다.
- 허용: `web/lib/types/generated/index.ts`
- 허용: `web/lib/types/generated/gateway.ts`
- 금지: `web/lib/types/gen/`
- 금지: `web/src/generated/`

## 3) 폴더 소유권 규칙

| 영역 | 소유 책임 |
|---|---|
| `core/` | 공통 커널과 cross-domain primitive |
| `planes/` | 런타임 조립, mount, bootstrap |
| `services/` | 도메인 규칙, 유스케이스, 서비스 구현 |
| `web/` | UI, capability wrapper, FE 전용 조립 |
| `deploy/catalog/` | 배포 생성물의 단일 원천 데이터 |
| `docs/` | 문서/인벤토리/결정 기록의 단일 원천 데이터 |

## 4) 허용/금지 예시

| 유형 | 허용 | 금지 |
|---|---|---|
| backend 서비스 | `services/stock/warehouse/oneerp_warehouse_app/main.py` | `services/stock/warehouse/main.py` |
| backend 테스트 | `services/stock/warehouse/tests/unit/test_*.py` | 서비스 루트에 흩어진 ad-hoc 테스트 |
| FE capability | `web/lib/capabilities/gateway-approval.ts` | `web/lib/capabilities/approval/gateway-approval.ts` |
| generated type | `web/lib/types/generated/index.ts` | `web/lib/generated-types/index.ts` |
| docs | `docs/engineering/architecture/repo-structure-rules.md` | `docs/repo-structure.md` |

## 5) 작은 폴더 템플릿 예시

### backend service 템플릿

```text
services/<domain>/<service>/
├── oneerp_<service>_app/
│   ├── main.py
│   ├── routes/
│   ├── schemas/
│   └── services/
└── tests/
    └── unit/
```

### FE capability area 템플릿

```text
web/lib/capabilities/
├── gateway-approval.ts
├── gateway-permissions.ts
└── gateway-tenants.ts
```

## 6) 운영 원칙

- 새 경로를 만들 때는 이 문서의 소유권에 맞춘다.
- 레거시 경로가 남아 있더라도 정본 판단은 이 문서로만 한다.
- 구조 변경이 필요하면 먼저 이 문서를 갱신하고, 이후 후속 문서를 정리한다.
