# accounting OPA RBAC

`accounting.routes` 패키지 — gateway 에서 `/accounting/*` 라우트 인가를 담당한다.

## 역할

| 역할 | 권한 |
|------|------|
| `accounting_viewer` | `GET /accounting/*` |
| `accounting_editor` | `POST`/`PUT`/`DELETE /accounting/journal*` |

## 테스트

```bash
opa test policies/accounting/ -v
```

기대: 6 tests PASS.

## opa 바이너리 미설치 시 수동 검증

1. 문법 힌트
   - 모든 규칙은 `import rego.v1` · `if` 구문 사용.
   - `input.user.roles[_] == "<role>"` 패턴으로 역할 매칭.
2. 규칙 매트릭스
   - viewer × GET → allow
   - editor × (POST|PUT|DELETE) /accounting/journal → allow
   - 그 외 조합 → default deny.
3. gateway 에서 OPA sidecar 로 로드: `opa eval -d policies/accounting/ -i input.json 'data.accounting.routes.allow'`.
