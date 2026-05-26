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

이는 기여한 코드의 라이선스 호환성을 확인하는 절차다. 자세한 내용은 [DCO](DCO) 파일을 참조한다.

## 코딩 규칙

### Python (Backend)

- **포매터/린터**: ruff 0.15.0
- **타입체크**: ty 0.0.15
- **테스트**: pytest
- **패키지 관리**: uv workspace

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

Conventional Commits를 따른다: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

### 테스트

테스트 없는 기능은 받아들이지 않는다. PR에는 관련 단위 테스트 추가/수정 및 테스트 통과 확인이 필수다.

## Pull Request 가이드

1. PR 제목은 변경 내용을 명확히 설명한다
2. PR 본문에 무엇을, 왜 변경했는지 기술한다
3. 관련 Issue가 있으면 링크한다
4. 모든 CI 체크를 통과해야 한다

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

All commits must include a Signed-off-by line. See the [DCO](DCO) file for details.

### Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
