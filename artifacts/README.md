# artifacts/

Commercial Grade v2 — 3-Tier 증거 저장소.

## 구조

- `_meta/` — 증거 메타 JSON (`<sha256>.json`) + `index.jsonl` (SoT)
- `T1/<gate>/<module>/` — 로컬 실행 로그 (90일 수명)
- `T2/<gate>/<module>/` — CI workflow run 참조 (180일 수명)
- `T3/<gate>/<module>/` — staging 실행 로그 + 승인 서명 (영구)
- `playwright/<module>/` — trace·screenshot·report (대형 바이너리는 .gitignore)
- `coverage/<module>-{unit,integration}.xml` — pytest coverage
- `mutation/<module>.json` — mutmut score
- `schemathesis/<module>-<ts>.log` — OpenAPI fuzz
- `k6/<module>-<ts>.{csv,json}` — 부하 테스트 실측
- `chaos/<module>-<ts>.log` — 카오스 드릴 실행 로그
- `drills/G4-{3,4,5}/<module>-<ts>.log` — 백업·롤백·On-call
- `slo/<module>-30d.json` — Prometheus 30일 번다운
- `secrets/<module>-rotation-<ts>.log` — ESO rotation
- `dep-audit/<module>-<ts>.log` — pip-audit / pnpm audit
- `uat/<module>-<run_id>.log` — G5-3 UAT 실행 결과
- `perf-regression/<module>/` — 30일 회귀 로그

## 규약

- `_meta/` 는 항상 git-tracked (증거 무결성 체인)
- T1/T2/T3 텍스트 로그는 git-tracked (.gitignore 예외 규칙)
- 큰 바이너리 (trace.zip, PNG, HTML report) 는 .gitignore — 필요 시 LFS 또는 외부 storage
- **수정·삭제 금지** (append-only)
- 위조 방지: `scripts/engine/replay.py --sha <sha>` 로 해시 재검증 가능

## 참조

- 증거 모델: `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md` §6
- 기록자: `scripts/engine/artifact_writer.record_execution()`
- 재검증: `scripts/engine/replay.py`
