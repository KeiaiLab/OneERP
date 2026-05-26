# OneERP Graphify CI 통합 설계서

## 1. 배경

OneERP는 `services/`, `planes/`, `core/`, `web/`, 그리고 다수의 설계 문서로 구성된 대형 저장소다.
현재도 ERD, roadmap, 상태 보드 등 자동 생성 문서가 존재하지만, 코드/문서/구조를 하나의 지식 그래프로 탐색하는 산출물은 없다.

사용자 요구는 `safishamsi/graphify`를 이용해:

- 코드베이스 전체 온보딩/분석용 그래프를 만들고
- `main` 머지 시와 주기 스케줄에서 자동 갱신하며
- 저장소에는 읽기 쉬운 요약본만 남기고
- 전체 원본 산출물은 CI 아티팩트로 보관하는 것이다.

## 2. 결정과 가정

이번 설계는 아래 결정을 전제로 한다.

- 적용 목적은 **OneERP 전체 코드베이스 온보딩/분석용 지식 그래프 생성**이다.
- 실행 방식은 **루트 스크립트 중심 하이브리드**다.
- 실행 시점은 **`main` 머지 시 + 주기 스케줄**이다.
- 저장소에는 **요약본만 커밋**하고, `graph.html`/`graph.json` 등 원본 결과는 **CI artifact**로만 보관한다.

추가 가정은 다음과 같다.

- `graphify`는 현재 저장소에 적용돼 있지 않다.
- 외부 도구 설치는 `graphifyy` 패키지 + `graphify` CLI 기준으로 진행한다.
- CI 러너에는 `graphify`가 비대화형으로 실행될 수 있는 인증 수단이 주입돼야 한다.
- 루트 저장소의 CI 엔트리포인트는 문서와 실제 트리 사이에 차이가 있을 수 있으므로, 구현은 **`scripts/graphify/run.sh`를 정본**으로 삼고 CI는 thin wrapper만 둔다.

## 3. 입력 범위

그래프 입력 범위는 아래로 고정한다.

- 포함:
  - `core/`
  - `services/`
  - `planes/`
  - `web/`
  - `docs/governance/`
  - `docs/engineering/`
  - `docs/product/roadmap/`
- 제외:
  - `node_modules/`
  - `.venv/`
  - `.next/`
  - `artifacts/`
  - `docs/generated/`
  - `.worktrees/`
  - `__pycache__/`
  - `.pytest_cache/`
  - `.ruff_cache/`
  - `.planning/`

즉, `docs/` 전체를 그래프에 넣지 않고 핵심 설계 문서만 포함한다.

## 4. 접근안 비교

### 접근안 A. CI 직접 실행형

- CI workflow 안에서 `graphify` 설치, 입력 수집, 결과 정리, 커밋까지 전부 처리한다.
- 장점: 워크플로우만 보면 동작이 보인다.
- 단점: 로컬 실행과 CI 실행이 쉽게 분리되고, CI 엔진 변경 시 유지보수 비용이 커진다.

### 접근안 B. 루트 스크립트 중심형

- `scripts/graphify/run.sh`가 모든 로직을 담당하고, 로컬과 CI가 동일 스크립트를 호출한다.
- 장점: 실행 규약의 단일 SoT가 생기고, 디버깅과 로컬 재현이 쉽다.
- 단점: 스크립트 책임이 커질 수 있어 출력 규칙을 명확히 정해야 한다.

### 접근안 C. 문서 생성 파이프라인 일체형

- `scripts/docs/*` 체계에 완전히 흡수해 docs 생성 파이프라인의 일부로 다룬다.
- 장점: 문서 생성 계열과 일관성이 높다.
- 단점: `graphify`는 문서 생성만이 아니라 코드 구조 분석 도구이므로 docs 전용 파이프라인 안에 넣으면 책임 경계가 흐려진다.

### 선택

이번 설계는 **접근안 B. 루트 스크립트 중심형**을 채택한다.

이 선택은:

- 실행 정본은 `scripts/graphify/run.sh`
- 저장소 반영 정본은 `docs/generated/graphify/`
- CI는 thin wrapper

로 역할을 분리한다는 뜻이다.

## 5. 산출물 구조

### 5.1 전체 원본 산출물

`graphify`의 원본 결과는 항상 임시 작업 디렉토리 아래 생성한다.

- 작업 디렉토리: `artifacts/graphify/latest/`
- 예상 결과:
  - `artifacts/graphify/latest/graph.html`
  - `artifacts/graphify/latest/graph.json`
  - `artifacts/graphify/latest/GRAPH_REPORT.md`
  - `artifacts/graphify/latest/cache/`
  - 필요 시 `obsidian/`, `wiki/`

이 경로는 **커밋 금지**다.

### 5.2 저장소 커밋 대상

저장소에는 아래 두 파일만 반영한다.

- `docs/generated/graphify/GRAPH_REPORT.md`
- `docs/generated/graphify/INDEX.md`

`GRAPH_REPORT.md`는 원본 결과에서 읽기 좋은 요약본 역할을 한다.
`INDEX.md`는 생성 시각, 입력 범위, 제외 범위, 실행 소스(`main`/`schedule`), 아티팩트 위치 규약을 기록한다.

