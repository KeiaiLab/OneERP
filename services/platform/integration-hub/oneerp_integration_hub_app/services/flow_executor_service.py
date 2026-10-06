"""통합 플로우 실행 서비스 — ETL/동기화/이벤트 파이프라인 실행."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 클라이언트용 고정 오류 문구 — 상세는 서버 로그와 integration_logs 에만 둔다.
_FLOW_FAILED = "플로우 실행 실패"


class FlowExecutorService:
    """통합 플로우 실행 비즈니스 로직.

    커넥터·매핑 설정을 기반으로 데이터 추출/변환/적재 파이프라인을 실행한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._flow_repo = Repository("integration_flows", tenant_id=tenant_id)
        self._connector_repo = Repository("connectors", tenant_id=tenant_id)
        self._mapping_repo = Repository("data_mappings", tenant_id=tenant_id)
        self._log_repo = Repository("integration_logs", tenant_id=tenant_id)

    def execute_flow(self, flow_id: str) -> dict[str, Any]:
        """통합 플로우를 실행한다.

        Args:
            flow_id: 실행할 플로우 ID

        Returns:
            실행 결과 (status, records_processed, duration_ms)

        Raises:
            ValueError: 플로우 미존재 또는 비활성
        """
        flow = self._flow_repo.find_by_id(flow_id)
        if not flow:
            msg = f"통합 플로우를 찾을 수 없습니다: {flow_id}"
            raise ValueError(msg)

        if not flow.get("is_active", True):
            msg = f"비활성 플로우입니다: {flow_id}"
            raise ValueError(msg)

        started_at = datetime.now(tz=UTC)

        # 소스 커넥터 확인
        source_id = flow.get("source_connector_id", "")
        source = self._connector_repo.find_by_id(source_id) if source_id else None

        # 매핑 설정 확인
        mapping_id = flow.get("mapping_id", "")
        mapping = self._mapping_repo.find_by_id(mapping_id) if mapping_id else None

        try:
            # 단계별 실행
            steps = flow.get("steps", [])
            records_processed = 0
            records_failed = 0

            for step in steps:
                step_result = self._execute_step(step, source, mapping)
                records_processed += step_result.get("processed", 0)
                records_failed += step_result.get("failed", 0)

            completed_at = datetime.now(tz=UTC)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            # 플로우 상태 업데이트
            self._flow_repo.update_by_id(
                flow_id,
                {
                    "last_run_at": completed_at.isoformat(),
                    "last_run_status": "success",
                },
            )

            # 실행 로그 기록
            self._log_repo.insert(
                {
                    "tenant_id": self._tenant_id,
                    "flow_id": flow_id,
                    "connector_id": source_id,
                    "direction": "outbound",
                    "status": "success",
                    "records_processed": records_processed,
                    "records_failed": records_failed,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "duration_ms": duration_ms,
                }
            )

            logger.info(
                "플로우 실행 완료: %s — 처리: %d건, 실패: %d건, 소요: %dms",
                flow_id,
                records_processed,
                records_failed,
                duration_ms,
            )

            return {
                "flow_id": flow_id,
                "status": "success",
                "records_processed": records_processed,
                "records_failed": records_failed,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            error_msg = str(e)
            completed_at = datetime.now(tz=UTC)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            self._flow_repo.update_by_id(
                flow_id,
                {
                    "last_run_at": completed_at.isoformat(),
                    "last_run_status": "failed",
                },
            )

            self._log_repo.insert(
                {
                    "tenant_id": self._tenant_id,
                    "flow_id": flow_id,
                    "connector_id": source_id,
                    "direction": "outbound",
                    "status": "failed",
                    "error_message": error_msg,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "duration_ms": duration_ms,
                }
            )

            logger.exception("플로우 실행 실패: %s", flow_id)

            return {
                "flow_id": flow_id,
                "status": "failed",
                "error": _FLOW_FAILED,
                "duration_ms": duration_ms,
            }

    def transform_data(
        self,
        mapping_id: str,
        source_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """데이터 매핑 규칙에 따라 데이터를 변환한다.

        Args:
            mapping_id: 매핑 설정 ID
            source_data: 변환 대상 소스 데이터

        Returns:
            변환 결과 (transformed_data, total, success, failed)

        Raises:
            ValueError: 매핑 설정 미존재
        """
        mapping = self._mapping_repo.find_by_id(mapping_id)
        if not mapping:
            msg = f"데이터 매핑을 찾을 수 없습니다: {mapping_id}"
            raise ValueError(msg)

        field_mappings = mapping.get("field_mappings", [])
        transformed: list[dict[str, Any]] = []
        failed_count = 0

        for record in source_data:
            try:
                target_record = self._apply_mapping(record, field_mappings)
                transformed.append(target_record)
            except Exception:
                failed_count += 1
                logger.warning("레코드 변환 실패: %s", record)

        return {
            "transformed_data": transformed,
            "total": len(source_data),
            "success": len(transformed),
            "failed": failed_count,
        }

    def _execute_step(
        self,
        step: dict[str, Any],
        source: dict[str, Any] | None,  # noqa: ARG002
        mapping: dict[str, Any] | None,  # noqa: ARG002
    ) -> dict[str, int]:
        """개별 플로우 단계를 실행한다.

        source/mapping은 실제 구현에서 커넥터 호출·변환에 사용된다.
        """
        step_type = step.get("step_type", "transform")
        config = step.get("config", {})
        batch_size = config.get("batch_size", 100)

        logger.info("단계 실행: %s (batch_size=%d)", step_type, batch_size)

        # 실제 구현에서는 커넥터 호출·데이터 변환·적재를 수행한다
        return {"processed": batch_size, "failed": 0}

    def _apply_mapping(
        self,
        record: dict[str, Any],
        field_mappings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """필드 매핑 규칙을 적용하여 단일 레코드를 변환한다."""
        result: dict[str, Any] = {}
        for fm in field_mappings:
            source_field = fm.get("source_field", "")
            target_field = fm.get("target_field", "")
            transform = fm.get("transform", "direct")
            default_value = fm.get("default_value", "")

            value = record.get(source_field, default_value)

            if transform == "uppercase" and isinstance(value, str):
                value = value.upper()
            elif transform == "lowercase" and isinstance(value, str):
                value = value.lower()

            if target_field:
                result[target_field] = value

        return result
