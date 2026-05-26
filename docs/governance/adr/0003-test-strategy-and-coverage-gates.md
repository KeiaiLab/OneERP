# ADR-0003: 테스트 전략 및 커버리지 게이트

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, QA 리드 |
| 영향 범위 | 전체 — 모든 BE/FE 코드, CI 파이프라인, PR 머지 게이트 |
| 관련 ADR | ADR-0001(상용 정의 G1-3·G1-4), ADR-0008(관측성), ADR-0010(배포) |
| 후속 phase | P-003 (CI 게이트 자동화), 모듈별 상용화 phase의 G1-3/G1-4 충족 |

## 1. 맥락(Context)

ADR-0001 G1-3(통합 테스트 전수 통과)와 G1-4(도메인 단위 테스트
≥90% / 분기 ≥80%)를 받아 구체화한다. 현재 OneERP의 테스트 자산은
`docs/engineering/ci/test-strategy.md`에 따르면:

- pytest `importmode=importlib`, 마커 `integration`/`e2e` 정의됨
- 단위 테스트는 `packages/core` 3건, 4개 서비스 헬스 1건씩(총 7건)
- 통합: `test_ferretdb_smoke.py` ping 1건
- E2E: 시나리오 정의는 있으나 자동화 부재
- FE: Biome lint·typecheck만 게이트화, 단위/E2E 테스트 자산 없음

이 상태에서 G1-4 90%를 모듈마다 직접 강요하면 거의 모든 모듈이 즉시
실패한다. **표준화된 단계적 임계값과 측정 도구**가 필요하다. 또한
"테스트 없는 기능은 존재할 수 없다"는 전역 규칙(CLAUDE.md)을
강제할 CI 차단 메커니즘이 명시돼야 한다.

근거 인벤토리:
- `docs/engineering/ci/test-strategy.md` — 현 3계층 정의
- `docs/product/scope/03-e2e-scenarios.md` — 5대 E2E 시나리오
- `pyproject.toml` (root) — pytest 설정
- `apps/web/biome.json`, `apps/web/package.json` — FE 게이트
- 전역 규칙: "테스트 없는 기능 금지", "검증되지 않은 성공은 성공이 아니다"

## 2. 결정(Decision)

OneERP는 4계층 테스트 피라미드와 라벨 단계별 임계값을 채택한다.

- **4계층**: 단위(Unit) → 컴포넌트(Component) → 통합(Integration) → E2E
- **라벨별 임계값**: ADR-0001 라벨에 따라 커버리지·통과율 게이트가 다르다
- **머지 차단**: PR 단위로 변경 줄(line)에 대한 테스트 신규 또는 갱신
  없이는 머지 차단 (patch coverage 정책)
- **회귀 방지**: 5대 E2E 시나리오는 main 브랜치에 머지되는 모든
  PR에서 nightly 자동 실행, 실패 시 즉시 revert 옵션 활성화
- **단일 측정 도구**: BE는 `coverage.py + pytest-cov`, FE는 `vitest` +
  `@vitest/coverage-v8` (Tailwind/Next 플러그인 호환). E2E는 `playwright`
- **속도 SLA**: 단위 테스트 슈트 < 90초, 컴포넌트 < 5분, 통합 < 15분,
  E2E < 30분 (CI 단일 잡 기준)

- **범위 In**: `services/*`, `packages/*`, `apps/web/*`의 모든 신규 코드.
- **범위 Out**: 마이그레이션 스크립트(별도 검증), 일회성 데이터 픽스처.
- **발효 시점**: 본 ADR 채택 즉시. 단, 90% 임계값은 모듈이
  `pre-commercial` 라벨 진입 시점부터 강제.

## 3. 대안(Alternatives Considered)

### 대안 A — 균일 80% 강제
- 설명: 전 모듈 단일 임계값.
- 장점: 단순.
- 단점: alpha 모듈의 진입 장벽 과대, beta 모듈의 강제력 부족.
- 채택하지 않은 이유: ADR-0001의 라벨 단계와 정합 필요.

### 대안 B — 커버리지 무관, 결과만 검증
- 설명: 통과/실패만 보고 비율은 무시.
- 장점: 게이트 경량.
- 단점: 신규 코드의 테스트 누락을 잡지 못함, 회귀 방지 효과 약화.
- 채택하지 않은 이유: G1-4 정량 게이트와 충돌.

