"""Fleet 모델 단위 테스트."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from oneerp_logistics_app.fleet.models.fuel_entry import (
    FuelEntry,
    FuelEntryCreate,
)
from oneerp_logistics_app.fleet.models.fuel_entry import (
    FuelType as FuelEntryFuelType,
)
from oneerp_logistics_app.fleet.models.vehicle import (
    FuelType as VehicleFuelType,
)
from oneerp_logistics_app.fleet.models.vehicle import (
    Vehicle,
    VehicleCreate,
    VehicleStatus,
)
from oneerp_logistics_app.fleet.models.vehicle_assignment import (
    AssignmentType,
    VehicleAssignment,
    VehicleAssignmentCreate,
)
from oneerp_logistics_app.fleet.models.vehicle_log import VehicleLog, VehicleLogCreate
from oneerp_logistics_app.fleet.models.vehicle_maintenance import (
    MaintenanceType,
    VehicleMaintenance,
    VehicleMaintenanceCreate,
)


class Test차량모델:
    """Vehicle 모델 테스트."""

    def test_차량_생성_스키마(self) -> None:
        """VehicleCreate 스키마가 올바르게 동작한다."""
        data = VehicleCreate(
            vehicle_no="12가 3456",
            vehicle_name="소나타",
            make="현대",
            model="소나타",
            year=2024,
            fuel_type=VehicleFuelType.GASOLINE,
            acquisition_date=date(2024, 1, 1),
            acquisition_cost=Decimal(30000000),
            company="C001",
        )
        assert data.vehicle_no == "12가 3456"
        assert data.acquisition_cost == Decimal(30000000)

    def test_차량_문서_기본값(self) -> None:
        """Vehicle 문서의 기본값을 검증한다."""
        doc = Vehicle()
        assert doc.status == VehicleStatus.ACTIVE
        assert doc.odometer == Decimal(0)


class Test차량배정모델:
    """VehicleAssignment 모델 테스트."""

    def test_배정_생성(self) -> None:
        """VehicleAssignmentCreate 스키마 동작을 검증한다."""
        data = VehicleAssignmentCreate(
            vehicle="VH-0001",
            employee="EMP-001",
            start_date=date(2024, 3, 1),
            assignment_type=AssignmentType.PERMANENT,
        )
        assert data.assignment_type == AssignmentType.PERMANENT

    def test_배정_문서_기본값(self) -> None:
        """VehicleAssignment 문서의 기본값을 검증한다."""
        doc = VehicleAssignment()
        assert doc.status == "active"


class Test운행기록모델:
    """VehicleLog 모델 테스트."""

    def test_운행기록_생성(self) -> None:
        """VehicleLogCreate 스키마 동작을 검증한다."""
        data = VehicleLogCreate(
            vehicle="VH-0001",
            driver="EMP-001",
            log_date=date(2024, 3, 1),
            start_odometer=Decimal(10000),
            end_odometer=Decimal(10050),
            distance=Decimal(50),
            purpose="거래처 방문",
        )
        assert data.distance == Decimal(50)

    def test_운행기록_문서_기본값(self) -> None:
        """VehicleLog 문서의 기본값을 검증한다."""
        doc = VehicleLog()
        assert doc.distance == Decimal(0)


class Test주유기록모델:
    """FuelEntry 모델 테스트."""

    def test_주유기록_생성(self) -> None:
        """FuelEntryCreate 스키마 동작을 검증한다."""
        data = FuelEntryCreate(
            vehicle="VH-0001",
            entry_date=date(2024, 3, 1),
            fuel_type=FuelEntryFuelType.GASOLINE,
            quantity=Decimal(50),
            amount=Decimal(85000),
            odometer=Decimal(10050),
        )
        assert data.amount == Decimal(85000)

    def test_주유기록_문서_기본값(self) -> None:
        """FuelEntry 문서의 기본값을 검증한다."""
        doc = FuelEntry()
        assert doc.quantity == Decimal(0)


class Test차량정비모델:
    """VehicleMaintenance 모델 테스트."""

    def test_정비_생성(self) -> None:
        """VehicleMaintenanceCreate 스키마 동작을 검증한다."""
        data = VehicleMaintenanceCreate(
            vehicle="VH-0001",
            maintenance_type=MaintenanceType.OIL_CHANGE,
            maintenance_date=date(2024, 3, 1),
            description="엔진 오일 교환",
            cost=Decimal(80000),
        )
        assert data.cost == Decimal(80000)

    def test_정비_문서_기본값(self) -> None:
        """VehicleMaintenance 문서의 기본값을 검증한다."""
        doc = VehicleMaintenance()
        assert doc.status == "draft"
        assert doc.cost == Decimal(0)
