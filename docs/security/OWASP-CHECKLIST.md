## OneERP 보안 체크리스트 — OWASP Top 10 + NoSQL 인젝션

> 작성일: 2026-04-10 (Wave 2-F)
> 적용 범위: 전체 BE 서비스 (`services/`) + 공통 커널 (`core/oneerp_core/`)
> 검증 자동화: bandit (정적 분석) + pip-audit (의존성 CVE) — `CI 파이프라인`

본 체크리스트는 OWASP Top 10 2021 항목과 OneERP가 사용하는 FerretDB(MongoDB 와이어 프로토콜) 환경의 NoSQL 인젝션 위험을 통합 점검하기 위한 표준 운영 문서다. 모든 새 기능은 PR 머지 전 본 체크리스트의 적용 항목을 점검해야 한다.

### 1. 적용 상태 요약

| 상태 | 정의 |
|------|------|
| 구현 | 코드/CI/문서로 강제됨 |
| 부분 | 일부 경로/서비스만 적용됨, 잔여 작업 존재 |
| 미구현 | 적용되지 않음, Wave 3 이후 도입 예정 |

### 2. OWASP Top 10 2021

#### A01: 깨진 접근 제어 (Broken Access Control)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| RBAC/ABAC 권한 모델 명세 | 구현 | `core/oneerp_core/permissions.py`, `core/oneerp_core/auth.py` |
| 모든 API에 권한 dependency 강제 | 부분 | FastAPI Annotated + Depends require_permission 패턴 사용. Wave 3에서 OpenAPI 자동 검사 도입 |
| 테넌트 격리 (`tenant_id`) 강제 | 구현 | `core/oneerp_core/repository.py` 에서 모든 query에 `tenant_id` 자동 주입. `tests/unit/test_tenant_isolation.py` |
| 최소 권한 원칙 (least privilege) | 부분 | 기본 role 매트릭스 정의됨. 동적 위임/UI 강제는 Wave 3 |
| IDOR 방지 — 객체 소유권 검증 | 부분 | `repository.find_by_id` 가 자동으로 `tenant_id` 검증. owner_id 검증은 도메인별 누락 가능 |
| 비활성화된 사용자/토큰 무효화 | 부분 | JWT exp 강제. 즉시 폐기(blacklist) 미구현 (Wave 3) |
| Cross-tenant 누수 회귀 테스트 | 구현 | `core/tests/unit/test_tenant_isolation.py` (8 케이스) |

#### A02: 암호화 실패 (Cryptographic Failures)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| 통신 채널 TLS 1.2 이상 | 구현 | 운영 환경 ingress (cert-manager) — `docs/infra/ingress.md` 참조 |
| 비밀번호 해시 — bcrypt/argon2 | 구현 | `core/oneerp_core/auth.py` |
| 비밀(secrets) 환경변수화 (`ONEERP_*`) | 구현 | `CoreSettings`, hard-coded 비밀 금지. ruff S106/S107 차단 |
| JWT 서명 알고리즘 — RS256/ES256 | 구현 | `core/oneerp_core/auth.py`. HS256 기본 폴백은 dev 전용 |
| 민감정보 로그 마스킹 (PII, 카드번호 등) | 부분 | `core/oneerp_core/logging.py` 에 마스킹 헬퍼. 도메인별 적용은 PR 검증 |
| KMS / 외부 시크릿 매니저 통합 | 미구현 | Wave 4 (HashiCorp Vault 또는 K8s sealed-secrets) |
| 저장 데이터 암호화 (FerretDB) | 미구현 | DB 레벨 encryption-at-rest는 운영 인프라 (Wave 4) |

#### A03: 인젝션 (Injection)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| Pydantic v2 입력 검증 | 구현 | 모든 API 요청 모델은 BaseModel. ruff B 카테고리 규칙 |
| SQL 인젝션 — N/A (FerretDB 사용) | 구현 | RDB 미사용. 단 Alembic 사용 시 raw SQL 금지 |
| NoSQL 인젝션 | 부분 | 별도 섹션 참조 (3장) |
| OS 명령 인젝션 — subprocess shell 비활성화 | 구현 | bandit B602/B604/B605 차단 |
| LDAP/XPath/XML — 미사용 | N/A | OneERP는 LDAP/XPath/XML 미사용 |
| 템플릿 인젝션 (Jinja2) | 부분 | autoescape True 강제. 도메인별 사용자 입력 회피는 PR 검증 |

