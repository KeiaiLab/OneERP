# 개발 표준(초안)

## 툴체인 버전 (고정)

<!-- BEGIN VERSIONS -->
**Python 툴체인 (고정)**

- `uv==0.11.1`
- `ruff==0.15.0`
- `ty==0.0.15`

**FE 툴체인 (고정)**

- `pnpm==10.30.3`
- `biome>=2.0.0`
- `next>=16.0.0` (App Router + Turbopack)
- `tailwindcss>=4.1.0` (CSS-first)

<sub>자동 생성 — `versions.toml` 수정 후 `render_versions.py --write`.</sub>
<!-- END VERSIONS -->

## 로컬 품질 게이트

```bash
./scripts/ci/run.sh
```

## 코드 규칙(요약)

### BE (Python)

- ruff format을 유일한 포매터로 사용
- ruff lint + ty type check 필수
- pytest (unit + integration) 필수

### FE (TypeScript)

- biome ci를 포매터 + 린터로 사용
- tsc --noEmit 타입체크 필수
- next build 빌드 검증 필수

### 공통

- lint/type/test는 CI에서 필수
- 새 “결정”은 ADR로 기록: `docs/governance/adr/`

## 커밋/PR 규칙

### 커밋 메시지 형식 (Wave 체계, 2026-04-12~)

모든 신규 커밋은 다음 형식을 따릅니다:

```
<type>(<scope>): <한국어 설명> — <BR 번호> (Wave N-X)
```

- **type**: [Conventional Commits](https://www.conventionalcommits.org/) 접두사 — `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- **scope**: 서비스명(`accounting` / `selling` / `stock` / `gateway` 등) 또는 `repo` / `docs` / `ci`
- **BR 번호** (선택): 비즈니스 요구사항 코드, 쉼표·물결표로 나열 — 예: `BR-WRP-012,020` 또는 `BR-LMS-002~010,013,015`
- **Wave 접미사** (필수): `(Wave N-X)` — 예: `(Wave 6-R)`, `(Wave 7-A)`. M0 복잡성 감축 작업은 `(M0 PR-0.N)` 형식 사용
- 본문에는 "왜" 변경했는지를 기술

### 예시

- `feat(workreport): 집계·리마인더 서비스 — BR-WRP-012,020 + 계산로직 4.1~4.7 (Wave 6-R)`
- `feat(lms): 수강·이수·한국 5대 법정교육 — BR-LMS-002~010,013,015 (Wave 6-R)`
- `chore(repo): autonomous 로그 9,660건 제거 + gitignore 갱신 (M0 PR-0.1)`

### Phase A~G 체계 (deprecated)

구 `PROGRESS.md`의 Phase A~G 분류는 **2026-04-12부터 deprecated** 입니다. 신규 커밋·PR·이슈 제목에 `Phase A`, `Phase B1` 같은 접두사/표현을 사용하지 마세요. Wave 체계와의 매핑은 `STATUS 문서(제거됨)`의 "Wave ↔ 구 Phase 매핑" 표를 참조합니다.

### PR 규칙

- 관련 문서(인벤토리 / ADR / 스코프)를 업데이트하거나 "영향 없음"을 명시
- CI 통과 필수
- ADR 경로: `docs/governance/adr/` (→ `docs/governance/adr/0000-template.md` 템플릿 참조)
