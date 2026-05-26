# 환경 변수/시크릿 정책(초안)

## 원칙

- 시크릿은 Git에 커밋하지 않는다.
- 로컬 개발은 `.env`를 사용할 수 있으나 `.gitignore`로 차단한다.
- CI/운영은 “인벤토리에서 확인된 방식”으로만 주입한다.

## Phase 0 현황

- **환경변수 관리**: Pydantic Settings (`services/*/app/config.py`)
  - 접두사: `ONEERP_` (예: `ONEERP_DEBUG`, `ONEERP_FERRETDB_URI`)
  - `.env` 파일 자동 로드 지원
- **gitignore**: `.env`, `.env.*` 패턴으로 차단 완료

## 확인 필요(Phase 1)

- Secret 저장소: (GitHub Secrets/Vault/KMS 등)
- K8s 주입: Secret/ExternalSecrets/CSI driver 여부
- OIDC federation 사용 여부