#### A04: 안전하지 않은 설계 (Insecure Design)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| 위협 모델링 (Threat Modeling) | 미구현 | Wave 3 — 도메인별 STRIDE 분석 (`docs/security/threats/<domain>.md`) |
| 비밀 관리 정책 명문화 | 부분 | `docs/security/secrets-policy.md` (Wave 3) |
| Rate Limiting 설계 | 미구현 | gateway 레벨 Wave 3 (slowapi 또는 envoy) |
| 안전한 기본값 (Secure Defaults) | 구현 | CoreSettings 모든 보안 옵션 deny-by-default |
| 비즈니스 로직 검증 — unique constraint | 부분 | FerretDB unique index 사용. 동시성(race) 검증은 도메인별 |

#### A05: 보안 구성 오류 (Security Misconfiguration)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| 디버그 모드 운영 차단 (`ONEERP_DEBUG=false`) | 구현 | `CoreSettings.debug` flag, prod 배포 시 강제 |
| 기본 자격증명 제거 | 구현 | 모든 dev 시드는 `ONEERP_DEV_*` prefix |
| 보안 헤더 (CSP, HSTS, X-Frame-Options) | 부분 | `core/oneerp_core/middleware.py`. CSP 도메인 화이트리스트는 Wave 3 |
| CORS 정책 — explicit origin | 구현 | `CoreSettings.cors_origins`, wildcard 금지 |
| 디렉토리 리스팅 비활성화 | 구현 | FastAPI 정적 파일 서빙 미사용 (gateway 통과) |
| 에러 메시지 — 스택트레이스 노출 차단 | 구현 | `core/oneerp_core/errors.py` 표준화. prod 응답 generic |
| 컨테이너 이미지 최소화 (distroless) | 부분 | Wave 4 (현재 python 3.14-slim) |

#### A06: 취약·오래된 컴포넌트 (Vulnerable Components)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| pip-audit / safety CI 통합 | 구현 | `CI 파이프라인` — `uv run pip-audit` (관측 모드) |
| Dependabot / Renovate 자동 PR | 미구현 | Wave 3 (CI 시스템 호환 도구 검토) |
| 의존성 lock — `uv.lock` 커밋 | 구현 | uv workspace lockfile |
| 이미지 SCA (Trivy/Grype) | 미구현 | Wave 4 |
| 라이선스 검사 | 미구현 | Wave 4 |

#### A07: 식별/인증 실패 (Identification & Authentication Failures)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| 계정 잠금 정책 (5회 실패 → 15분) | 부분 | gateway 레벨 미구현. Wave 3 |
| 다중 인증(MFA) | 미구현 | Wave 4 (TOTP/WebAuthn) |
| 세션 토큰 — 충분한 엔트로피 | 구현 | JWT + secrets.token_urlsafe |
| 토큰 회전 (refresh token rotation) | 부분 | refresh 발급은 구현. 자동 회전은 Wave 3 |
| Brute-force 방어 (gateway rate limit) | 미구현 | Wave 3 |
| 비밀번호 정책 — 길이/복잡도 | 구현 | `core/oneerp_core/auth.py` 에서 검증 |

#### A08: 소프트웨어/데이터 무결성 실패 (Software & Data Integrity Failures)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| 신뢰할 수 없는 deserialization 금지 | 구현 | bandit B301/B506 차단. yaml safe-load 강제 |
| CI/CD 파이프라인 무결성 (서명된 commit) | 미구현 | Wave 4 (gpg 서명 정책) |
| 컨테이너 이미지 서명 (cosign/notary) | 미구현 | Wave 4 |
| 감사 로그 (audit log) — append-only | 구현 | `core/oneerp_core/audit.py`. `tests/unit/test_audit.py` |

#### A09: 로깅/모니터링 실패 (Security Logging & Monitoring Failures)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| 구조화된 로그 (JSON) | 구현 | `core/oneerp_core/logging.py` |
| Request ID 추적 | 구현 | `core/oneerp_core/middleware.py` (RequestIdMiddleware) |
| 인증 실패 / 권한 거부 로깅 | 구현 | `core/oneerp_core/auth.py` |
| 감사 이벤트 (CRUD/권한 변경) | 구현 | `core/oneerp_core/audit.py` |
| 중앙 로그 수집 (Loki/ELK) | 미구현 | Wave 4 (운영 인프라) |
| 알림(Alerting) — 비정상 패턴 | 미구현 | Wave 4 (운영 인프라 + SIEM) |

