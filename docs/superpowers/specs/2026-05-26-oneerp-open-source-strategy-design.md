# OneERP 오픈소스 전환 전략 설계

- **작성일**: 2026-05-26
- **상태**: Approved
- **결정자**: phil (케이아이랩 CTO)

---

## 1. 배경 및 동기

OneERP는 ERPNext와 기능 동등성(feature parity)을 목표로 하는 통합 비즈니스 앱이다.
현재 GitLab `keiailab/services/apps-onerp`에서 private으로 개발 중이며,
다음 세 가지 동기로 오픈소스 전환을 결정했다:

1. **커뮤니티 기여 확보** — 외부 개발자의 기여로 개발 속도와 품질을 높인다
2. **시장 신뢰·채택 확대** — 소스 공개 투명성으로 벤더 락인 우려를 해소한다
3. **ERPNext 한국 대안 포지셔닝** — ERPNext의 한국 시장 한계(로컬라이제이션, 세금 체계)를 해결하는 오픈소스 대안이 된다

---

## 2. 핵심 결정

### 2.1 접근 방식: Full Open Source (AGPL v3)

전체 코드를 AGPL-3.0-or-later로 공개한다.

- ERPNext(GPL v3)와 동일 계열 copyleft로 대안 포지셔닝 명확
- AGPL의 네트워크 조항이 SaaS 무임승차를 법적으로 방지
- 향후 CLA 확보 시 듀얼 라이선스 전환 가능성 보존

### 2.2 공개 시점: 조기 (1-2개월 내)

커뮤니티와 함께 만들어가는 "build in public" 접근.
v1.0 완성을 기다리지 않고 현재 상태에서 공개한다.

### 2.3 Git History: Fresh Start

과거 커밋에 시크릿 노출 리스크를 제거하기 위해 새 초기 커밋으로 시작한다.
원본 히스토리는 내부 GitLab에 보존한다.

---

## 3. 라이선스 및 법적 구조

### 3.1 라이선스 배분

| 대상 | 라이선스 |
|---|---|
| 메인 코드 (core + services + web + planes) | AGPL-3.0-or-later |
| 문서 (docs/) | CC BY-SA 4.0 |
| 향후 `oneerp_core` 독립 패키지 배포 시 | 별도 검토 (LGPL v3 또는 Apache 2.0 듀얼) |

### 3.2 기여 합의: DCO (Developer Certificate of Origin)

- 초기에는 DCO(Signed-off-by)로 운영하여 진입장벽을 낮춘다
- 커뮤니티 규모 성장 시 CLA(Contributor License Agreement)로 전환 검토
- CLA 전환 이유: 듀얼 라이선스 또는 라이선스 업그레이드 필요 시

### 3.3 필수 파일

- `LICENSE` — AGPL v3 전문
- `NOTICE` — 저작권자(케이아이랩 주식회사) + 서드파티 라이선스 목록
- `DCO` — Developer Certificate of Origin 1.1 전문

---

## 4. 저장소 구조 및 민감 분리

### 4.1 전략: 단일 공개 저장소 + 내부 오버레이

GitHub에 공개 저장소를 생성하고, 민감 부분만 별도 private repo에 유지한다.

### 4.2 공개 대상

```
공개 (GitHub)
├── core/                    # 공통 커널
├── planes/                  # 6 Runtime Plane
├── services/                # 48개 도메인
├── web/                     # 프론트엔드
├── docs/                    # API, 아키텍처, 매뉴얼, 온보딩
├── scripts/                 # 개발/감사 스크립트
├── .planning/PROJECT.md     # 제품 정의
├── .planning/ROADMAP.md     # 공개 로드맵
├── .planning/REQUIREMENTS.md # 요구사항
└── .planning/STATE.md       # 현재 상태
```

### 4.3 비공개 유지 (별도 private repo)