### 5.3 문서 인덱스 연결

`docs/generated/INDEX.md` 또는 `docs/INDEX.md`에는 `graphify` 요약본 링크를 추가한다.
단, 이 링크는 `docs/generated/graphify/GRAPH_REPORT.md`를 가리켜야 하며, `graph.html` 같은 무거운 아티팩트는 링크하지 않는다.

## 6. 실행 흐름

### 6.1 로컬 실행

개발자는 아래와 같은 단일 명령으로 그래프를 재생성할 수 있어야 한다.

- `make graphify`

내부적으로는:

1. `graphify` 설치 여부 확인
2. 입력 범위 스테이징
3. 제외 경로 적용
4. `graphify` 실행
5. 원본 결과를 `artifacts/graphify/latest/`에 정리
6. 요약본을 `docs/generated/graphify/GRAPH_REPORT.md`로 복사/정규화
7. `INDEX.md` 갱신

순서로 처리한다.

### 6.2 CI 실행

CI는 두 가지 트리거를 가진다.

- `main` 머지 시:
  - 최신 `main` 기준 그래프 생성
  - `docs/generated/graphify/GRAPH_REPORT.md`와 `INDEX.md` 갱신
  - 전체 원본은 artifact 업로드
- 스케줄 실행:
  - 같은 스크립트를 주기적으로 돌려 구조 변경 누락을 보정
  - 결과는 artifact 업로드
  - 요약본 커밋 정책은 `main` 머지 시와 동일하거나, 필요 시 schedule은 PR만 생성하도록 제한 가능

CI workflow는 스크립트를 호출만 해야 하며, 입력/출력 규칙을 자체적으로 다시 구현하지 않는다.

## 7. 실패 처리와 운영 규칙

`graphify`는 외부 설치/인증에 의존하므로, 일반 품질 게이트와 분리해야 한다.

- `quality-gates`를 막는 핵심 workflow 안에 직접 넣지 않는다.
- 전용 workflow에서 실패를 보고하고, 실패 로그와 원인을 artifact 또는 job summary로 남긴다.
- 설치 실패, 인증 실패, 출력 파일 누락은 모두 명시적 실패로 처리한다.
- 단, 이 실패가 일반 BE/FE 품질 게이트 전체를 red 로 만들지는 않도록 분리한다.

즉:

- **제품 품질 게이트와 graphify 생성 게이트는 분리**
- **graphify workflow는 독립적으로 성공/실패를 표시**

정책을 따른다.

## 8. 보안과 시크릿

`graphify` 실행에 필요한 인증값은 저장소에 두지 않는다.

- CI secret 또는 runner 환경변수로만 주입
- 스크립트는 실행 초기에 필수 인증값 존재 여부를 검사
- 없으면 곧바로 실패하고 원인을 출력

또한 입력 범위에는 `artifacts/`, `.venv/`, 캐시류, 생성 문서가 제외되어야 하므로,
민감 정보나 대용량 생성물이 그래프 입력으로 흘러들어가지 않게 한다.

## 9. 성공 기준

이번 통합의 성공 기준은 아래와 같다.

1. 개발자는 `make graphify`로 동일한 그래프 생성 파이프라인을 로컬에서 재현할 수 있다.
2. `main` 머지 시와 스케줄 실행 시 동일 스크립트가 호출된다.
3. 저장소에는 항상 최신 `docs/generated/graphify/GRAPH_REPORT.md`와 `INDEX.md`가 존재한다.
4. `graph.html`, `graph.json` 등 원본 결과는 저장소에 커밋되지 않고 CI artifact로 보관된다.
5. graphify 실패는 독립적으로 관측 가능하지만, 일반 품질 게이트 전체를 막지는 않는다.

## 10. 비목표

이번 설계의 비목표는 다음과 같다.

- `graphify` 결과를 OneERP의 기존 ERD 산출물과 강제로 병합
- `docs/` 전체를 그래프 입력에 포함
- `graph.html`/`graph.json`을 저장소에 커밋
- graphify 실행 로직을 CI workflow 파일마다 중복 구현
- graphify 결과를 제품 런타임 기능으로 노출

## 11. 발견사항

- 루트 저장소에는 `.gitea/workflows/`가 현재 보이지 않지만, 문서와 일부 서브모듈에는 Gitea workflow 전제가 남아 있다.
- 따라서 구현은 **CI wrapper의 실제 위치를 먼저 확인**하거나, 없으면 루트 workflow 디렉토리를 신설해야 한다.
- `graphify`는 “Claude Code skill” 성격이 강하므로, CI에서 비대화형 실행이 가능한 인증/실행 모델을 먼저 검증해야 한다.

## 12. 승인 상태

- 상태: 승인됨
- 승인 일시: 2026-04-16
- 승인 범위:
  - 입력 범위는 코드 루트 + 핵심 설계 문서만 포함
  - 원본 그래프는 artifact, 요약본은 저장소 커밋
  - 실행 시점은 `main` 머지 + 주기 스케줄
  - 접근 방식은 루트 스크립트 중심형
