# OneERP Governance

## 거버넌스 모델

OneERP는 초기 단계에서 BDFL(Benevolent Dictator For Life) 모델을 채택한다.
커뮤니티 규모가 성장하면 Steering Committee 모델로 전환할 계획이다.

## 역할

### Maintainer

- 책임: 프로젝트 방향 결정, 코드 리뷰, 릴리즈 관리
- 권한: 모든 저장소에 대한 merge/release 권한
- 대상: 케이아이랩 핵심 팀

### Committer

- 책임: 특정 모듈의 코드 리뷰 및 merge
- 권한: 담당 모듈에 대한 merge 권한
- 조건: 3개 이상의 merged PR + Maintainer 추천

### Contributor

- 모든 외부 기여자
- PR 제출, Issue 생성, Discussion 참여 가능
- DCO sign-off 필수

## 의사결정 프로세스

1. **일상적 결정**: Maintainer가 PR 리뷰로 결정
2. **아키텍처 결정**: ADR 작성 → Maintainer 합의
3. **방향 결정**: GitHub Discussion에서 RFC → Maintainer 투표

## ADR (Architecture Decision Record)

아키텍처 결정은 `docs/governance/adr/`에 ADR로 기록한다.

## 행동 강령

모든 참여자는 [Code of Conduct](CODE_OF_CONDUCT.md)를 준수한다.
