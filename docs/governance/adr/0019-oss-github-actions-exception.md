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

**공개 OSS 저장소에 한하여 GitHub Actions 사용을 허용한다.**

조건:
- 공개 저장소에서만 적용 (내부 GitLab 저장소는 §2 그대로 적용)
- self-hosted runner 금지 (무료 GitHub-hosted runner만 사용)
- 워크플로우는 lint/typecheck/test 게이트만 (배포 워크플로우 금지)

## Consequences

- 외부 기여자의 PR이 자동으로 품질 게이트를 통과하는지 확인 가능
- billing 리스크 없음 (공개 저장소 무료 tier)
- 내부 개발 프로세스의 §2 원칙은 유지