#### A10: 서버측 요청 위조 (SSRF — Server-Side Request Forgery)

| 항목 | 상태 | 검증 방법 / 관련 코드 |
|------|------|----------------------|
| 외부 URL 호출 — 화이트리스트 강제 | 부분 | gateway egress 정책 미정. Wave 3 |
| URL 스킴 검증 (http/https 만 허용) | 부분 | 도메인별 검증 (외부 webhook 등) |
| 내부 메타데이터 IP 차단 (169.254.169.254) | 미구현 | Wave 3 (egress proxy) |
| `httpx` 사용 시 timeout 강제 | 구현 | `core/oneerp_core/_app_utils.py` 의 httpx 클라이언트 timeout 기본 30s |

### 3. NoSQL (FerretDB / MongoDB) 인젝션 체크리스트

OneERP는 FerretDB 2.7 (PostgreSQL backend, MongoDB wire protocol)을 사용한다. MongoDB 호환 query를 사용하므로 NoSQL 인젝션 위험이 존재한다.

#### 3.1 금지 사항 (Hard Rules)

| 규칙 | 사유 | 검증 |
|------|------|------|
| `where` 연산자 사용 금지 | 임의 JavaScript 실행 | 코드 리뷰 + grep |
| 사용자 입력을 dict로 직접 query 전달 금지 | 비교 연산자 우회 가능 | Pydantic 검증 후 명시 필드만 사용 |
| eval / mapReduce 사용 금지 | 임의 코드 실행 | 코드 리뷰 |
| 사용자 입력 → `re.compile` 직접 전달 금지 | ReDoS, regex 인젝션 | `re.escape(user_input)` 강제 |
| `find(...user_dict)` 패턴 금지 | type confusion 우회 | `repository.find_by` 헬퍼 사용 |

#### 3.2 필수 사항 (Must Do)

##### 3.2.1 Pydantic 검증 우선

잘못된 예 (취약):

```text
@router.get("/users")
async def list_users(filters: dict, db: Database):
    return await db.users.find(filters).to_list()
```

올바른 예:

```text
class UserFilter(BaseModel):
    status: Literal["active", "inactive"] | None = None
    role: str | None = Field(None, max_length=64, pattern=r"^[a-z_]+$")

@router.get("/users")
async def list_users(filters: Annotated[UserFilter, Query()], db: DbDep):
    query: dict[str, Any] = {"tenant_id": current_tenant_id()}
    if filters.status:
        query["status"] = filters.status
    if filters.role:
        query["role"] = filters.role
    return await db.users.find(query).to_list(length=1000)
```

##### 3.2.2 `tenant_id` 강제 주입

모든 query는 `repository.find_by` / `find_by_id` / `update_one` 헬퍼를 통해 `tenant_id`가 자동 주입되어야 한다. 직접 db 컬렉션 find 사용 시 코드 리뷰에서 차단.

```text
docs = await repo.find_by({"status": "open"})  # 자동으로 tenant_id 추가
```

##### 3.2.3 정렬/필드 화이트리스트

```text
ALLOWED_SORT_FIELDS: Final = frozenset({"created_at", "updated_at", "name"})

class ListQuery(BaseModel):
    sort_by: Literal["created_at", "updated_at", "name"] = "created_at"
    sort_dir: Literal["asc", "desc"] = "desc"
```

##### 3.2.4 Regex 인젝션 방어

```text
import re
search = request.query_params["q"]
escaped = re.escape(search)
# prefix-only 검색 + 대소문자 무시
db.users.find({"name": {"$regex": f"^{escaped}", "$options": "i"}})
```

##### 3.2.5 페이지네이션 한계

```text
class Pagination(BaseModel):
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0, le=10_000)
```

#### 3.3 리뷰 체크 항목

PR 리뷰 시 다음 패턴이 발견되면 보안 검토를 한 번 더 거친다:

| 패턴 | 의심 사항 |
|------|----------|
| where 연산자 | $where 연산자 사용 |
| 직접 db 컬렉션 find 호출 | repository 헬퍼 미사용 |
| regex + 사용자 입력 | regex 인젝션 |
| eval / exec 호출 | 임의 코드 실행 |
| 위험한 직렬화 (safe_load 미사용) | 신뢰할 수 없는 deserialization |
| subprocess shell 옵션 활성화 | OS 명령 인젝션 |
| not-equal null 우회 | 인증 우회 시도 |

### 4. 자동화된 보안 게이트

#### 4.1 bandit (정적 분석)

- 설정: `pyproject.toml` `[tool.bandit]`
- 실행: `uv run bandit -c pyproject.toml -r services/ core/oneerp_core/ -ll -ii`
- CI: `CI 파이프라인` — Wave 2 관측 모드 (`continue-on-error: true`)
- 전환 계획:
  - Wave 2 (현재): 관측만, 결과를 PR 코멘트에 노출
  - Wave 3: HIGH/CRITICAL 1건 이상 발생 시 fail
  - Wave 4: MEDIUM 이상 fail

#### 4.2 pip-audit (의존성 CVE)

- 실행: `uv run pip-audit --strict --skip-editable`
- CI: `CI 파이프라인` — Wave 2 관측 모드
- 전환 계획:
  - Wave 3: KNOWN CVE 발생 시 fail
  - Wave 4: 추가로 license 검사 통합

#### 4.3 ruff 보안 규칙 (S 카테고리)

이미 `pyproject.toml` `[tool.ruff.lint] select = ["S", ...]` 로 활성화. 다음 규칙이 자동 차단:

- S101 — assert 사용 (tests 제외)
- S105/S106/S107 — hard-coded password
- S108 — 안전하지 않은 임시 파일
- S301/S302 — 위험한 직렬화 모듈
- S303/S324 — MD5/SHA1
- S501 — SSL 검증 비활성화
- S506 — yaml.load (safe_load 미사용)
- S602/S604/S605/S607 — subprocess shell 활성화

### 5. 검증·운영 절차

#### 5.1 신규 기능 PR 체크리스트

새 API/도메인 서비스 PR 머지 전 다음 항목을 점검한다:

- [ ] Pydantic 모델로 입력 검증
- [ ] `tenant_id` 격리 — repository 헬퍼 사용
- [ ] 권한 dependency 부착
- [ ] 사용자 입력 → query/regex/sort 직접 전달 없음
- [ ] 비밀(secret) 값은 환경변수 (`ONEERP_*`)
- [ ] PII/민감정보 로그 마스킹 확인
- [ ] 권한 거부/인증 실패 음성 테스트 추가
- [ ] cross-tenant 음성 테스트 추가 (도메인별)
- [ ] bandit 신규 경고 0건 또는 사유 명시
- [ ] pip-audit 신규 CVE 0건 또는 사유 명시

#### 5.2 분기별 침투 테스트 (Wave 4)

- 외부 보안 업체 또는 적색팀(red team) 분기 1회
- 결과는 `docs/kb/incident/INC-NNNN-pen-test-<quarter>.md` 형식

#### 5.3 사고 대응 (Incident Response)

- 보안 사고 발견 시: `docs/kb/incident/INC-NNNN-slug.md` 작성
- 크리티컬 이슈는 24시간 내 patch + post-mortem
- 외부 노출 가능성 있으면 법무/CISO 즉시 보고

### 6. 참조

- OWASP Top 10 2021 — https://owasp.org/Top10/
- OWASP NoSQL Injection Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/NoSQL_Database_Injection_Prevention_Cheat_Sheet.html
- bandit documentation — https://bandit.readthedocs.io/
- pip-audit documentation — https://pypi.org/project/pip-audit/
- 내부: `core/oneerp_core/auth.py`, `core/oneerp_core/middleware.py`, `core/oneerp_core/permissions.py`
- 내부: `docs/engineering/ci/quality-gates.md` — CI 게이트 정의

### 7. 변경 이력

| 날짜 | 변경 | 작성자 |
|------|------|--------|
| 2026-04-10 | 초안 작성 (Wave 2-F) — OWASP Top 10 + NoSQL 인젝션 + bandit/pip-audit 통합 | 품질 게이트 에이전트 |