### 대안 C — Mutation 테스트 도입
- 설명: `mutmut`/`stryker`로 테스트 품질까지 강제.
- 장점: 테스트의 실효성까지 측정.
- 단점: 실행 시간 폭증(현 슈트 X10), 도입 학습 비용.
- 채택하지 않은 이유: 본 ADR 발효 6개월 후 별도 ADR로 점진 도입 검토.

### 대안 D — 현 상태 유지
- 비용: PR마다 즉흥 판단, 테스트 누락 빈발.
- 채택하지 않은 이유: G1-4 강제 불가.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 3/5 | 초기 도구 도입 + CI 시간 증가 |
| 리스크 | 5/5 | 회귀 차단·신규 결함 조기 발견 |
| 운영 | 4/5 | patch coverage가 일상 PR 흐름에 자연 정착 |
| 팀 역량 | 4/5 | pytest는 익숙, vitest/playwright는 학습 필요 |

## 5. 영향(Consequences)

### 5.1 긍정적
- 신규 결함 조기 발견, 회귀 사고 감소.
- "테스트 없는 PR" 자동 차단.
- 라벨 승급 의사결정에 객관 입력.

### 5.2 부정적
- CI 시간 증가 (대응: 분기 병렬화 + 캐싱).
- 초기 작성 부담 (대응: ADR-0001 웨이브 진행 phase 안에 포함).

### 5.3 호환성
- 기존 7건 단위 테스트 그대로 유지.
- 기존 통합 테스트 1건 유지, 게이트 통과율은 모듈별로 계측 시작.

### 5.4 측정 지표

| 지표 | 현재 | 목표(6개월) |
|------|------|-------------|
| 단위 테스트 수 | 7건 | 1500건+ |
| 통합 테스트 수 | 1건 | 200건+ |
| E2E 시나리오 자동화 | 0/5 | 5/5 |
| BE 라인 커버리지(평균) | 측정 시작 | 70% |
| FE 라인 커버리지(평균) | 0% | 60% |
| nightly E2E 안정성 | n/a | ≥ 95% pass |

## 6. 4계층 정의

### 6.1 단위 (Unit)
- 대상: 함수/클래스 단일, 외부 의존 없음(DB/네트워크/파일)
- 도구: `pytest`, `vitest`
- 위치: 파일과 동일 패키지 내 `tests/unit/`
- 속도: 슈트 전체 < 90초

### 6.2 컴포넌트 (Component)
- 대상: 모듈 내부 다중 클래스 협력, 외부는 페이크/스텁
- 도구: `pytest` + 페이크 리포지토리, FE는 `@testing-library/react`
- 위치: `tests/component/`
- 속도: 슈트 < 5분

### 6.3 통합 (Integration)
- 대상: 실제 FerretDB + API + 인증 미들웨어
- 마커: `@pytest.mark.integration`
- 환경: `docker compose up -d ferretdb` 또는 testcontainers
- 위치: `tests/integration/`
- 속도: 슈트 < 15분

### 6.4 E2E (End-to-end)
- 대상: 5대 시나리오(판매/구매/재고/회계/권한) + 모듈별 핵심 1~3 시나리오
- 도구: `playwright` (FE→BE→DB 전체 경로)
- 마커: `@pytest.mark.e2e` (Python 측 헬퍼 호출 시)
- 위치: `tests/e2e/`
- 속도: 슈트 < 30분 (병렬)

## 7. 라벨별 게이트

| 게이트 | alpha | beta | pre-commercial | commercial-ready |
|--------|-------|------|----------------|------------------|
| 단위 라인 커버리지 | n/a | ≥ 60% | ≥ 80% | ≥ 90% |
| 단위 분기 커버리지 | n/a | ≥ 50% | ≥ 70% | ≥ 80% |
| 통합 테스트 (CRUD 전 흐름) | n/a | 100% | 100% | 100% |
| 통합 테스트 (도메인 규칙) | n/a | ≥ 50% | ≥ 80% | 100% |
| 모듈별 E2E 시나리오 | n/a | ≥ 1건 | ≥ 3건 | 모듈 핵심 100% |
| 5대 E2E 통과율 | n/a | n/a | ≥ 95% | ≥ 99% |
| Mutation score (선택) | n/a | n/a | n/a | ≥ 70% (도입 후) |