| 경로 | 이유 |
|---|---|
| `deploy/secrets/` | ExternalSecret 정의, 시크릿 키 이름 |
| `.planning/strategy/` | 내부 제품 전략, 경쟁 분석 |
| `.planning/program/` | 내부 PMO, 리스크 레지스터 |
| `artifacts/T3/` | staging 승인 서명 |
| 내부 인프라 설정 | 클러스터 주소, bastion IP |

### 4.4 환경변수 치환

하드코딩된 내부 도메인/IP를 `${ONEERP_*}` 환경변수로 치환한다.
`.env.example`에 개발 환경용 기본값을 제공한다.

---

## 5. 커뮤니티 인프라

### 5.1 GitHub 조직 및 저장소

- Organization: `oneerp` (또는 `keiailab` 하위 — 결정 필요)
- Repository: `oneerp/oneerp` (모노레포)
- Discussions 활성화: Q&A, Ideas, Show & Tell, Announcements

### 5.2 커뮤니티 문서

| 파일 | 용도 |
|---|---|
| `README.md` | 프로젝트 소개, 퀵스타트, 배지 |
| `CONTRIBUTING.md` | 기여 가이드 (DCO, 코드 스타일, PR 규칙) |
| `CODE_OF_CONDUCT.md` | Contributor Covenant v2.1 |
| `SECURITY.md` | 보안 취약점 신고 절차 (private disclosure) |
| `GOVERNANCE.md` | 거버넌스 구조 (BDFL → Steering Committee) |
| `ROADMAP.md` | 공개 로드맵 |
| `docs/getting-started.md` | 10분 개발 환경 셋업 |
| `docs/architecture.md` | 아키텍처 개요 (6 Plane + 48 도메인) |
| `docs/module-guide.md` | 새 모듈 추가 가이드 |

### 5.3 거버넌스 모델

**초기 (Year 1)**: BDFL — 케이아이랩 핵심 팀이 방향 결정

| 역할 | 권한 | 조건 |
|---|---|---|
| Maintainer | merge, release, 아키텍처 결정 | 케이아이랩 팀 |
| Committer | 특정 모듈 merge 권한 | 3+ merged PR |
| Contributor | PR, issue, discussion | 누구나 |

**성장 후**: Steering Committee + SIG(Special Interest Group) per domain

### 5.4 커뮤니케이션 채널

