# ADR-0014 P2 Realtime Plane 컨테이너.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY core/ core/
COPY planes/_shared/ planes/_shared/
COPY planes/realtime_plane/ planes/realtime_plane/
COPY services/portal/portal_core/ services/portal/portal_core/
COPY services/portal/portal_comms/ services/portal/portal_comms/
COPY services/collab/calendar/ services/collab/calendar/

RUN uv sync --frozen --package oneerp-plane-realtime --no-dev

FROM python:3.14-slim-bookworm

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/core/ core/
COPY --from=builder /app/planes/ planes/
COPY --from=builder /app/services/ services/
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "plane_realtime.main:app", "--host", "0.0.0.0", "--port", "8000"]
