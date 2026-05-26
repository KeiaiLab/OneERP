# ADR-0014 P3 Worker Plane 컨테이너 — 이벤트 구독 전용, 포트 노출 없음.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY core/ core/
COPY planes/_shared/ planes/_shared/
COPY planes/worker_plane/ planes/worker_plane/
# Worker Plane 대상 도메인 (M2 _EVENT_DOMAINS)
COPY services/sales/selling/ services/sales/selling/
COPY services/sales/crm/ services/sales/crm/
COPY services/scm/stock/ services/scm/stock/
COPY services/scm/manufacturing/ services/scm/manufacturing/
COPY services/scm/buying/ services/scm/buying/
COPY services/finance/accounting/ services/finance/accounting/
COPY services/finance/payroll/ services/finance/payroll/
COPY services/finance/expenses/ services/finance/expenses/
COPY services/hr/hr/ services/hr/hr/
COPY services/assets/plm/ services/assets/plm/
COPY services/assets/assets/ services/assets/assets/

RUN uv sync --frozen --package oneerp-plane-worker --no-dev

FROM python:3.14-slim-bookworm

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/core/ core/
COPY --from=builder /app/planes/ planes/
COPY --from=builder /app/services/ services/
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "plane_worker.main:app", "--host", "0.0.0.0", "--port", "8000"]
