# ADR-0014 P6 Platform-Adapter Plane 컨테이너.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY core/ core/
COPY planes/_shared/ planes/_shared/
COPY planes/extension_plane/ planes/extension_plane/
COPY services/platform/iot/ services/platform/iot/
COPY services/platform/integration-hub/ services/platform/integration-hub/
COPY services/marketing/marketing/ services/marketing/marketing/
COPY services/marketing/marketing-automation/ services/marketing/marketing-automation/
COPY services/marketing/gtm/ services/marketing/gtm/
COPY services/collab/board/ services/collab/board/
COPY services/collab/projects/ services/collab/projects/
COPY services/collab/wiki/ services/collab/wiki/
COPY services/collab/knowledge/ services/collab/knowledge/
COPY services/collab/documents/ services/collab/documents/
COPY services/collab/survey/ services/collab/survey/

RUN uv sync --frozen --package oneerp-plane-extension --no-dev

FROM python:3.14-slim-bookworm

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/core/ core/
COPY --from=builder /app/planes/ planes/
COPY --from=builder /app/services/ services/
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "plane_extension.main:app", "--host", "0.0.0.0", "--port", "8000"]
