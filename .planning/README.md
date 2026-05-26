> **참고**: `strategy/`와 `program/` 디렉토리는 내부 전략 문서로 공개 저장소에서 제외된다.
> 공개 로드맵은 [ROADMAP.md](./ROADMAP.md)를 참조한다.

# OneERP Planning Hub

OneERP의 `.planning`은 GSD 실행 상태와 제품 전략, 프로그램 관리 문서를 함께 운영하는 허브다.

## 1. Orchestration Layer

GSD가 직접 읽고 쓰는 문서다. 짧고 구조화된 상태를 유지한다.

- `PROJECT.md` — 현재 제품 정의와 active scope
- `REQUIREMENTS.md` — 현재 마일스톤 요구사항과 traceability
- `ROADMAP.md` — 실행 phase와 success criteria
- `STATE.md` — 현재 위치, blocker, 다음 액션

## 2. Strategy Layer

상세한 제품 전략 문서다. 길어도 되며, ERP·그룹웨어·AI 전환 방향을 관리한다.

- `strategy/portfolio/` — 제품 비전, 포트폴리오 논지, 경쟁 우위
- `strategy/erp/` — ERP 제품 전략
- `strategy/groupware/` — 그룹웨어 전략
- `strategy/ai/` — AI 전략

## 3. Program Layer

실행 관리 문서다. 마일스톤, 릴리즈, 파일럿, 리스크, KPI를 관리한다.

- `program/milestones/`
- `program/releases/`
- `program/pilot/`
- `program/risks/`
- `program/metrics/`

## 운영 규칙

1. 실행 상태는 orchestration 문서에서만 갱신한다.
2. 상세한 전략 설명은 strategy 문서에만 쓴다.
3. PMO/릴리즈/파일럿 정보는 program 문서에만 쓴다.
4. `ROADMAP.md`의 각 phase는 상세 문서를 `Canonical refs`로 참조한다.
