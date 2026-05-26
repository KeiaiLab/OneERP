# OneERP 오픈소스 전환 실행 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OneERP를 AGPL v3 Full OSS로 GitHub에 공개하기 위한 저장소 정리, 법적 파일 추가, 커뮤니티 인프라 구축, 개발자 경험 정비를 완료한다.

**Architecture:** 현재 GitLab private 저장소(`keiailab/services/apps-onerp`)에서 민감 파일을 분리하고, Fresh Start 커밋으로 GitHub 공개 저장소를 생성한다. 내부 인프라(deploy/secrets, .planning/strategy, .planning/program)는 별도 private repo로 이동하고, 공개 코드에서 참조하는 내부 주소는 환경변수로 치환한다.

**Tech Stack:** Python 3.14 (uv), Node.js 22 (pnpm), FastAPI, Next.js 16, Docker Compose, FerretDB, GitHub (공개), GitLab (내부 보존)

**Spec:** `docs/superpowers/specs/2026-05-26-oneerp-open-source-strategy-design.md`

---

## Phase 1: 시크릿 감사 및 민감 분리 (Week 1-2)

### Task 1: 시크릿 스캔 도구 설치 및 전체 스캔

**Files:**
- Create: `scripts/oss/scan-secrets.sh`
- Read: 전체 저장소

- [ ] **Step 1: gitleaks 설치 확인**

```bash
brew install gitleaks || echo "이미 설치됨"
gitleaks version
```

Expected: gitleaks 버전 출력

- [ ] **Step 2: 전체 소스 시크릿 스캔 스크립트 작성**

`scripts/oss/scan-secrets.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="artifacts/secrets"
mkdir -p "$REPORT_DIR"

echo "=== gitleaks: 현재 소스 스캔 ==="
gitleaks dir . \
  --report-path "$REPORT_DIR/gitleaks-source-$(date +%Y%m%d).json" \
  --report-format json \
  --verbose \
  --exit-code 0

echo ""
echo "=== 하드코딩 내부 주소 grep ==="
grep -rn \
  --include='*.py' --include='*.yaml' --include='*.yml' \
  --include='*.toml' --include='*.json' --include='*.ts' --include='*.tsx' \
  'keiailab\.com\|116\.37\.\|bastion' . \
  | grep -v '.git/' \
  | grep -v 'node_modules/' \
  | tee "$REPORT_DIR/internal-refs-$(date +%Y%m%d).txt" || true

echo ""
echo "=== API 키/패스워드 패턴 grep ==="
grep -rn \
  --include='*.py' --include='*.yaml' --include='*.yml' \
  --include='*.toml' --include='*.json' \
  'password\s*=\s*["\x27][^$]\|api_key\s*=\s*["\x27][^$]\|secret\s*=\s*["\x27][^$]' . \
  | grep -v '.git/' \
  | grep -v 'node_modules/' \
  | grep -v '.env.example' \
  | grep -v 'test' \
  | tee "$REPORT_DIR/hardcoded-secrets-$(date +%Y%m%d).txt" || true

echo ""
echo "결과: $REPORT_DIR/"
ls -la "$REPORT_DIR/"
```

- [ ] **Step 3: 스캔 실행**

```bash
chmod +x scripts/oss/scan-secrets.sh
./scripts/oss/scan-secrets.sh
```

Expected: `artifacts/secrets/` 에 3개 리포트 파일 생성. 발견된 시크릿/내부 주소 목록 확인.

- [ ] **Step 4: 결과 분석 및 수정 대상 목록 작성**

스캔 결과를 검토하여 실제 시크릿과 false positive를 구분한다. 이미 확인된 주요 파일:

| 파일 | 내용 | 조치 |
|---|---|---|
| `deploy/charts/*/values-prod.yaml` | 내부 도메인 참조 | 환경변수 치환 또는 제거 |
| `deploy/infra/external-secrets.yaml` | 인프라 설정 | 비공개 분리 |
| `deploy/infra/ray-cluster.yaml` | 내부 도메인 | 비공개 분리 |
| `deploy/catalog/planes.yaml` | 내부 도메인 참조 가능 | 확인 후 치환 |
| `deploy/catalog/services.yaml` | 내부 도메인 참조 가능 | 확인 후 치환 |
| `docker-compose.yml` | 로컬 개발용(안전) | 유지 |
| `HANDOFF.md` | 내부 주소 포함 가능 | 검토 후 정리 |

- [ ] **Step 5: 커밋**

```bash
git add scripts/oss/scan-secrets.sh
git commit -m "chore: 오픈소스 전환용 시크릿 스캔 스크립트 추가"
```

---

### Task 2: 민감 파일 분리 — deploy/secrets

**Files:**
- Modify: `.gitignore`
- Remove (from public): `deploy/secrets/` (47개 서비스별 ExternalSecret 정의)

- [ ] **Step 1: deploy/secrets 내용 백업 확인**

```bash
ls deploy/secrets/ | wc -l
find deploy/secrets/ -name '*.yaml' | wc -l
```

Expected: ~47 디렉토리, 각각 ExternalSecret yaml 파일 보유

- [ ] **Step 2: .gitignore에 deploy/secrets 추가**

`.gitignore` 파일 끝에 추가:

