---
module: fleet
approver: qa-lead@oneerp.dev
approved_date: 2026-05-07
test_run_id: uat-fleet-20260507
source: commercial-readiness-g5-3
---

# fleet UAT 승인 기록

## 승인 요약

`fleet` 모듈은 SaaS 상용 출시 전 사용자 인수 테스트 기준으로 검수한다.
본 문서는 사용자 시나리오, 기대 결과, 실패 대응, 테스트 데이터 정리를 하나의 승인 기록으로 묶는다.
승인은 코드 구현 완료 선언이 아니라 실행 가능한 사용자 흐름과 운영 증거가 함께 확인된 경우에만 유효하다.

기존 UAT 메모:
> ---
> module: fleet
> status: uat-in-progress
> uat_date: 2026-04-22
> sign_off: ["@module-lead", "@qa-lead"]
> ---
> # fleet 상용화 검수(UAT) 기록
> ## 범위
> fleet 모듈의 상용 준비도 ADR-0001 23 기준 점검.
> ## 검수 결과 (2026-04-22)
> - G1: 일부 PASS (ERD, OpenAPI 자동 생성)
> - G3: G3-4 audit_hooks.py 로 확보
> - G4: 운영 문서 작성 중
> - G5: 문서 기반
> ## 참조 문서
> - 런북: docs/ops/ 하위 관련
> - 드릴: docs/ops/drills/G4-{3,4,5}/
> - 성능: docs/engineering/data/perf-fleet-baseline.md
> - chaos: docs/kb/incident/chaos-fleet-2026-04-22.md
> ## 상용화 체크리스트 (ADR-0001 23 기준)
> - G1 기능 완전성: ERD·OpenAPI·통합/단위 테스트·UI 설정
> - G2 비기능: SLO·부하·회귀·Chaos·i18n
> - G3 보안: 인증·권한·테넌시·감사 로그·의존성 스캔
> - G4 운영: 관측성·런북·백업/롤백/on-call 드릴

## 테스트 범위

- 웹 UI 목록, 상세, 신규, 수정, 상태 전이 흐름
- API 계약과 화면 validation 메시지의 사용자-facing 일치
- tenant 컨텍스트, 역할 기반 권한, 감사 로그
- 오류 상태, 빈 상태, 저장 중 상태, 재시도 경로
- 테스트 데이터 생성부터 삭제 확인까지의 전체 라이프사이클

범위 제외:
- 신규 기능 추가
- 도메인 경계 변경
- 운영 데이터 직접 수정
- production 실사용자 데이터로 destructive 테스트

## 테스트 데이터 라이프사이클

- 식별자: `test_cleanup_20260507_fleet_uat`
- 시작 전: 테스트 tenant와 역할을 확인하고 동일 식별자 잔여 데이터를 조회한다.
- 실행 중: 생성, 수정, 승인, 반려, 삭제 이벤트의 request id를 기록한다.
- 실패 시: 실패 단계, 입력값, 응답 코드, 화면 메시지를 남기고 같은 데이터로 재실행한다.
- 종료 후: 테스트 데이터 삭제 확인, 첨부 파일 삭제 확인, 감사 로그 기록 확인을 수행한다.
- DB 초기화: 영속 seed가 필요한 경우 compose volume reset 또는 API 삭제로 원복한다.

삭제 확인 기준:
- 목록 재조회에서 `test_cleanup_20260507` 데이터가 보이지 않는다.
- 상세 조회는 404 또는 삭제 상태를 반환한다.
- 감사 로그에는 삭제 actor와 timestamp가 남는다.
- 관련 모듈 참조와 queue 잔여 항목이 없다.

## 사용자 시나리오

### 시나리오 1: 목록 조회

사용자 시나리오:
1. 사용자는 `fleet` 화면에 접속한다.
2. 사용자가 모듈 목록에 접속하고 필터를 적용한다.
3. 사용자는 화면 메시지, 상태 badge, 목록 갱신을 확인한다.
4. 사용자는 request id와 감사 로그를 운영 증거로 기록한다.

기대 결과:
- 목록, 총 건수, 빈 상태가 일관되게 표시된다.
- 사용자에게 모호한 서버 오류가 그대로 노출되지 않는다.
- 권한과 validation 실패는 데이터 변경 없이 종료된다.
- 감사 로그에 actor, tenant, action, timestamp가 남는다.

검증 명령:
```bash
python3 scripts/audit/commercial_readiness.py --module fleet --gate G5-3 --format text
```

### 시나리오 2: 신규 생성

사용자 시나리오:
1. 사용자는 `fleet` 화면에 접속한다.
2. 사용자가 test_cleanup_20260507 식별자로 신규 데이터를 저장한다.
3. 사용자는 화면 메시지, 상태 badge, 목록 갱신을 확인한다.
4. 사용자는 request id와 감사 로그를 운영 증거로 기록한다.

기대 결과:
- 저장 성공과 상세 화면 이동이 확인된다.
- 사용자에게 모호한 서버 오류가 그대로 노출되지 않는다.
- 권한과 validation 실패는 데이터 변경 없이 종료된다.
- 감사 로그에 actor, tenant, action, timestamp가 남는다.

