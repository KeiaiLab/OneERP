---
title: OneERP 구현 마스터 프롬프트
status: draft
owner: product-scope-wg
date: 2026-04-22
language: 한국어
---

# OneERP 구현 마스터 프롬프트

> 본 문서는 구현 루프 실행 시 에이전트가 일관된 판단 기준으로 모듈·시나리오·검증
> 경계를 따르도록 하는 **프롬프트 정본** 이다. 새로운 에이전트 세션은 본 문서를
> 최우선 컨텍스트로 로드한다.

## 프롬프트 역할

본 프롬프트는 각 실행 세션에서 다음 3 가지 역할을 한다.

1. 입력 해석 — 사용자의 요청을 OneERP 모듈·게이트·Wave 좌표로 환산한다.
2. 실행 안전망 — 검증 없는 커밋·거짓 완료 선언 등 `AGENTS.md` 금지 사항 위반을 차단한다.
3. 보고 규칙 — 완료 판단과 증거 인용이 항상 동일한 형식을 따르게 한다.

## 입력 컨텍스트 우선순위

입력이 충돌할 때는 다음 순으로 정본을 따른다.

1. `AGENTS.md` · `/Users/phil/.claude/CLAUDE.md` · `.claude/CLAUDE.md` — 전역 규약
2. `docs/product/scope/00-source-of-truth.md` — 제품 범위 SoT
3. `docs/product/scope/MODULE-SERVICE-MAP.md` — 모듈·서비스 매핑
4. `docs/product/IMPLEMENTATION-GAP-REPORT.md` — 구현 갭 보고서
5. `docs/product/PROJECT-INTEGRITY-REPORT.md` — 서비스/문서 무결성 보고서
6. `docs/product/scope/08-amaranth10-gap-analysis.md` — Amaranth10 갭 분석
7. 현재 활성 Wave/Phase 의 ADR (`docs/governance/adr/*`)

## 전역 실행 원칙

- 모든 산출물·주석·커밋 메시지는 **한국어** 로 작성한다.
- 테스트 없는 기능은 존재할 수 없다. 실행하여 검증된 증거만 "완료" 로 승격한다.
- 외부 라이브러리는 사용 전 `context7` MCP 로 최신 공식 문서를 조회한다.
- 배포 이미지는 `docker buildx` + `masblue-builder` 로 `linux/amd64` 만 빌드한다.
- `print()` 금지. 로깅을 사용한다 (ruff T20 규칙).

## 작업 선택 알고리즘

1. 활성 Wave 의 미완료 모듈을 `scripts/audit/commercial_readiness.py` 로 식별
2. 모듈별 실패 게이트 중 **가장 저비용 + 가장 높은 점수 기여** 순으로 정렬
3. 의존 선행 작업 (ADR·스크립트·런북) 이 없는 게이트부터 착수
4. 한 iteration 에서는 하나의 모듈에 집중 (컨텍스트 스위치 비용 회피)
5. iteration 종료 시 `./scripts/ci/run.sh` 전수 통과 확인

## 모듈 실행 루프

각 모듈을 아래 7 단계로 진행한다.

1. SoT 조회: `00-source-of-truth.md` · `01-module-catalog.csv`
2. 시나리오 명세: `docs/tutorials/<module>.md` 에서 대표 시나리오 확인
3. 코드 설계: 서비스 레이어 / 라우트 / 모델 / 이벤트 계약
4. 단위 테스트 · 통합 테스트 · E2E 시나리오 추가
5. 런북 · 매뉴얼 · 튜토리얼 문서 동기화
6. `scripts/ci/run.sh` 와 `commercial_readiness.py --module <m>` 통과
7. 증거 아티팩트 저장 (`artifacts/verification/session-N/`)

## 사용자 시나리오 명세 형식

```
# <모듈> — <시나리오 이름>

## 사전 조건 (Prerequisites)
- ...

## 완료 조건 (Completion Criteria)
- ...

## 다음 단계 (Next Step)
- ...
```

- **한국어** 로 작성. 사용자 관점 동사를 쓴다 ("등록한다", "확인한다").
- 입력·출력·허용 오류를 모두 명시한다.

## 테스트 전략

- 4 계층 피라미드: unit → integration → contract → e2e.
- 게이트 라벨별 커버리지 임계치는 `docs/governance/adr/0003-*.md` 를 따른다.
- UI 회귀는 **Playwright** (웹) 와 **Appium** (모바일) 로 수행한다.
- 각 PR 은 `patch coverage` 게이트를 통과해야 머지 가능하다.

## 테스트 데이터 라이프사이클

- 테넌트 기본: `default` (관리자 username `demo`, password `demo1234`).
- 테스트 데이터 초기화는 `scripts/dev/seed-data.sh` 로 멱등 수행한다.
- 테스트 종료 시 생성 문서는 소유 테스트가 정리 (fixture `tmp_*` 네임스페이스).
- 프로덕션 데이터는 절대 시드에 사용하지 않는다.

## 검증 명령어

세션 완료 전 아래를 전수 통과시킨다.

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check .
uv run pytest -m "not integration and not e2e" services/ packages/ core/ tests/
pnpm --filter @oneerp/web lint
pnpm --filter @oneerp/web typecheck
pnpm --filter @oneerp/web build
./scripts/ci/run.sh
```

## 완료 보고 형식

완료 보고는 다음 4 항목을 포함한다.

- 변경 요약 (2–3 줄)
- 증거 (명령어 출력·커밋 SHA·아티팩트 경로)
- 영향 범위 (모듈·게이트·Wave 좌표)
- 잔여 위험·후속 권장 (없으면 "없음")

## 금지 사항

- 검증되지 않은 "완료" 선언.
- 범위 외 수정 (사용자 동의 없는 리팩토링).
- 프로덕션 시크릿·토큰 커밋.
- `kubectl port-forward` 직접 사용 (드라이브 기반 접근 사용).
- git-flow 미사용 브랜치 작업.

## 참조 문서

- `docs/product/scope/00-source-of-truth.md`
- `docs/product/scope/MODULE-SERVICE-MAP.md`
- `docs/product/IMPLEMENTATION-GAP-REPORT.md`
- `docs/product/PROJECT-INTEGRITY-REPORT.md`
- `docs/product/scope/08-amaranth10-gap-analysis.md`
- `docs/governance/adr/` — 불변 규약 ADR 전수
- `./scripts/ci/run.sh` — CI 게이트 진입점
