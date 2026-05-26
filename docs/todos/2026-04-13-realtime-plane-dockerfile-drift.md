# TODO — realtime_plane Dockerfile 경로 드리프트

- 발견일: 2026-04-13
- 발견 맥락: 시각 이중 루프 웜업 중 전체 백엔드 기동 시도

## 증상

`./scripts/dev/compose-up.sh` 실행 시 realtime_plane 이미지 빌드가 실패:

```
COPY failed: file not found in build context or excluded by .dockerignore:
stat services/portal/portal_core_merged/: file does not exist
```

## 원인

`planes/realtime_plane/Dockerfile:9` 가 존재하지 않는 경로를 COPY 대상으로 지정:

```dockerfile
COPY services/portal/portal_core_merged/ services/portal/portal_core_merged/
```

실제 `services/portal/` 하위 디렉토리:
- `portal_comms/`
- `portal_core/`
- (`portal_core_merged/` 없음 — 포털 리팩터링 이후 Dockerfile 미갱신)

## 영향

- 로컬: `compose-up.sh` 전체 실패 → 6 plane 중 일부만 올라오거나 아예 올라가지 않음
- CI/배포: realtime_plane 이미지 빌드 파이프라인도 동일 영향 가능성 (점검 필요)

## 해결 방향 후보

1. **단순 교체**: `portal_core_merged` → `portal_core` — 가장 가능성 높음. 단, runtime에서 `portal_core_merged` 모듈/패키지를 import하는 코드가 없는지 확인 필요
2. **병합 원복**: 만약 `portal_core_merged`가 의도된 임시 합성 디렉토리였다면, 빌드 전 생성 스크립트 추가
3. **realtime_plane 제외**: 해당 plane이 현재 미사용이면 profile 분리 고려

## 조사 포인트

- `git log planes/realtime_plane/Dockerfile` — 언제/왜 `portal_core_merged` 경로가 들어갔는지
- `grep -r "portal_core_merged" services/ planes/` — runtime 의존 여부
- 관련 ADR (ADR-0014 plane 구조, 포털 리팩터링 ADR 있는지)

## 우선순위

보통. 시각 이중 루프 웜업 자체는 FE만으로 완료되었으므로 급하지 않음.
그러나 FE에서 로그인 엔드투엔드 시연을 하려면 edge-plane+gateway만이라도 기동 필요.