- **GitHub Discussions**: 공식 Q&A, RFC, 아이디어
- **Discord**: 실시간 소통 (채널: #general, #dev, #help, 도메인별)
- **GitHub Issues**: 버그 리포트, 기능 요청
- **블로그**: 릴리즈 노트, 기술 글, 마일스톤 업데이트

### 5.5 기여 온보딩 전략

1. **Good First Issue**: 도메인별 1-2개, 공개 시 10-20개 사전 준비
2. **모듈 독립성**: 한 도메인만 이해해도 기여 가능한 구조 강조
3. **이중 언어**: README/CONTRIBUTING = 한국어 + 영어. 코드 주석 = 영어
4. **Docker Compose 원클릭**: `docker compose up` → 전체 스택 10분 내 기동
5. **한국 로컬라이제이션 강조**: 세금계산서, 4대보험 등 = 차별화 + 기여 유인

---

## 6. 수익 모델

### 6.1 원칙

코드는 100% 공개. 수익은 **운영 편의성**에서 창출한다.
"직접 설치할 수 있지만, 우리가 운영하면 더 편하다."

### 6.2 수익원

| 수익원 | 설명 | 시작 시점 |
|---|---|---|
| **OneERP Cloud (SaaS)** | 관리형 멀티테넌트 호스팅 + 자동 업데이트 + 백업 | v1.0 |
| **기술 지원 구독** | SLA 보장, 온프레미스 설치 지원, 마이그레이션 | 공개 직후 |
| **컨설팅/구축** | 커스터마이징, ERP 도입 컨설팅, 교육 | 공개 직후 |
| **마켓플레이스** | 서드파티 모듈/테마 수수료 | 커뮤니티 성장 후 |

---

## 7. 공개 전 실행 체크리스트

### Phase 1: 시크릿 감사 및 정리 (Week 1-2)

- [ ] `trufflehog` / `gitleaks`로 전체 코드 시크릿 스캔
- [ ] `deploy/secrets/` → 별도 private repo 분리
- [ ] `.planning/strategy/`, `.planning/program/` → private repo 분리
- [ ] `artifacts/T3/` → private
- [ ] 하드코딩된 내부 도메인/IP → 환경변수 치환 확인
- [ ] `.env.example` 작성
- [ ] 서드파티 라이선스 감사 (`pip-licenses`, `license-checker`)

### Phase 2: 공개 저장소 준비 (Week 2-3)

- [ ] GitHub organization 생성
- [ ] Fresh start 커밋 준비 (stable 브랜치 기준 스냅샷)
- [ ] `LICENSE`, `NOTICE`, `DCO` 추가
- [ ] `README.md` 오픈소스 프로젝트용 재작성
- [ ] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` 작성
- [ ] `GOVERNANCE.md` 작성
- [ ] `.github/ISSUE_TEMPLATE/` (bug, feature, module-request)
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] `docs/getting-started.md` (로컬 개발 환경 10분 셋업)

### Phase 3: 개발자 경험 (Week 3-4)

- [ ] Docker Compose 원클릭 개발 환경
- [ ] Good First Issue 10-20개 생성
- [ ] GitHub Actions CI (OSS 프로젝트 — ADR로 §2 예외 문서화)
- [ ] OpenAPI → Swagger UI 자동 문서
- [ ] ROADMAP.md 공개 버전
- [ ] 기여자 가이드 영어 번역

### Phase 4: 공개 및 런칭 (Week 4-6)

- [ ] 저장소 visibility → public
- [ ] 런칭 블로그 포스트 (dev.to, 개인 블로그)
- [ ] 커뮤니티 채널 공유 (Hacker News, Reddit r/selfhosted, 한국 개발자 커뮤니티)
- [ ] Discord 서버 오픈
- [ ] 첫 릴리즈 태그: `v0.1.0-alpha`
- [ ] Product Hunt / AlternativeTo 등록

---

## 8. 리스크 및 완화

| 리스크 | 영향 | 완화 |
|---|---|---|
| 시크릿 유출 (git history) | Critical | Fresh start로 원천 차단 |
| Fork 후 경쟁 SaaS | High | AGPL 네트워크 조항이 법적 방어 |
| 커뮤니티 무관심 | Medium | Good First Issue + 한국 로컬라이제이션 차별화 |
| 내부 개발 속도 저하 (리뷰 부담) | Medium | Committer 승격 기준 명확화 + bot 활용 |
| 라이선스 충돌 (의존성) | Medium | Phase 1에서 라이선스 감사 |

---

## 9. 성공 지표

| 지표 | 3개월 목표 | 6개월 목표 |
|---|---|---|
| GitHub Stars | 100+ | 500+ |
| 외부 Contributor (1+ merged PR) | 5+ | 20+ |
| Good First Issue 완료율 | 50%+ | 80%+ |
| Discord 멤버 | 50+ | 200+ |
| SaaS 대기자 목록 | 20+ | 100+ |

---

## 10. 관련 문서

- ADR-0014: 6 Runtime Plane 아키텍처
- `.planning/PROJECT.md`: 현재 제품 정의
- `.planning/ROADMAP.md`: 실행 로드맵
- `docs/governance/adr/`: 기존 ADR 모음

---

## 11. 다음 단계

1. 본 spec 승인 후 → 실행 계획(writing-plans) 작성
2. Phase 1 시크릿 감사부터 시작
3. GitHub Actions 예외에 대한 ADR 작성 (§2 영구 금지 조항 예외 문서화)
