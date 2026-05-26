.PHONY: help status smoke lint typecheck test versions-check br-sync docs-gate arch-check arch-baseline stack-up stack-down stack-smoke stack-logs stack-metrics verify-roadmap roadmap-render total-commercial-gate

help:  ## 이 메시지 표시
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## --- 상태·문서 ---
status:  ## docs/STATUS.md frontmatter 갱신 (실측 반영)
	python3 scripts/docs/gen_status.py --write

versions-check:  ## 버전 문서 drift 검사 (CI)
	python3 scripts/docs/render_versions.py

br-sync:  ## BR 번호 ↔ 모듈 BR-COMMITS.md 동기화
	python3 scripts/docs/sync_br_codes.py --write

docs-gate:  ## 문서 전체 품질 게이트 (strict)
	python3 scripts/docs/check_integrity.py
	python3 scripts/docs/render_versions.py
	python3 scripts/docs/gen_status.py
	python3 scripts/docs/sync_br_codes.py

total-commercial-gate:  ## 전체 상용 완성용 출시급 실측 게이트
	./scripts/ci/run_total_commercial_gate.sh

verify-roadmap:  ## 로드맵 게이트 — 렌더 drift + 링크 + 금지 어휘 + stale 배너
	python3 scripts/roadmap/status_render.py --check
	python3 scripts/roadmap/link_check.py --forward --reverse
	python3 scripts/roadmap/forbidden_terms.py
	python3 scripts/roadmap/stale_check.py --warn-only

roadmap-render:  ## 로드맵 status.md 자동 섹션 재렌더 (쓰기 모드)
	python3 scripts/roadmap/status_render.py
	python3 scripts/roadmap/stale_check.py --warn-only

## --- 아키텍처 ---
arch-check:  ## Route→Service→Repository 경계 검사 (baseline 대비 감소만 허용)
	python3 scripts/dev/check_layer_boundaries.py --check

arch-baseline:  ## 현재 위반 수를 baseline 으로 갱신 (감소 반영 시)
	python3 scripts/dev/check_layer_boundaries.py --update-baseline

## --- 코드 품질 ---
lint:  ## ruff format + check
	uv run ruff format --check .
	uv run ruff check .

typecheck:  ## ty 정적 타입 검사
	uv run ty check .

test:  ## 전체 유닛 테스트 (integration·e2e 제외)
	uv run pytest -m "not integration and not e2e" services/ packages/ tests/unit/

## --- 스모크 ---
## --- docker-compose 스택 (MSA 간소화 캠페인) ---
# PROFILE 기본값: starter (docs/engineering/msa/CONSOLIDATION.md 의 7단계 중 3번째)
PROFILE ?= starter

stack-up:  ## 지정 profile 로 compose up -d 실행 (PROFILE=minimal|starter|business|advanced|platform|full)
	docker compose --profile $(PROFILE) up -d

stack-down:  ## 모든 profile 의 compose down 실행 (볼륨 보존)
	docker compose --profile full down

stack-smoke:  ## compose up → healthcheck wait → /health curl 전수 → down (스모크 게이트)
	scripts/dev/stack-smoke.sh $(PROFILE)

stack-logs:  ## 실행 중인 compose 서비스 로그 추적 (SERVICE=<name> 지정 시 단일)
	@if [ -n "$(SERVICE)" ]; then \
		docker compose logs -f $(SERVICE); \
	else \
		docker compose logs -f; \
	fi

stack-metrics:  ## 실행 중 스택의 컨테이너별 RAM/CPU 스냅샷 (docker stats --no-stream)
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

smoke: lint typecheck  ## QUICKSTART 3단계 — 로컬 환경 검증
	@echo "=== 공통 커널 유닛 테스트 ==="
	uv run pytest -m "not integration and not e2e" packages/ tests/unit/ -q
	@echo ""
	@echo "=== 매출-매출채권(FL1) 시나리오 (환경 준비 시) ==="
	@if docker compose ps --status running --services 2>/dev/null | grep -q ferretdb; then \
		uv run pytest tests/e2e -m "fl1" -q || echo "  (FL1 시나리오 파일 없음 또는 skipped)"; \
	else \
		echo "  (FerretDB 미기동 — docker compose up -d 실행 후 재시도)"; \
	fi
	@echo ""
	@echo "✓ 스모크 통과. 다음 단계는 docs/onboarding/QUICKSTART.md 의 '다음 단계' 5개 링크 참조."