검증 명령:
```bash
python3 scripts/audit/commercial_readiness.py --module fleet --gate G5-3 --format text
```

### 시나리오 3: 수정

사용자 시나리오:
1. 사용자는 `fleet` 화면에 접속한다.
2. 사용자가 상세 화면에서 허용된 필드를 변경한다.
3. 사용자는 화면 메시지, 상태 badge, 목록 갱신을 확인한다.
4. 사용자는 request id와 감사 로그를 운영 증거로 기록한다.

기대 결과:
- 변경 값과 감사 로그 diff가 남는다.
- 사용자에게 모호한 서버 오류가 그대로 노출되지 않는다.
- 권한과 validation 실패는 데이터 변경 없이 종료된다.
- 감사 로그에 actor, tenant, action, timestamp가 남는다.

검증 명령:
```bash
python3 scripts/audit/commercial_readiness.py --module fleet --gate G5-3 --format text
```

### 시나리오 4: 권한 검증

사용자 시나리오:
1. 사용자는 `fleet` 화면에 접속한다.
2. 권한이 부족한 사용자가 승인 또는 삭제 작업을 시도한다.
3. 사용자는 화면 메시지, 상태 badge, 목록 갱신을 확인한다.
4. 사용자는 request id와 감사 로그를 운영 증거로 기록한다.

기대 결과:
- 403 또는 권한 안내가 표시되고 데이터는 바뀌지 않는다.
- 사용자에게 모호한 서버 오류가 그대로 노출되지 않는다.
- 권한과 validation 실패는 데이터 변경 없이 종료된다.
- 감사 로그에 actor, tenant, action, timestamp가 남는다.

검증 명령:
```bash
python3 scripts/audit/commercial_readiness.py --module fleet --gate G5-3 --format text
```

### 시나리오 5: 정리

사용자 시나리오:
1. 사용자는 `fleet` 화면에 접속한다.
2. 사용자가 테스트 데이터와 임시 첨부를 삭제한다.
3. 사용자는 화면 메시지, 상태 badge, 목록 갱신을 확인한다.
4. 사용자는 request id와 감사 로그를 운영 증거로 기록한다.

기대 결과:
- 삭제 확인, 감사 로그, 재조회 불가 상태가 확인된다.
- 사용자에게 모호한 서버 오류가 그대로 노출되지 않는다.
- 권한과 validation 실패는 데이터 변경 없이 종료된다.
- 감사 로그에 actor, tenant, action, timestamp가 남는다.

검증 명령:
```bash
python3 scripts/audit/commercial_readiness.py --module fleet --gate G5-3 --format text
```

## 실패 대응

| 실패 유형 | 판정 기준 | 조치 |
|-----------|-----------|------|
| UI 오류 | 버튼, 입력, 상태가 기대와 다름 | Playwright 재현 로그와 스크린샷을 첨부한다 |
| API 오류 | 4xx/5xx가 기대와 다름 | OpenAPI 계약과 서버 로그를 대조한다 |
| 권한 오류 | 허용/거부 결과가 반대 | G3-1/G3-3 증거와 OPA policy를 확인한다 |
| 데이터 오류 | 저장 값, 목록 값, 감사 로그가 불일치 | 테스트 데이터 snapshot을 보존한다 |
| 정리 실패 | 테스트 데이터가 남음 | API 삭제 또는 compose reset으로 원복 후 재조회한다 |

실패 시 재실행 규칙:
- 원인 분석 없이 같은 테스트를 반복하지 않는다.
- 코드 수정 후 동일 시나리오를 다시 실행한다.
- 통과 전까지 승인 상태로 변경하지 않는다.
- 임시 완화는 UAT 승인으로 인정하지 않는다.

## 승인 체크리스트

- [x] 사용자 시나리오 5종이 문서화됐다.
- [x] 각 시나리오에 기대 결과가 있다.
- [x] 테스트 데이터 식별자가 `test_cleanup_20260507`로 고정됐다.
- [x] 삭제 확인 절차가 있다.
- [x] G3 인증/권한 증거와 연결된다.
- [x] G4 운영 런북과 연결된다.
- [x] 승인자와 승인일이 frontmatter에 기록됐다.

## 증거 연결

- 사용자 매뉴얼: `docs/user-manual/fleet.md`
- 튜토리얼: `docs/tutorials/fleet.md`
- 운영 런북: `docs/ops/runbook-fleet.md`
- UAT T2 결과: `artifacts/T2/G5-3/fleet/run-*.json`
- UAT T3 로그: `artifacts/uat/fleet-*.log`
- 상용 상태: `docs/generated/commercial-status.json`

## 승인 결론

`fleet` UAT는 지정된 시나리오와 테스트 데이터 정리 기준을 만족할 때 승인된다.
승인자는 frontmatter의 `approver`이며, 재검수 필요 시 `test_run_id`를 새로 발급한다.
본 승인 기록은 배포 승인 자체가 아니라 상용 출시 후보 판정의 사용자 인수 증거다.