라벨 진입 시점에 자동 검사. 미통과 시 라벨 부여 거부.

## 8. PR 머지 게이트 (모든 라벨 공통)

다음을 통과하지 못한 PR은 머지 차단된다.

1. **Patch coverage**: PR이 추가/수정한 라인의 ≥ 80%가 테스트로 커버
   - 도구: `diff-cover` + `coverage.xml`
   - 예외: 자동 생성 코드, 마이그레이션, `pragma: no cover` (사유 주석 필수)
2. **신규 BE 라우트**: 통합 테스트 1개 이상 추가
3. **신규 FE 페이지**: 컴포넌트 테스트 1개 이상 추가
4. **모든 슈트 통과**: 단위·컴포넌트·통합 (E2E는 nightly)
5. **린트·타입체크**: ruff/biome 0건, ty/tsc 0건

## 9. CI 잡 구성

```yaml
# 개념 다이어그램
ci:
  pr:
    - lint           # ruff format/check, biome ci
    - typecheck      # ty, tsc
    - unit           # pytest -m "not integration and not e2e", vitest
    - component      # pytest -m component, vitest --component
    - integration    # docker compose + pytest -m integration
    - patch-coverage # diff-cover --fail-under=80
    - build          # pnpm build, uv build
  nightly:
    - e2e            # playwright (5 시나리오 + 모듈별)
    - perf           # k6 baseline
    - dep-audit      # pip-audit, npm audit, gitleaks
```

## 10. 테스트 데이터 표준

- **고정 시드**: `tests/fixtures/seed.py`가 테넌트 2개, 사용자 5명,
  회사 2개, 통화 2종을 결정론적으로 생성
- **격리**: 각 테스트는 자체 데이터베이스 또는 트랜잭션 롤백
- **시간 의존성**: `freezegun`으로 고정 (랜덤 실패 차단)
- **외부 호출**: VCR/`responses`로 녹화-재생
- **금지**: 테스트가 외부 네트워크·외부 API·운영 데이터에 접근

## 11. 회귀 추적

- 모든 INC-* 인시던트는 회귀 테스트로 변환 → `tests/regression/INC-NNNN_*.py`
- 회귀 테스트는 영구 보존, 삭제 시 ADR 또는 PR 본문에 사유 명시
- 회귀 슈트는 단위 슈트의 일부로 항상 실행

## 12. 실행 항목

- [ ] 인프라팀 — `coverage.xml` 생성·`diff-cover` CI 잡 추가 — 2026-04-30 — phase: P-003
- [ ] FE팀 — `vitest` 도입, `apps/web/`에 첫 컴포넌트 테스트 — 2026-05-15
- [ ] QA 리드 — `playwright` 5대 시나리오 골격 — 2026-05-31
- [ ] 모든 모듈 오너 — `pre-commercial` 진입 전 G1-4 임계값 충족
- [ ] 인프라팀 — nightly E2E + 결과 Slack 게시 — 2026-06-15

## 13. 검증

- [ ] CI에 patch coverage 차단 적용
- [ ] `commercial-readiness.py`가 라벨별 임계값 비교
- [ ] 회귀 테스트 추가 누락 PR(인시던트 클로즈) 자동 경고

## 14. 부록 — pytest 마커 표준

| 마커 | 의미 | 기본 실행? |
|------|------|-----------|
| (없음) | 단위 | 예 |
| `component` | 컴포넌트 | 예 |
| `integration` | 통합 (FerretDB 필요) | 아니오 (CI 잡 별도) |
| `e2e` | E2E (배포 환경 필요) | 아니오 (nightly) |
| `slow` | 60초 초과 | 아니오 (옵션 잡) |
| `flaky` | 재시도 허용 (심사 후 부여) | 예 (3회 재시도) |

## 15. 참고 자료

- `docs/engineering/ci/test-strategy.md`
- ADR-0001 (G1-3, G1-4 게이트 정의)
- coverage.py: <https://coverage.readthedocs.io>
- diff-cover: <https://github.com/Bachmann1234/diff_cover>
- Playwright: <https://playwright.dev>
