# OneErp (apps/OneErp)

@~/.claude/CLAUDE.md

> 글로벌 v3.0 거버넌스를 자동 import. 본 레포의 *팀 작업 규칙*은 `AGENTS.md`도 함께 참조.
> OneErp의 ADR/incident KB 패턴은 글로벌 standards/{adr,incident-kb}.md의 *역승격 출처*.

## 스택
- 언어/런타임: Python 3.12 (uv) + Node (pnpm) — **혼합**
- 구조: `core/` (Python backend, submodule), `web/` (Node frontend, submodule)
- 데이터: PostgreSQL/FerretDB, OIDC, S3/MinIO

## 주요 명령
- **품질 게이트**: `./scripts/ci/run.sh` (로컬). CI는 ruff/ty/tests(유닛/통합/E2E)/마이그레이션·스키마 검증
- 개발: 서브모듈별 개별 명령 (`core/`, `web/` 각각의 README 참조)
- 빌드: `docker buildx` 기본 빌더(`default`) 사용 (글로벌 §2)

## 지식 베이스 위치 (OneErp 단일 SoT — 글로벌 표준의 *원형 모델*)
- **ADR**: `docs/governance/adr/` (글로벌 standards/adr.md의 역승격 출처)
- **인프라 인벤토리**: `docs/infra/inventory/`
- **범위/기능 매트릭스**: `docs/product/scope/`
- **운영/CI**: `docs/infra/ops/`
- **UI Design System**: `docs/engineering/ui/`
- **Incident**: `artifacts/verification/session-*/`

## 프로젝트 고유 규칙
- **0단계 필수**: 공유 리소스 인벤토리(`docs/infra/inventory/`) 확인 *없이* 아키텍처 확정·모듈 분해·일정 산출 **금지**
- **ADR 우선**: 설계/스택/경계/권한/테넌시/데이터/CI 결정은 ADR로만 확정. PR에 ADR 없으면 "제안"으로만 취급(머지 보류)
- **브랜치/작업 분리**: worktree 기반 분리 권장 (`.worktrees/`, gitignore)
- **FE 작업**: `web/` 변경 시 `.claude/skills/visual-dual-loop.md` 준수, before/after 스크린샷·콘솔 점검 증거를 `docs/superpowers/visual-log/`에 기록
- **자가수정 (ralph-loop)**: 글로벌 standards/enforcement.md §self-repair 적용. hook 우회는 `LEFTHOOK=0` env 또는 `[skip-hooks]` 트레일러
- **artifacts/ 커밋 금지**: 수집 스크립트 결과는 git ignore 대상

## 개인 override
<!-- CLAUDE.local.md (gitignored)에서 부분 덮어쓰기 가능 -->
