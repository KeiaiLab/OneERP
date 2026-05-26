"""설비보전 모델 단위 테스트."""

from __future__ import annotations

from datetime import date
from decimal import Decimal


class Test설비모델:
    """Equipment 모델 테스트."""

    def test_기본값_생성(self) -> None:
        """기본값으로 Equipment 인스턴스를 생성한다."""
        from oneerp_qm_app.maintenance.models.equipment import Equipment, EquipmentStatus

        eq = Equipment()

        assert eq.equipment_name == ""
        assert eq.status == EquipmentStatus.ACTIVE
        assert eq.purchase_cost == Decimal(0)
        assert eq.failure_count == 0

    def test_커스텀_값_생성(self) -> None:
        """커스텀 값으로 Equipment 인스턴스를 생성한다."""
        from oneerp_qm_app.maintenance.models.equipment import Equipment, EquipmentStatus

        eq = Equipment(
            equipment_name="1호 프레스",
            equipment_code="PR-001",
            status=EquipmentStatus.UNDER_MAINTENANCE,
            purchase_cost=Decimal(50000000),
            criticality="high",
            installation_date=date(2024, 1, 15),
        )

        assert eq.equipment_name == "1호 프레스"
        assert eq.status == EquipmentStatus.UNDER_MAINTENANCE
        assert eq.purchase_cost == Decimal(50000000)
        assert eq.installation_date == date(2024, 1, 15)


class Test작업지시모델:
    """WorkOrder 모델 테스트."""

    def test_기본값_생성(self) -> None:
        """기본값으로 WorkOrder 인스턴스를 생성한다."""
        from oneerp_qm_app.maintenance.models.work_order import (
            WorkOrder,
            WorkOrderPriority,
            WorkOrderStatus,
        )

        wo = WorkOrder()

        assert wo.status == WorkOrderStatus.DRAFT
        assert wo.priority == WorkOrderPriority.MEDIUM
        assert wo.total_cost == Decimal(0)
        assert wo.labor_hours == 0.0
        assert wo.spare_parts_used == []

    def test_예비자재_사용_기록(self) -> None:
        """작업지시에 예비자재 사용을 기록한다."""
        from oneerp_qm_app.maintenance.models.work_order import SparePartUsage, WorkOrder

        wo = WorkOrder(
            title="모터 교체",
            spare_parts_used=[
                SparePartUsage(
                    spare_part_id="MSP-001",
                    part_name="베어링",
                    qty_used=2,
                    unit_cost=Decimal(15000),
                ),
            ],
        )

        assert len(wo.spare_parts_used) == 1
        assert wo.spare_parts_used[0].part_name == "베어링"
        assert wo.spare_parts_used[0].unit_cost == Decimal(15000)


class Test고장신고모델:
    """BreakdownReport 모델 테스트."""

    def test_기본값_생성(self) -> None:
        """기본값으로 BreakdownReport 인스턴스를 생성한다."""
        from oneerp_qm_app.maintenance.models.breakdown_report import (
            BreakdownReport,
            BreakdownReportStatus,
            BreakdownSeverity,
        )

        br = BreakdownReport()

        assert br.severity == BreakdownSeverity.MAJOR
        assert br.status == BreakdownReportStatus.REPORTED
        assert br.work_order_id == ""


class Test점검체크리스트모델:
    """InspectionChecklist 모델 테스트."""

    def test_체크리스트_항목_포함(self) -> None:
        """체크리스트 항목을 포함하여 생성한다."""
        from oneerp_qm_app.maintenance.models.inspection_checklist import (
            ChecklistItem,
            InspectionChecklist,
        )

        cl = InspectionChecklist(
            checklist_name="일일 점검표",
            items=[
                ChecklistItem(
                    idx=1,
                    item_name="오일 레벨 확인",
                    acceptance_criteria="정상 범위 내",
                    is_required=True,
                ),
                ChecklistItem(
                    idx=2,
                    item_name="이상 소음 확인",
                    acceptance_criteria="소음 없음",
                ),
            ],
        )

        assert len(cl.items) == 2
        assert cl.items[0].item_name == "오일 레벨 확인"
        assert cl.items[1].is_required is True


class Test예방보전계획모델:
    """PreventiveMaintenancePlan 모델 테스트."""

    def test_기본_주기_30일(self) -> None:
        """기본 점검 주기는 30일이다."""
        from oneerp_qm_app.maintenance.models.preventive_maintenance_plan import (
            PreventiveMaintenancePlan,
        )

        plan = PreventiveMaintenancePlan(
            plan_name="월간 점검",
            equipment_id="EQ-001",
        )

        assert plan.interval_days == 30
        assert plan.is_active is True
        assert plan.last_execution_date is None


class Test설비가동율모델:
    """EquipmentAvailability 모델 테스트."""

    def test_가동율_계산용_필드(self) -> None:
        """가동율 계산에 필요한 필드가 모두 존재한다."""
        from oneerp_qm_app.maintenance.models.equipment_availability import EquipmentAvailability

        ea = EquipmentAvailability(
            equipment_id="EQ-001",
            total_hours=720.0,
            operating_hours=680.0,
            downtime_hours=40.0,
            planned_downtime_hours=30.0,
            unplanned_downtime_hours=10.0,
            failure_count=2,
            availability_rate=94.4,
            mtbf_hours=340.0,
            mttr_hours=5.0,
        )

        assert ea.availability_rate == 94.4
        assert ea.mtbf_hours == 340.0
        assert ea.mttr_hours == 5.0


class Test보전예비자재모델:
    """MaintenanceSparePart 모델 테스트."""

    def test_재고_기본값(self) -> None:
        """예비자재 재고 기본값을 확인한다."""
        from oneerp_qm_app.maintenance.models.maintenance_spare_part import MaintenanceSparePart

        sp = MaintenanceSparePart(part_name="베어링 6205")

        assert sp.qty_on_hand == 0
        assert sp.reorder_level == 0
        assert sp.unit_cost == Decimal(0)
        assert sp.compatible_equipment_ids == []
