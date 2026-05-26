# ADR-0014 P5 Edge/BFF Plane 컨테이너.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY core/ core/
COPY planes/_shared/ planes/_shared/
COPY planes/edge_plane/ planes/edge_plane/
COPY services/platform/gateway/ services/platform/gateway/

RUN uv sync --frozen --package oneerp-plane-edge --no-dev

FROM python:3.14-slim-bookworm

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/core/ core/
COPY --from=builder /app/planes/ planes/
COPY --from=builder /app/services/ services/
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "plane_edge.main:app", "--host", "0.0.0.0", "--port", "8000"]
