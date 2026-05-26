"""RPA 작업 큐 실행기 — 비동기 작업 처리.

작업 큐에서 pending 작업을 가져와 적절한 Runner로 실행하고
결과를 DB에 저장한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from .appium_manager import AppiumManager
from .banking_runner import BankingRunner
from .hometax_runner import HometaxRunner
from .insurance_runner import InsuranceRunner

logger = logging.getLogger(__name__)


class TaskExecutor:
    """RPA 작업 실행기."""

    def __init__(self, tenant_id: str, appium_url: str = "http://localhost:4723") -> None:
        self._tenant_id = tenant_id
        self._task_repo = Repository("rpa_tasks", tenant_id=tenant_id)
        self._result_repo = Repository("rpa_results", tenant_id=tenant_id)
        self._appium = AppiumManager(appium_url)

        # task_type -> Runner 매핑
        self._runners: dict[str, Any] = {
            "hometax_issue": self._run_hometax_issue,
            "hometax_query": self._run_hometax_query,
            "banking_balance": self._run_banking_balance,
            "banking_transactions": self._run_banking_transactions,
            "insurance_status": self._run_insurance_status,
            "insurance_payments": self._run_insurance_payments,
        }

    async def execute_task(self, task_id: str) -> dict[str, Any]:
        """작업을 실행하고 결과를 반환한다."""
        task = self._task_repo.find_by_id(task_id)
        if not task:
            msg = f"작업을 찾을 수 없습니다: {task_id}"
            raise ValueError(msg)

        task_type = task.get("task_type", "")
        runner_fn = self._runners.get(task_type)
        if not runner_fn:
            msg = f"지원하지 않는 작업 유형: {task_type}"
            raise ValueError(msg)

        # 상태 업데이트: running
        self._task_repo.update_by_id(
            task_id,
            {
                "status": "running",
                "started_at": datetime.now(tz=UTC),
            },
        )

        try:
            result = await runner_fn(task)

            # 결과 저장
            self._task_repo.update_by_id(
                task_id,
                {
                    "status": "completed",
                    "result_data": result,
                    "completed_at": datetime.now(tz=UTC),
                },
            )

            # RPAResult 기록
            result_id = generate_name("RPAR", tenant_id=self._tenant_id)
            self._result_repo.insert(
                {
                    "_id": result_id,
                    "tenant_id": self._tenant_id,
                    "task_id": task_id,
                    "step_name": task_type,
                    "success": True,
                    "data": result,
                }
            )

            return {"status": "completed", "result": result}

        except Exception as e:
            error_msg = str(e)
            logger.exception("RPA 작업 실패: %s", task_id)

            # 실패 상태 + 재시도 카운트
            retry_count = task.get("retry_count", 0) + 1
            max_retries = task.get("max_retries", 3)
            new_status = "pending" if retry_count < max_retries else "failed"

            self._task_repo.update_by_id(
                task_id,
                {
                    "status": new_status,
                    "error_message": error_msg,
                    "retry_count": retry_count,
                    "completed_at": datetime.now(tz=UTC) if new_status == "failed" else None,
                },
            )

            return {"status": new_status, "error": error_msg, "retry_count": retry_count}

    async def _run_hometax_issue(self, task: dict) -> dict:
        """홈택스 세금계산서 발급."""
        input_data = task.get("input_data", {})
        device_id = task.get("device_id", "emulator-5554")

        runner = HometaxRunner(self._appium)
        await runner.start(device_id)
        await runner.login(input_data.get("cert_password", ""))
        result = await runner.issue_tax_invoice(input_data.get("invoice_data", {}))
        await runner.stop()
        return result

    async def _run_hometax_query(self, task: dict) -> dict:
        """홈택스 세금계산서 조회."""
        input_data = task.get("input_data", {})
        device_id = task.get("device_id", "emulator-5554")

        runner = HometaxRunner(self._appium)
        await runner.start(device_id)
        await runner.login(input_data.get("cert_password", ""))
        invoices = await runner.query_tax_invoices(input_data.get("period", ""))
        await runner.stop()
        return {"invoices": invoices}

    async def _run_banking_balance(self, task: dict) -> dict:
        """은행 잔액 조회."""
        input_data = task.get("input_data", {})
        device_id = task.get("device_id", "emulator-5554")

        runner = BankingRunner(self._appium)
        await runner.start(device_id, app_package=input_data.get("app_package", ""))
        balance = await runner.get_balance(input_data.get("account", ""))
        await runner.stop()
        return balance

    async def _run_banking_transactions(self, task: dict) -> dict:
        """은행 거래내역 조회."""
        input_data = task.get("input_data", {})
        device_id = task.get("device_id", "emulator-5554")

        runner = BankingRunner(self._appium)
        await runner.start(device_id, app_package=input_data.get("app_package", ""))
        txns = await runner.get_transactions(
            input_data.get("account", ""),
            input_data.get("period", ""),
        )
        await runner.stop()
        return {"transactions": txns}

    async def _run_insurance_status(self, task: dict) -> dict:
        """보험 계약 상태 조회."""
        input_data = task.get("input_data", {})
        device_id = task.get("device_id", "emulator-5554")

        runner = InsuranceRunner(self._appium)
        await runner.start(device_id, app_package=input_data.get("app_package", ""))
        status = await runner.get_insurance_status(input_data.get("policy_number", ""))
        await runner.stop()
        return status

    async def _run_insurance_payments(self, task: dict) -> dict:
        """보험료 납부내역 조회."""
        input_data = task.get("input_data", {})
        device_id = task.get("device_id", "emulator-5554")

        runner = InsuranceRunner(self._appium)
        await runner.start(device_id, app_package=input_data.get("app_package", ""))
        payments = await runner.get_payment_history(
            input_data.get("policy_number", ""),
        )
        await runner.stop()
        return {"payments": payments}
