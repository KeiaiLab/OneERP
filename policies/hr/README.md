# hr OPA RBAC

`hr.routes` 패키지 — gateway 에서 `/hr/*` 라우트 인가를 담당한다.

## 역할

| 역할 | 권한 |
|------|------|
| `hr_viewer` | `GET /hr/*` (단, `/hr/payroll/*` 제외) |
| `hr_editor` | `GET`/`POST`/`PUT`/`DELETE /hr/*` (단, `/hr/payroll/*` 제외) |
| `payroll_admin` | `/hr/payroll/*` 전체 메서드 (급여·개인정보 전담) |

## 개인정보 보호 설계

`/hr/payroll/*` 은 **payroll_admin 전용**. `hr_viewer`·`hr_editor` 는 접근 불가 — 급여/개인정보는 최소권한 원칙으로 분리한다.

## 테스트

```bash
opa test policies/hr/ -v
```

기대: 9 tests PASS.

## opa 바이너리 미설치 시 수동 검증

1. 문법 힌트
   - `import rego.v1` · `if` 구문.
   - `not startswith(input.path, "/hr/payroll/")` 로 payroll 을 viewer/editor 에서 배제.
2. 규칙 매트릭스
   - payroll_admin × any × `/hr/payroll/*` → allow
   - hr_viewer × GET × `/hr/*` (not payroll) → allow
   - hr_editor × (GET|POST|PUT|DELETE) × `/hr/*` (not payroll) → allow
   - 그 외 → default deny.
