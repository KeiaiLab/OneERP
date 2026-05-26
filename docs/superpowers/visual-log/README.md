# visual-log — 시각 이중 루프 증거 저장소

`visual-dual-loop` 스킬이 남기는 before/after 스크린샷과 NOTES를 보관한다.

## 디렉토리 규약

```
visual-log/
└── <YYYY-MM-DD>/
    └── <topic>/
        ├── before-1.png
        ├── after-1.png
        ├── before-2.png
        ├── after-2.png
        └── NOTES.md
```

## NOTES.md 형식

```markdown
# <topic> — <YYYY-MM-DD>

## 사이클

- 1: <한 줄 메모. 무엇을 왜 바꿨는지>
- 2: ...

## 콘솔/네트워크 샘플

(필요 시 인용)
```

## 수명

90일 경과한 날짜 디렉토리는 아카이브 대상. 수동 또는 별도 스크립트로 처리.

## 범위

본 저장소는 **증거**만 담는다. 회귀 테스트(Playwright visual regression)는 `web/tests/e2e/visual/` 에 별도 보관한다.

## 체크리스트

- 스토리별 캡처 체크리스트는 `docs/superpowers/visual-log/checklists/` 에 둔다.
- 각 체크리스트는 `docs/plans/2026-04-17-user-story-execution-catalog-design.md` 의 Visual 키와 1:1로 대응한다.