```gitignore
# 오픈소스 공개 제외 — 시크릿 정의 (ExternalSecret)
deploy/secrets/
```

- [ ] **Step 3: deploy/secrets에 placeholder README 추가**

`deploy/secrets/README.md`:

```markdown
# deploy/secrets/

이 디렉토리는 Kubernetes ExternalSecret 정의를 보관한다.
시크릿 키 이름과 인프라 경로가 포함되어 있어 공개 저장소에서 제외한다.

온프레미스 설치 시 시크릿 설정은 [설치 가이드](../../docs/getting-started.md#시크릿-설정)를 참조한다.
```

- [ ] **Step 4: git rm --cached로 추적 제거 (파일은 로컬 보존)**

```bash
git rm -r --cached deploy/secrets/
git add .gitignore deploy/secrets/README.md
```

- [ ] **Step 5: 커밋**

```bash
git commit -m "chore: deploy/secrets를 공개 저장소에서 제외

ExternalSecret 정의에 시크릿 키 이름과 인프라 경로가 포함되어 있어
.gitignore로 제외한다. 온프레미스 설치 가이드는 별도 제공."
```

---

### Task 3: 민감 파일 분리 — .planning/strategy, .planning/program

**Files:**
- Modify: `.gitignore`
- Remove (from public): `.planning/strategy/`, `.planning/program/`
- Keep: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/README.md`

- [ ] **Step 1: .gitignore에 추가**

`.gitignore` 파일에 추가:

```gitignore
# 오픈소스 공개 제외 — 내부 전략/PMO
.planning/strategy/
.planning/program/
.planning/seeds/
.planning/notes/
.planning/phases/
```

- [ ] **Step 2: 공개 유지 파일 확인**

```bash
ls .planning/PROJECT.md .planning/ROADMAP.md .planning/REQUIREMENTS.md .planning/STATE.md .planning/README.md 2>/dev/null
```

Expected: 공개 유지 대상 파일 존재 확인

- [ ] **Step 3: git rm --cached로 추적 제거**

```bash
git rm -r --cached .planning/strategy/ .planning/program/ .planning/seeds/ .planning/notes/ .planning/phases/ 2>/dev/null || true
git add .gitignore
```

- [ ] **Step 4: .planning/README.md 수정 — 비공개 섹션 안내 추가**

`.planning/README.md` 상단에 추가:

```markdown
> **참고**: `strategy/`와 `program/` 디렉토리는 내부 전략 문서로 공개 저장소에서 제외된다.
> 공개 로드맵은 [ROADMAP.md](./ROADMAP.md)를 참조한다.
```

- [ ] **Step 5: 커밋**

```bash
git add .planning/README.md
git commit -m "chore: .planning/strategy,program을 공개 저장소에서 제외

내부 제품 전략과 PMO 문서는 비공개로 유지한다.
공개 로드맵은 .planning/ROADMAP.md에서 제공."
```

---

### Task 4: 민감 파일 분리 — artifacts/T3, .github/workflows, 기타

**Files:**
- Modify: `.gitignore`
- Remove (from public): `artifacts/T3/`, `.github/workflows/`

- [ ] **Step 1: .gitignore에 추가**

```gitignore
# 오픈소스 공개 제외 — 승인 서명 증거
artifacts/T3/

# 레거시 GH Actions (공개 저장소에서는 새로 작성)
.github/workflows/

# 내부 작업 문서
HANDOFF.md
.remember/
```

- [ ] **Step 2: git rm --cached**

```bash
git rm -r --cached artifacts/T3/ 2>/dev/null || true
git rm -r --cached .github/workflows/ 2>/dev/null || true
git rm --cached HANDOFF.md 2>/dev/null || true
git rm -r --cached .remember/ 2>/dev/null || true
git add .gitignore
```

- [ ] **Step 3: 커밋**

```bash
git commit -m "chore: artifacts/T3, .github/workflows, HANDOFF.md를 공개 저장소에서 제외

T3 승인 서명 증거는 비공개. 기존 GH Actions는 레거시이며
공개 저장소용 CI는 별도 작성 (ADR-0019)."
```

---

### Task 5: 하드코딩된 내부 주소 치환

**Files:**
- Modify: `deploy/charts/*/values-prod.yaml` (비공개 처리)
- Modify: `deploy/catalog/planes.yaml`, `deploy/catalog/services.yaml` (내부 도메인 치환)

- [ ] **Step 1: 현재 내부 주소 참조 파일 확인**

```bash
grep -rn 'keiailab\.com\|116\.37\.' \
  --include='*.py' --include='*.yaml' --include='*.yml' \
  --include='*.toml' --include='*.json' \
  . | grep -v '.git/' | grep -v 'node_modules/' | grep -v deploy/secrets/
```

- [ ] **Step 2: deploy/charts/*/values-prod.yaml 비공개 처리**

prod values에는 내부 인프라 주소가 포함되므로 `.gitignore`에 추가:

```gitignore
# prod values — 인프라 주소 포함
deploy/charts/*/values-prod.yaml
```

```bash
find deploy/charts/ -name 'values-prod.yaml' -exec git rm --cached {} \;
git add .gitignore
```

- [ ] **Step 3: deploy/catalog에서 내부 참조 확인 및 치환**

