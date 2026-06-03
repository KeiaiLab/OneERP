# OneERP

ERPNext를 대안할 목적으로 만드는 오픈소스 ERP. Python 백엔드 기반이며, 한국 비즈니스 환경(전자세금계산서·4대보험 등)을 1차 목표로 한다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.14-blue.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)

## 현재 상태

**Alpha (v0.1.x) — 활발히 개발 중. 아직 동작하는 릴리스가 아니다.**

이 저장소에는 판매·구매·재고·회계·HR 등 약 40개 도메인의 데이터 모델과 서비스 코드가 들어 있다(서비스 코드만 약 19만 줄, 테스트 약 500개). 다만 다음 이유로 **현재 이 저장소만으로는 빌드·실행이 되지 않는다**:

- 공통 커널 `core/` (서비스 코드 1,300여 개 파일이 `oneerp_core`로 import하는 핵심 모듈)가 별도 비공개 서브모듈로 분리되어 있어 이 저장소에 포함돼 있지 않다.
- 프론트엔드 `web/`도 별도 서브모듈이며 포함돼 있지 않다.
- 배포 산출물(`deploy/`)과 일부 통합 경로는 아직 정리되지 않았다.

즉 도메인 로직은 상당 부분 작성돼 있으나, **end-to-end로 띄울 수 있는 상태는 아니다.** 공개 정리·기여 환경 구성이 진행 중이다. 진행 상황은 [ROADMAP.md](ROADMAP.md)를 참고.

## 목표

- ERPNext의 핵심 모듈(판매·구매·재고·제조·회계·HR 등)에 대응하는 기능을 오픈소스로 제공
- 한국 특화 기능: 전자세금계산서 연동, 4대보험 자동 계산, 멀티테넌시
- 도메인별로 분리된 서비스 구조 + 런타임 plane 분해(동기 API / 워커 / 스케줄러 / 게이트웨이 등)

## 저장소 구성

```
OneERP/
├── services/         # 도메인 서비스 (sales, scm, finance, hr, collab, platform, ...)
│                     #   각 도메인은 Pydantic 모델 + FastAPI 라우트로 구성
├── planes/           # 런타임 plane 진입점 (api / realtime / worker / scheduler / edge / extension)
│                     #   각 plane이 services/의 도메인을 마운트하는 구조 (ADR-0014)
├── docs/             # 아키텍처·도메인 명세·운영 문서
├── tests/            # 교차 서비스 / E2E 테스트
├── core/             # 공통 커널 — 별도 서브모듈 (현재 미포함)
└── web/              # 프론트엔드(Next.js) — 별도 서브모듈 (현재 미포함)
```

구현된 도메인 영역(일부): 판매(selling/crm/pos/commerce/reservation), 공급망(buying/stock/manufacturing/qm), 회계·재무(accounting/expenses/payroll), 인사(hr/learning), 협업(projects/documents/wiki/calendar 등), 자산/PLM, 컴플라이언스, 물류.

전체 구조는 [docs/ARCHITECTURE-MAP.md](docs/ARCHITECTURE-MAP.md), plane 분해 결정은 [docs/governance/adr/0014-runtime-plane-decomposition.md](docs/governance/adr/0014-runtime-plane-decomposition.md) 참고.

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 백엔드 | Python 3.14, FastAPI, Pydantic v2 |
| 패키지 관리 | uv (workspace) |
| 데이터 | FerretDB(MongoDB 프로토콜) / PostgreSQL, Valkey, NATS JetStream |
| 프론트엔드 | Next.js (별도 서브모듈) |
| 린트/포맷 | ruff (Python), Biome (TS) |

## 개발 환경

> 참고: 위 [현재 상태](#현재-상태)에 적은 대로 공통 커널(`core/`)이 아직 이 저장소에 없어
> 전체 빌드는 되지 않는다. 아래는 환경이 갖춰진 뒤의 기준 흐름이다.

```bash
git clone <repo-url> OneERP
cd OneERP
git submodule update --init --recursive   # core/, web/ 가져오기 (접근 권한 필요)

uv sync          # 백엔드 의존성
```

도메인 코드 자체를 둘러보는 데에는 서브모듈이 없어도 된다. `services/` 아래 각 도메인의
`models/`, `dto.py`, `main.py`를 보면 데이터 모델과 라우트 구조를 확인할 수 있다.

## 로드맵

자세한 내용은 [ROADMAP.md](ROADMAP.md). 요약하면:

- **Alpha (현재)** — 핵심 도메인 CRUD, 런타임 plane 구조 안정화, 빌드/실행 환경 정리
- **Beta** — 전자세금계산서 연동, 4대보험 계산, 멀티테넌시, OpenAPI 문서
- **v1.0** — ERPNext 핵심 모듈 기능 동등성, 프로덕션 배포 가이드

## 기여

초기 단계이므로 설계 논의와 피드백을 환영한다. 자세한 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고.

1. 관심 있는 영역의 Issue를 확인하거나 새로 연다
2. 큰 변경은 먼저 Discussion/Issue에서 설계를 논의한다
3. 테스트와 함께 PR을 제출한다 (테스트 없는 기능은 받지 않는다)

코드와 주석은 한국어로 작성한다.

## 라이선스

[MIT License](LICENSE) · Copyright (c) 2026 keiailab
