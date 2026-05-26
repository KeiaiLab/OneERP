# 이중 배포 모델 공통화

## 목표

- `docker-compose 기반 온프렘`과 `K8s/Helm/ArgoCD 기반 MSA`가 같은 서비스 정의를 사용한다.
- 두 환경은 같은 `release manifest`를 소비하고, 배포 엔진만 다르게 둔다.
- 서비스 추가/제거/버전 변경은 `deploy/catalog/`만 수정하고 산출물은 generator가 갱신한다.

## 단일 SoT

- 서비스 카탈로그: `deploy/catalog/services.yaml`
- 플랫폼 오버레이: `deploy/catalog/platforms.yaml`
- 현재 릴리즈: `deploy/catalog/releases/current.yaml`

## 생성 산출물

- `docker-compose.yml`
- `deploy/apps/applicationset.yaml`
- `deploy/charts/*/values-release.yaml`

## 운영 흐름

1. 운영자는 `deploy/catalog/releases/current.yaml`에서 플랫폼 릴리즈를 변경한다.
2. `uv run python -m scripts.deploy sync`로 산출물을 갱신한다.
3. 온프렘은 `docker compose --profile <profile> up -d`로 배포한다.
4. K8s는 ArgoCD가 `values-release.yaml` 변경을 감지해 동일 릴리즈를 배포한다.

## 검증

- `uv run python -m scripts.deploy validate`
- `uv run pytest tests/unit/test_deploy_generator.py -q`
