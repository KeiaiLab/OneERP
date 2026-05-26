"""EHS 모델 단위 테스트."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from oneerp_ehs_app.models.hazardous_material import HazardousMaterial, HazardousMaterialCreate
from oneerp_ehs_app.models.health_checkup import CheckupType, HealthCheckup, HealthCheckupCreate
from oneerp_ehs_app.models.safety_incident import (
    IncidentType,
    SafetyIncident,
    SafetyIncidentCreate,
    Severity,
)
from oneerp_ehs_app.models.safety_training import SafetyTraining, SafetyTrainingCreate, TrainingType


class Test안전사고모델:
    """SafetyIncident 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """SafetyIncidentCreate 스키마가 올바르게 동작한다."""
        data = SafetyIncidentCreate(
            incident_date=datetime(2024, 3, 1, 10, 30, tzinfo=UTC),
            location="제1공장 B동",
            incident_type=IncidentType.INJURY,
            severity=Severity.MODERATE,
            description="작업 중 손가락 절상",
            employee="EMP-001",
        )
        assert data.incident_type == IncidentType.INJURY
        assert data.severity == Severity.MODERATE

    def test_문서_기본값(self) -> None:
        """SafetyIncident 문서의 기본값을 검증한다."""
        doc = SafetyIncident()
        assert doc.status == "reported"
        assert doc.reported_to_kosha is False


class Test안전교육모델:
    """SafetyTraining 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """SafetyTrainingCreate 스키마가 올바르게 동작한다."""
        data = SafetyTrainingCreate(
            training_name="신규 입사자 안전교육",
            training_type=TrainingType.NEW_HIRE,
            legal_basis="산안법 제29조",
            target_employees=["EMP-001", "EMP-002"],
            scheduled_date=date(2024, 3, 15),
            duration_hours=Decimal(8),
        )
        assert len(data.target_employees) == 2
        assert data.duration_hours == Decimal(8)

    def test_문서_기본값(self) -> None:
        """SafetyTraining 문서의 기본값을 검증한다."""
        doc = SafetyTraining()
        assert doc.status == "planned"


class Test위험물모델:
    """HazardousMaterial 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """HazardousMaterialCreate 스키마가 올바르게 동작한다."""
        data = HazardousMaterialCreate(
            material_name="아세톤",
            cas_number="67-64-1",
            ghs_classification=["인화성 액체", "급성 독성"],
            msds_document="/docs/msds/acetone.pdf",
            storage_conditions="화기엄금, 환기시설 확보",
            emergency_contact="안전팀 02-1234-5678",
        )
        assert len(data.ghs_classification) == 2

    def test_문서_기본값(self) -> None:
        """HazardousMaterial 문서의 기본값을 검증한다."""
        doc = HazardousMaterial()
        assert doc.material_name == ""


class Test건강검진모델:
    """HealthCheckup 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """HealthCheckupCreate 스키마가 올바르게 동작한다."""
        data = HealthCheckupCreate(
            employee="EMP-001",
            checkup_type=CheckupType.GENERAL,
            scheduled_date=date(2024, 4, 1),
            hospital="서울대학교병원",
        )
        assert data.checkup_type == CheckupType.GENERAL

    def test_문서_기본값(self) -> None:
        """HealthCheckup 문서의 기본값을 검증한다."""
        doc = HealthCheckup()
        assert doc.status == "scheduled"