```bash
grep -n 'keiailab\.com\|116\.37\.' deploy/catalog/planes.yaml deploy/catalog/services.yaml
```

이미지 레지스트리 참조가 있다면 환경변수로 치환:
- `registry.keiailab.com/oneerp/` → `${ONEERP_REGISTRY:-ghcr.io/oneerp}/`

또는 docker-compose.yml이 생성 파일이므로 생성 스크립트(`scripts/deploy/catalog.py`)에서 치환.

- [ ] **Step 4: deploy/infra 비공개 처리**

`deploy/infra/`에 내부 클러스터 설정이 포함되어 있으므로:

```gitignore
# 내부 인프라 설정
deploy/infra/
```

```bash
git rm -r --cached deploy/infra/ 2>/dev/null || true
git add .gitignore
```

- [ ] **Step 5: 최종 확인 및 커밋**

```bash
grep -rn 'keiailab\.com\|116\.37\.' \
  --include='*.py' --include='*.yaml' --include='*.yml' \
  --include='*.toml' --include='*.json' \
  . | grep -v '.git/' | grep -v 'node_modules/' | wc -l
```

Expected: 0 (모든 내부 주소가 .gitignore 처리 또는 치환됨)

```bash
git add -A
git commit -m "chore: 하드코딩된 내부 주소를 환경변수로 치환/비공개 처리

deploy/charts/*/values-prod.yaml, deploy/infra/ 비공개.
deploy/catalog 내 레지스트리 참조 변수화."
```

---

### Task 6: 서드파티 라이선스 감사

**Files:**
- Create: `scripts/oss/audit-licenses.sh`

- [ ] **Step 1: 라이선스 감사 스크립트 작성**

`scripts/oss/audit-licenses.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="artifacts/dep-audit"
mkdir -p "$REPORT_DIR"

echo "=== Python 라이선스 ==="
uv run pip-licenses --format=csv --with-urls \
  --output-file="$REPORT_DIR/python-licenses.csv" 2>/dev/null || \
  echo "⚠️ pip-licenses 실행 실패 — 수동 확인 필요"

echo "=== Node.js 라이선스 ==="
if [ -d "apps/web" ]; then
  cd apps/web
  npx license-checker --csv --out "../../$REPORT_DIR/node-licenses.csv" 2>/dev/null || \
    echo "⚠️ license-checker 실행 실패 — 수동 확인 필요"
  cd ../..
fi

echo "=== AGPL 비호환 검사 ==="
if ls "$REPORT_DIR"/*.csv 1>/dev/null 2>&1; then
  grep -i 'CPAL\|Sleepycat\|QPL\|RPSL\|SSPL' "$REPORT_DIR"/*.csv 2>/dev/null && \
    echo "⚠️ 비호환 라이선스 발견!" || \
    echo "✅ AGPL 비호환 라이선스 없음"
else
  echo "⚠️ 라이선스 CSV 미생성 — 수동 확인 필요"
fi
```

- [ ] **Step 2: 실행**

```bash
chmod +x scripts/oss/audit-licenses.sh
./scripts/oss/audit-licenses.sh
```

Expected: AGPL 비호환 라이선스 없음

- [ ] **Step 3: 커밋**

```bash
git add scripts/oss/audit-licenses.sh
git commit -m "chore: 서드파티 라이선스 감사 스크립트 추가"
```

---

## Phase 2: 법적 파일 및 공개 저장소 준비 (Week 2-3)

### Task 7: LICENSE 파일 추가 (AGPL v3)

**Files:**
- Create: `LICENSE`

- [ ] **Step 1: AGPL v3 전문 다운로드**

```bash
curl -sL https://www.gnu.org/licenses/agpl-3.0.txt -o LICENSE
```

- [ ] **Step 2: 파일 확인**

```bash
head -5 LICENSE
```

Expected: `GNU AFFERO GENERAL PUBLIC LICENSE` 헤더

- [ ] **Step 3: 커밋**

```bash
git add LICENSE
git commit -m "chore: AGPL-3.0 라이선스 파일 추가"
```

---

### Task 8: NOTICE 및 DCO 파일 추가

**Files:**
- Create: `NOTICE`
- Create: `DCO`

- [ ] **Step 1: NOTICE 파일 작성**

`NOTICE`:

```
OneERP
Copyright 2024-2026 Keiailab Co., Ltd.

This product is licensed under the GNU Affero General Public License v3.0.
See the LICENSE file for the full license text.

This product includes software developed by third parties.
See the dependency license reports in artifacts/dep-audit/ for details.

---

Third-party components and their licenses:

FastAPI — MIT License
  Copyright (c) 2018 Sebastián Ramírez

Pydantic — MIT License
  Copyright (c) 2017 Samuel Colvin

Next.js — MIT License
  Copyright (c) 2024 Vercel, Inc.

Tailwind CSS — MIT License
  Copyright (c) Tailwind Labs, Inc.

FerretDB — Apache License 2.0
  Copyright (c) 2021 FerretDB Inc.

For the complete list of dependencies and their licenses,
run: ./scripts/oss/audit-licenses.sh
```

- [ ] **Step 2: DCO 파일 작성**

`DCO`:

