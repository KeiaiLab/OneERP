"""M3 platform/iot EventStreamService 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_core.uow import UnitOfWork
from oneerp_iot_app.services.sensor_stream_service import SensorStreamService


def _make_svc() -> tuple:
    uow = UnitOfWork(tenant_id="t1")
    svc = SensorStreamService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.insert.return_value = "SNSR-EVT-001"
    repo.write_outbox = MagicMock()
    svc.register_repo("sensor_event", repo)
    return svc, repo


def test_센서_데이터_수집() -> None:
    svc, repo = _make_svc()
    result = svc.ingest(
        event={
            "sensor_id": "TEMP-1F-A",
            "temperature_c": 23.5,
            "timestamp": "2026-04-12T11:00:00+09:00",
        },
        source="warehouse_floor_sensor",
    )
    assert result["event_id"] == "SNSR-EVT-001"
    assert result["stream"] == "iot.sensor"
    assert result["source"] == "warehouse_floor_sensor"
    subject, _ = repo.write_outbox.call_args[0]
    assert subject == "stream.iot.sensor.received"
