# ⚡ OneERP 15분 시작 가이드

새 기여자가 **15분 안에** 레포를 클론하고 첫 스모크 테스트까지 통과시키는 최단 경로. 상세 설명은 각 단계 아래의 "더 알아보기" 링크로 이어집니다.

---

## 0단계: 사전 요구 사항

버전 실측 체크를 자동 실행합니다:

```fish
./scripts/dev/check-prereqs.sh
```

실패하는 항목이 있으면 상세 가이드 — 사전 요구사항으로 이동하세요.

---

## 1단계: 의존성 설치 (BE + FE, 단일 명령)

```fish
uv sync --all-packages --all-groups && pnpm install
```

---

## 2단계: FerretDB 기동

```fish
docker compose up -d
```

PostgreSQL 17 + DocumentDB 확장 + FerretDB가 함께 뜹니다. 자세한 DB 설정은 환경변수 섹션 참조.

---

## 3단계: 스모크 테스트

```fish
make smoke
```

이 타깃은 `ruff check` → `ty check` → 공통 커널 유닛 테스트 → 매출-매출채권(FL1) 시나리오 1개를 연속 실행합니다. 전부 통과하면 로컬 환경 준비 완료.

---

## 4단계: 서비스 기동 (필요한 것만)

```fish
uv run --package oneerp-gateway --directory services/platform/gateway uvicorn app.main:app --port 8000 --reload
```

포트 맵 전체는 상세 가이드 — 서비스 포트 맵.

---

## 다음 단계 (5개 링크로만 분기)

여기까지 성공했다면 아래 문서들이 핵심입니다:

1. **[📊 프로젝트 현재 상태 (STATUS)](../STATUS.md)** — 활성 Wave · 최근 PR 이력
2. **[🗺️ 모듈 ↔ 서비스 매핑](../product/scope/MODULE-SERVICE-MAP.md)** — 56 모듈이 48 서비스에 어떻게 배치되는지
3. **[🛒 매출-매출채권 튜토리얼 (FL1)](../tutorials/01-order-to-cash.md)** — 실제 E2E 비즈니스 시나리오
4. **[🏛️ 아키텍처 개요](01-architecture-overview.md)** — 모노레포 구조 · DI · 이벤트 체인
5. **[✍️ 코딩 가이드](02-coding-guide.md)** — 한국어 주석·FastAPI 패턴·테스트 우선 원칙

---

## 트러블슈팅

`make smoke` 실패 시 증상별 처방은 상세 가이드 — 문제 해결 또는 STATUS.md 트러블슈팅 섹션을 참고하세요.