```
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

- [ ] **Step 3: 커밋**

```bash
git add NOTICE DCO
git commit -m "chore: NOTICE(저작권) 및 DCO(기여 합의) 파일 추가"
```

---

### Task 9: CONTRIBUTING.md 작성

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: CONTRIBUTING.md 작성**

`CONTRIBUTING.md`:

```markdown
# Contributing to OneERP

OneERP에 기여해 주셔서 감사합니다! 이 문서는 기여 방법을 안내합니다.

*[English version below](#contributing-english)*

---

## 시작하기

1. 저장소를 Fork한다
2. 로컬 개발 환경을 셋업한다 — [Getting Started](docs/getting-started.md)
3. Feature 브랜치를 생성한다: `git checkout -b feat/my-feature`
4. 변경사항을 작성하고 테스트한다
5. DCO sign-off와 함께 커밋한다: `git commit -s -m "feat: 기능 설명"`
6. Pull Request를 생성한다

## DCO (Developer Certificate of Origin)

모든 커밋에 Signed-off-by 라인이 필요하다:

```bash
git commit -s -m "feat: 기여 내용"
```

이는 기여한 코드의 라이선스 호환성을 확인하는 절차다.
자세한 내용은 [DCO](DCO) 파일을 참조한다.

## 코딩 규칙

### Python (Backend)

- **포매터/린터**: ruff 0.15.0
- **타입체크**: ty 0.0.15
- **테스트**: pytest
- **패키지 관리**: uv workspace
- **규칙**: `from __future__ import annotations` 필수, `print()` 금지

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check .
uv run pytest -m "not integration and not e2e" services/ packages/
```

### TypeScript (Frontend)

- **프레임워크**: Next.js 16 (App Router)
- **스타일**: Tailwind CSS 4
- **린터/포매터**: Biome 2
- **패키지 관리**: pnpm 10

```bash
pnpm --filter @oneerp/web lint
pnpm --filter @oneerp/web typecheck
pnpm --filter @oneerp/web build
```

### 커밋 메시지

Conventional Commits를 따른다:

- `feat:` — 새 기능
- `fix:` — 버그 수정
- `docs:` — 문서 변경
- `refactor:` — 리팩토링
- `test:` — 테스트 추가/수정
- `chore:` — 빌드, 설정 등

### 테스트

테스트 없는 기능은 받아들이지 않는다. PR에는 반드시:
- 관련 단위 테스트 추가/수정
- 테스트 통과 로그 첨부

## Pull Request 가이드

1. PR 제목은 변경 내용을 명확히 설명한다
2. PR 본문에 무엇을, 왜 변경했는지 기술한다
3. 관련 Issue가 있으면 링크한다
4. 모든 CI 체크를 통과해야 한다

## 이슈 리포트

- **버그**: Issue 템플릿의 Bug Report를 사용한다
- **기능 요청**: Feature Request 템플릿을 사용한다
- **모듈 요청**: Module Request 템플릿을 사용한다

## 거버넌스

프로젝트 거버넌스 구조는 [GOVERNANCE.md](GOVERNANCE.md)를 참조한다.

## 보안

보안 취약점은 공개 이슈로 보고하지 않는다. [SECURITY.md](SECURITY.md)의 절차를 따른다.

---

<a id="contributing-english"></a>

## Contributing (English)

Thank you for your interest in contributing to OneERP!

### Quick Start

1. Fork the repository
2. Set up your local dev environment — [Getting Started](docs/getting-started.md)
3. Create a feature branch: `git checkout -b feat/my-feature`
4. Make changes and write tests
5. Commit with DCO sign-off: `git commit -s -m "feat: description"`
6. Open a Pull Request

### DCO Requirement

All commits must include a Signed-off-by line:

```bash
git commit -s -m "feat: your contribution"
```

See the [DCO](DCO) file for details.

### Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Please be respectful and inclusive.
```

- [ ] **Step 2: 커밋**

```bash
git add CONTRIBUTING.md
git commit -m "docs: 기여 가이드(CONTRIBUTING.md) 추가"
```

---

### Task 10: CODE_OF_CONDUCT.md, SECURITY.md, GOVERNANCE.md 작성

**Files:**
- Create: `CODE_OF_CONDUCT.md`
- Create: `SECURITY.md`
- Create: `GOVERNANCE.md`

- [ ] **Step 1: CODE_OF_CONDUCT.md 작성**

Contributor Covenant v2.1 다운로드 후 연락처 수정:

```bash
curl -sL https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md -o CODE_OF_CONDUCT.md
```

파일 하단 `[INSERT CONTACT METHOD]` → `opensource@keiailab.com` 으로 수정.

- [ ] **Step 2: SECURITY.md 작성**

`SECURITY.md`:

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a Vulnerability

**보안 취약점은 공개 이슈로 보고하지 마세요.**

다음 방법 중 하나로 비공개 보고해 주세요:

1. **GitHub Security Advisory**: [Report a vulnerability](../../security/advisories/new) (권장)
2. **이메일**: security@keiailab.com

### 보고 시 포함할 정보

- 취약점 유형 (예: XSS, SQL injection, 인증 우회)
- 재현 단계
- 영향 범위
- 가능하면 PoC 코드

### 대응 절차

1. 24시간 내 접수 확인
2. 72시간 내 영향도 평가 및 대응 계획 공유
3. 수정 패치 준비 후 coordinated disclosure
4. 보고자에게 Credit 제공 (동의 시)

## 보안 업데이트

보안 업데이트는 [Releases](../../releases)에서 확인할 수 있다.
중요 보안 패치는 GitHub Security Advisory를 통해 통보한다.
```

- [ ] **Step 3: GOVERNANCE.md 작성**

`GOVERNANCE.md`:

```markdown
# OneERP Governance

## 거버넌스 모델

OneERP는 초기 단계에서 BDFL(Benevolent Dictator For Life) 모델을 채택한다.
커뮤니티 규모가 성장하면 Steering Committee 모델로 전환할 계획이다.

## 역할

### Maintainer

- 책임: 프로젝트 방향 결정, 코드 리뷰, 릴리즈 관리
- 권한: 모든 저장소에 대한 merge/release 권한
- 대상: 케이아이랩 핵심 팀

### Committer

- 책임: 특정 모듈의 코드 리뷰 및 merge
- 권한: 담당 모듈에 대한 merge 권한
- 조건: 3개 이상의 merged PR + Maintainer 추천
- 승격 절차: Maintainer 과반 동의

### Contributor

- 모든 외부 기여자
- PR 제출, Issue 생성, Discussion 참여 가능
- DCO sign-off 필수

## 의사결정 프로세스

1. **일상적 결정**: Maintainer가 PR 리뷰로 결정
2. **아키텍처 결정**: ADR(Architecture Decision Record) 작성 → Maintainer 합의
3. **방향 결정**: GitHub Discussion에서 RFC → Maintainer 투표

## ADR (Architecture Decision Record)

아키텍처 결정은 `docs/governance/adr/` 에 ADR로 기록한다.
기존 ADR 목록은 해당 디렉토리에서 확인할 수 있다.

## 행동 강령

모든 참여자는 [Code of Conduct](CODE_OF_CONDUCT.md)를 준수한다.
```

- [ ] **Step 4: 커밋**

```bash
git add CODE_OF_CONDUCT.md SECURITY.md GOVERNANCE.md
git commit -m "docs: CODE_OF_CONDUCT, SECURITY, GOVERNANCE 문서 추가"
```

---

### Task 11: GitHub Issue/PR 템플릿 작성

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug-report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature-request.yml`
- Create: `.github/ISSUE_TEMPLATE/module-request.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **Step 1: 디렉토리 생성**

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

- [ ] **Step 2: Bug Report 템플릿 작성**

`.github/ISSUE_TEMPLATE/bug-report.yml`:

```yaml
name: Bug Report
description: 버그를 신고합니다
title: "[Bug] "
labels: ["bug"]
body:
  - type: textarea
    id: description
    attributes:
      label: 버그 설명
      description: 무엇이 잘못되었나요?
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: 재현 단계
      value: |
        1.
        2.
        3.
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: 기대 동작
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: 실제 동작
    validations:
      required: true
  - type: input
    id: version
    attributes:
      label: OneERP 버전
      placeholder: v0.1.0
  - type: dropdown
    id: module
    attributes:
      label: 관련 모듈
      options:
        - core
        - web (프론트엔드)
        - finance (회계)
        - hr (인사)
        - sales (판매)
        - scm (공급망)
        - logistics (물류)
        - portal (포털)
        - 기타
```

- [ ] **Step 3: Feature Request 템플릿 작성**

`.github/ISSUE_TEMPLATE/feature-request.yml`:

```yaml
name: Feature Request
description: 새 기능을 제안합니다
title: "[Feature] "
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: 해결하려는 문제
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: 제안하는 해결 방법
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: 고려한 대안
  - type: dropdown
    id: module
    attributes:
      label: 관련 모듈
      options:
        - core
        - web (프론트엔드)
        - finance (회계)
        - hr (인사)
        - sales (판매)
        - 신규 모듈
        - 기타
```

- [ ] **Step 4: Module Request 템플릿 작성**

`.github/ISSUE_TEMPLATE/module-request.yml`:

```yaml
name: Module Request
description: 새 ERP 모듈을 제안합니다
title: "[Module] "
labels: ["module-request"]
body:
  - type: textarea
    id: description
    attributes:
      label: 모듈 설명
      description: 어떤 비즈니스 영역을 다루나요?
    validations:
      required: true
  - type: textarea
    id: use-cases
    attributes:
      label: 주요 사용 사례
      value: |
        1.
        2.
        3.
    validations:
      required: true
  - type: textarea
    id: reference
    attributes:
      label: 참고 자료
      description: ERPNext, Odoo 등 기존 ERP에서의 유사 기능
```

- [ ] **Step 5: PR 템플릿 작성**

`.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## 변경 내용

<!-- 무엇을, 왜 변경했는지 설명 -->

## 변경 유형

- [ ] 버그 수정
- [ ] 새 기능
- [ ] 리팩토링
- [ ] 문서
- [ ] 테스트

## 관련 이슈

<!-- closes #이슈번호 -->

## 체크리스트

- [ ] 테스트 추가/수정 완료
- [ ] 테스트 통과 확인
- [ ] 린트/타입체크 통과
- [ ] DCO sign-off 포함 (`git commit -s`)
- [ ] 문서 업데이트 (해당 시)
```

- [ ] **Step 6: 커밋**

```bash
git add .github/ISSUE_TEMPLATE/ .github/PULL_REQUEST_TEMPLATE.md
git commit -m "docs: GitHub Issue/PR 템플릿 추가"
```

---

### Task 12: README.md 오픈소스 프로젝트용 보강

**Files:**
- Modify: `README.md`

- [ ] **Step 1: README.md 상단에 OSS 헤더 추가**

현재 README.md의 `# OneERP` 줄을 다음으로 교체:

```markdown
<div align="center">

# OneERP

**ERPNext 기능 동등성을 목표로 하는 오픈소스 ERP**

한국 비즈니스 환경에 최적화된 통합 비즈니스 앱

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![CI](https://github.com/oneerp/oneerp/actions/workflows/ci.yml/badge.svg)](https://github.com/oneerp/oneerp/actions/workflows/ci.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[시작하기](docs/getting-started.md) · [문서](docs/) · [기여하기](CONTRIBUTING.md) · [로드맵](ROADMAP.md)

</div>
```

- [ ] **Step 2: README.md 하단에 기여/라이선스 섹션 추가**

파일 끝에 추가:

```markdown
---

## 🤝 기여하기

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 참조해 주세요.

## 📄 라이선스

이 프로젝트는 [AGPL-3.0](LICENSE) 라이선스 하에 배포됩니다.

Copyright 2024-2026 [Keiailab Co., Ltd.](https://keiailab.com)
```

- [ ] **Step 3: 커밋**

```bash
git add README.md
git commit -m "docs: README.md를 오픈소스 프로젝트용으로 보강"
```

---

## Phase 3: 개발자 경험 (Week 3-4)

### Task 13: docs/getting-started.md 작성

**Files:**
- Create: `docs/getting-started.md`

- [ ] **Step 1: getting-started.md 작성**

`docs/getting-started.md`:

```markdown
# Getting Started

OneERP 로컬 개발 환경 셋업 가이드.

## 요구 환경

| 도구 | 버전 | 설치 |
|------|------|------|
| Docker + Compose | 24+ / v2.20+ | [Docker Desktop](https://docker.com/products/docker-desktop/) |
| uv | 0.11.1+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Python | 3.14 | `uv python install 3.14` |
| Node.js | 22.x | `nvm install 22` |
| pnpm | 10.30.3 | `corepack enable && corepack prepare pnpm@10.30.3 --activate` |
| git | 2.40+ | — |

## 빠른 시작 (10분)

### 1. 저장소 클론

```bash
git clone https://github.com/oneerp/oneerp.git
cd oneerp
git submodule update --init --recursive
```

### 2. 의존성 설치

```bash
uv sync           # Python (backend)
pnpm install      # Node.js (frontend)
```

### 3. 환경변수 설정

```bash
cp .env.example .env
```

로컬 개발에는 기본값으로 충분하다.

### 4. 인프라 시작

```bash
docker compose up -d
```

PostgreSQL, FerretDB, Valkey(Redis), NATS가 시작된다.

### 5. Backend 실행

```bash
./scripts/dev/compose-up.sh
```

또는 개별 서비스:

```bash
uv run --package oneerp-gateway --directory services/gateway uvicorn app.main:app --port 8000
```

### 6. Frontend 실행

```bash
pnpm --filter @oneerp/web dev
```

브라우저에서 http://localhost:3000 접속.

## 시크릿 설정

로컬 개발에는 `.env.example`의 기본값으로 충분하다.
프로덕션 배포 시에는 각 서비스별 시크릿을 별도 설정해야 한다.

## 테스트 실행

```bash
# 단위 테스트 (backend)
uv run pytest -m "not integration and not e2e" services/ packages/

# 린트 + 타입체크 (backend)
uv run ruff format --check .
uv run ruff check .
uv run ty check .

# 프론트엔드
pnpm --filter @oneerp/web lint
pnpm --filter @oneerp/web typecheck
```

## 아키텍처 개요

OneERP는 6개 Runtime Plane으로 구성된다:

| Plane | 역할 |
|-------|------|
| API Plane | ERP 동기 CRUD (21 도메인 mount) |
| Realtime Plane | WebSocket/Presence |
| Worker Plane | 이벤트 컨슈머 |
| Scheduler Plane | Cron/Batch |
| Edge Plane | Gateway/Auth (외부 진입점) |
| Extension Plane | 외부 커넥터 |

자세한 아키텍처는 [docs/ARCHITECTURE-MAP.md](ARCHITECTURE-MAP.md)를 참조한다.

## 다음 단계

- [기여 가이드](../CONTRIBUTING.md)
- [API 문서](api/)
- [모듈 추가 가이드](developer/)
```

- [ ] **Step 2: 커밋**

```bash
git add docs/getting-started.md
git commit -m "docs: Getting Started 개발 환경 셋업 가이드 추가"
```

---

### Task 14: ADR-0019 — GitHub Actions 예외 문서화

**Files:**
- Create: `docs/governance/adr/0019-oss-github-actions-exception.md`

- [ ] **Step 1: ADR 작성**

`docs/governance/adr/0019-oss-github-actions-exception.md`:

```markdown
# ADR-0019: 공개 OSS 저장소 GitHub Actions 예외

- **상태**: Accepted
- **일자**: 2026-05-26
- **결정자**: phil

## Context

글로벌 거버넌스 §2(RFC 0002)는 GitHub Actions 영구 금지를 선언했다.
근거는 2026-04-28 organization billing SPOF 사고(I-2026-04-28)이다.

OneERP를 GitHub에 공개 OSS로 전환하면서, 외부 기여자의 PR에 대한
자동 CI 실행이 필수적이다. 공개 OSS 저장소의 GitHub Actions는:

1. 무료 tier 사용 (billing 독립)
2. 외부 기여자가 접근 가능한 유일한 CI 환경
3. 원래 사고 원인(organization billing SPOF)과 무관

## Decision

**공개 OSS 저장소(`oneerp/oneerp`)에 한하여 GitHub Actions 사용을 허용한다.**

조건:
- 공개 저장소에서만 적용 (내부 GitLab 저장소는 §2 그대로 적용)
- self-hosted runner 금지 (무료 GitHub-hosted runner만 사용)
- 워크플로우는 lint/typecheck/test 게이트만 (배포 워크플로우 금지)

## Consequences

- 외부 기여자의 PR이 자동으로 품질 게이트를 통과하는지 확인 가능
- billing 리스크 없음 (공개 저장소 무료 tier)
- 내부 개발 프로세스의 §2 원칙은 유지
```

- [ ] **Step 2: 커밋**

```bash
git add docs/governance/adr/0019-oss-github-actions-exception.md
git commit -m "docs: ADR-0019 공개 OSS 저장소 GitHub Actions 예외"
```

---

### Task 15: GitHub Actions CI 워크플로우 (공개 저장소용)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: CI 워크플로우 작성**

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  backend-lint:
    name: BE Lint & Typecheck
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - uses: astral-sh/setup-uv@v6
        with:
          version: "0.11.1"

      - run: uv python install 3.14
      - run: uv sync

      - name: ruff format
        run: uv run ruff format --check .

      - name: ruff check
        run: uv run ruff check .

      - name: ty check
        run: uv run ty check .

  backend-test:
    name: BE Unit Tests
    runs-on: ubuntu-latest
    needs: backend-lint
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - uses: astral-sh/setup-uv@v6
        with:
          version: "0.11.1"

      - run: uv python install 3.14
      - run: uv sync

      - name: pytest
        run: uv run pytest -m "not integration and not e2e" services/ packages/ --tb=short -q

  frontend-lint:
    name: FE Lint & Typecheck
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - uses: actions/setup-node@v4
        with:
          node-version: "22"

      - uses: pnpm/action-setup@v4
        with:
          version: "10.30.3"

      - run: pnpm install --frozen-lockfile

      - name: lint
        run: pnpm --filter @oneerp/web lint

      - name: typecheck
        run: pnpm --filter @oneerp/web typecheck
```

- [ ] **Step 2: 커밋**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: 공개 OSS 저장소용 GitHub Actions CI 추가 (ADR-0019)"
```

---

### Task 16: ROADMAP.md 공개 버전 작성

**Files:**
- Create: `ROADMAP.md` (루트)

- [ ] **Step 1: ROADMAP.md 작성**

`ROADMAP.md`:

```markdown
# OneERP Roadmap

> 이 로드맵은 커뮤니티와 공유하는 공개 계획이다.

## 현재 단계: Alpha (v0.1.x)

핵심 도메인의 기본 CRUD와 아키텍처 안정화에 집중한다.

### 활성 작업

- [ ] 6 Runtime Plane 안정화
- [ ] 핵심 도메인 (회계, HR, 구매, 판매) CRUD 완성
- [ ] 인증/인가 체계 정비
- [ ] Docker Compose 원클릭 개발 환경

### 다음 마일스톤: Beta (v0.2.x)

- [ ] 한국 세금 계산서 (전자세금계산서 API 연동)
- [ ] 4대보험 자동 계산
- [ ] 멀티테넌시 기본 지원
- [ ] API 문서 자동 생성 (OpenAPI)

### 장기 목표: v1.0

- [ ] ERPNext 핵심 모듈 기능 동등성
- [ ] 프로덕션 배포 가이드
- [ ] SaaS (OneERP Cloud) 런칭
- [ ] 마켓플레이스 (서드파티 모듈)

## 기여 방법

특정 기능에 관심이 있다면:
1. 관련 Issue를 확인하거나 생성한다
2. Discussion에서 설계를 논의한다
3. PR을 제출한다
```

- [ ] **Step 2: 커밋**

```bash
git add ROADMAP.md
git commit -m "docs: 공개 로드맵(ROADMAP.md) 추가"
```

---

## Phase 4: Fresh Start 및 공개 (Week 4-6)

### Task 17: 최종 검증 및 Fresh Start 커밋

이 Task는 Phase 1-3의 모든 변경이 stable 브랜치에 반영된 후 실행한다.

**Files:**
- 전체 저장소 (새 GitHub 저장소에 initial commit)

- [ ] **Step 1: 최종 .gitignore 동작 확인**

```bash
git ls-files | grep -E 'deploy/secrets/|\.planning/strategy/|\.planning/program/|artifacts/T3/|values-prod\.yaml|HANDOFF' || echo "✅ 민감 파일 추적 제거 확인"
```

Expected: 출력 없음 (모든 민감 파일이 추적에서 제거됨)

- [ ] **Step 2: 시크릿 최종 스캔**

```bash
./scripts/oss/scan-secrets.sh
```

Expected: 하드코딩 시크릿 0건, 내부 주소 0건

- [ ] **Step 3: 법적 파일 존재 확인**

```bash
ls LICENSE NOTICE DCO CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md GOVERNANCE.md ROADMAP.md
```

Expected: 모든 파일 존재

- [ ] **Step 4: GitHub organization/repo 생성 (사용자 수동)**

1. https://github.com/organizations/plan 에서 org 생성 (이름 결정 필요)
2. 저장소 생성 (empty, public)
3. Repository settings → Discussions 활성화

- [ ] **Step 5: Fresh Start push**

```bash
EXPORT_DIR=$(mktemp -d)

# .gitignore 가 적용된 상태의 파일만 export
git archive HEAD | tar -x -C "$EXPORT_DIR"

cd "$EXPORT_DIR"
git init
git add -A
git commit -m "feat: OneERP 오픈소스 초기 커밋

ERPNext 기능 동등성을 목표로 하는 오픈소스 ERP.
한국 비즈니스 환경에 최적화된 통합 비즈니스 앱.

AGPL-3.0-or-later 라이선스.

Signed-off-by: Phil Park <eightynine01@gmail.com>"

git remote add origin git@github.com:oneerp/oneerp.git
git branch -M main
git push -u origin main
```

- [ ] **Step 6: 릴리즈 태그**

```bash
git tag -a v0.1.0-alpha -m "v0.1.0-alpha: OneERP 최초 공개 릴리즈

한국 비즈니스 환경에 최적화된 오픈소스 ERP.
ERPNext 기능 동등성을 목표로 한다.

주요 내용:
- 6 Runtime Plane 아키텍처
- 48개 도메인 모듈 (개발 중)
- FastAPI + Next.js 16 스택
- Docker Compose 개발 환경
- AGPL-3.0 라이선스"

git push origin v0.1.0-alpha
```

---

### Task 18: 런칭 준비

**Files:**
- GitHub UI 작업 + 외부 플랫폼

- [ ] **Step 1: GitHub 저장소 설정**

GitHub UI에서:
- About: "Open-source ERP for Korean businesses — ERPNext feature parity"
- Topics: `erp`, `open-source`, `korean`, `fastapi`, `nextjs`, `agpl`, `enterprise`
- Discussions 활성화
- Labels 추가: `good first issue`, `help wanted`, `module-request`, `documentation`, `korean-localization`

- [ ] **Step 2: Good First Issue 10개 이상 생성**

```bash
gh issue create --title "[Good First Issue] 한국어 에러 메시지 번역 — core" --label "good first issue" --body "..."
gh issue create --title "[Good First Issue] 급여명세서 PDF 출력 — hr" --label "good first issue" --body "..."
gh issue create --title "[Good First Issue] 부가세 신고 양식 생성 — finance" --label "good first issue" --body "..."
gh issue create --title "[Good First Issue] 발주서 이메일 발송 — scm" --label "good first issue" --body "..."
gh issue create --title "[Good First Issue] 견적서 PDF 템플릿 — sales" --label "good first issue" --body "..."
gh issue create --title "[Good First Issue] API 문서 개선" --label "good first issue,documentation" --body "..."
gh issue create --title "[Good First Issue] 다크모드 지원 — web" --label "good first issue" --body "..."
gh issue create --title "[Good First Issue] 설정 유효성 검사 개선 — core" --label "good first issue" --body "..."
gh issue create --title "[Good First Issue] 대시보드 위젯 추가 — portal" --label "good first issue" --body "..."
gh issue create --title "[Good First Issue] 재고 이동 내역 조회 — logistics" --label "good first issue" --body "..."
```

- [ ] **Step 3: Discord 서버 생성**

채널 구조:
- #announcements
- #general
- #dev
- #help
- #showcase

- [ ] **Step 4: 런칭 블로그 포스트 작성**

핵심 메시지:
- ERPNext 대안으로서 한국 비즈니스 최적화
- AGPL v3 Full Open Source
- 기술 스택 소개 (Python 3.14, FastAPI, Next.js 16)
- 기여 방법

- [ ] **Step 5: 커뮤니티 공유**

- Hacker News: "Show HN: OneERP — Open-source ERP for Korean businesses"
- Reddit: r/selfhosted, r/opensource
- GeekNews (한국)
- 디스콰이엇
- OKKY, velog

---

## 완료 기준

모든 Task 완료 시:

1. ✅ GitHub 저장소가 public으로 공개됨
2. ✅ AGPL v3 LICENSE + NOTICE + DCO 존재
3. ✅ 민감 파일(시크릿, 전략, PMO, prod values) 비공개 분리 완료
4. ✅ 하드코딩된 내부 주소 0건 (공개 코드에서)
5. ✅ CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, GOVERNANCE.md 존재
6. ✅ GitHub Issue/PR 템플릿 존재
7. ✅ CI(GitHub Actions) 워크플로우 작성됨
8. ✅ docs/getting-started.md로 개발 환경 셋업 가능
9. ✅ Good First Issue 10개 이상 생성
10. ✅ v0.1.0-alpha 태그 및 릴리즈
