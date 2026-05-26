# ADR-0014 P1 API Plane 컨테이너 — ERP 동기 CRUD 21 도메인.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY core/ core/
COPY planes/_shared/ planes/_shared/
COPY planes/api_plane/ planes/api_plane/
# 21 ERP 도메인 전체 복사 (전체 services/ 를 복사하는 것이 더 단순)
COPY services/ services/

RUN uv sync --frozen --package oneerp-plane-api --no-dev

FROM python:3.14-slim-bookworm

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/core/ core/
COPY --from=builder /app/planes/ planes/
COPY --from=builder /app/services/ services/
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "plane_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
