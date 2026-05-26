"""SensorStreamService — M3 platform/iot."""

from __future__ import annotations

from oneerp_core.service_base import EventStreamService


class SensorStreamService(EventStreamService):
    REPO_KEY = "sensor_event"
    STREAM_NAME = "iot.sensor"
