"""Compliance 모델 단위 테스트."""

from __future__ import annotations

from datetime import date

from oneerp_compliance_app.compliance_mod.models.compliance_checklist import (
    ComplianceChecklist,
    ComplianceChecklistCreate,
)
from oneerp_compliance_app.compliance_mod.models.compliance_report import (
    ComplianceReport,
    ComplianceReportCreate,
    OverallRating,
    ReportType,
)
from oneerp_compliance_app.compliance_mod.models.data_privacy_record import (
    DataPrivacyRecord,
    DataPrivacyRecordCreate,
)
from oneerp_compliance_app.compliance_mod.models.internal_control import (
    ControlFrequency,
    ControlType,
    InternalControl,
    InternalControlCreate,
)
from oneerp_compliance_app.compliance_mod.models.regulatory_sandbox import (
    RegulatorySandbox,
    RegulatorySandboxCreate,
    SandboxType,
)
from oneerp_compliance_app.compliance_mod.models.risk_assessment import (
    RiskAssessment,
    RiskAssessmentCreate,
    RiskCategory,
)


class Test내부통제모델:
    """InternalControl 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """InternalControlCreate 스키마가 올바르게 동작한다."""
        data = InternalControlCreate(
            control_id="IC-001",
            name="구매 승인 통제",
            description="구매 금액별 승인 체계",
            control_type=ControlType.PREVENTIVE,
            risk_area="구매",
            frequency=ControlFrequency.MONTHLY,
            responsible="감사팀장",
        )
        assert data.control_type == ControlType.PREVENTIVE

    def test_문서_기본값(self) -> None:
        """InternalControl 문서의 기본값을 검��한다."""
        doc = InternalControl()
        assert doc.status == "draft"


class Test위험평가모델:
    """RiskAssessment 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """RiskAssessmentCreate 스키마가 올바르게 동작한다."""
        data = RiskAssessmentCreate(
            risk_name="데이터 유출 위험",
            risk_category=RiskCategory.COMPLIANCE,
            likelihood=3,
            impact=5,
            risk_score=15,
            owner="보안팀장",
        )
        assert data.risk_score == 15

    def test_문서_기본값(self) -> None:
        """RiskAssessment 문서의 기본값을 검증한다."""
        doc = RiskAssessment()
        assert doc.likelihood == 1
        assert doc.status == "draft"


class Test체크리스트모델:
    """ComplianceChecklist 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """ComplianceChecklistCreate 스키마가 올바르게 동작한다."""
        data = ComplianceChecklistCreate(
            name="Q1 SOX 점검",
            internal_control="IC-001",
            period="2024-Q1",
            items=[{"item": "승인 체계 확인", "result": "pass"}],
        )
        assert len(data.items) == 1

    def test_문서_기본값(self) -> None:
        """ComplianceChecklist 문서의 기본값을 검증한다."""
        doc = ComplianceChecklist()
        assert doc.status == "draft"


class Test보고서모델:
    """ComplianceReport 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """ComplianceReportCreate 스키마가 올바르게 동작한다."""
        data = ComplianceReportCreate(
            report_type=ReportType.SOX,
            period="2024-Q1",
            findings=[{"finding": "미비점 1", "severity": "low", "recommendation": "개선 필요"}],
            overall_rating=OverallRating.SATISFACTORY,
            prepared_by="감사인",
        )
        assert data.overall_rating == OverallRating.SATISFACTORY

    def test_문서_기본값(self) -> None:
        """ComplianceReport 문서의 기본값을 검증한다."""
        doc = ComplianceReport()
        assert doc.status == "draft"


class Test개인정보기록부모델:
    """DataPrivacyRecord 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """DataPrivacyRecordCreate 스키마가 올바르게 동작한다."""
        data = DataPrivacyRecordCreate(
            processing_purpose="고객 서비스 제공",
            data_categories=["이름", "연락처", "이메일"],
            data_subjects="고객",
            retention_period="5년",
            legal_basis="개인정보보호법 제15조",
            transfer_to_third_party=False,
        )
        assert len(data.data_categories) == 3

    def test_문서_기본값(self) -> None:
        """DataPrivacyRecord 문서의 기본값을 검증한다."""
        doc = DataPrivacyRecord()
        assert doc.transfer_to_third_party is False


class Test규제샌드박스모델:
    """RegulatorySandbox 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """RegulatorySandboxCreate 스키마가 올바르게 동작한다."""
        data = RegulatorySandboxCreate(
            sandbox_type=SandboxType.FINANCIAL,
            project_name="혁신 결제 서비스",
            approval_date=date(2024, 1, 1),
            expiry_date=date(2026, 12, 31),
            regulatory_body="금융위원회",
            exempted_regulations=["전자금융거래법 제28조"],
        )
        assert data.sandbox_type == SandboxType.FINANCIAL

    def test_문서_기본값(self) -> None:
        """RegulatorySandbox 문서의 기본값을 검증한다."""
        doc = RegulatorySandbox()
        assert doc.status == "draft"
