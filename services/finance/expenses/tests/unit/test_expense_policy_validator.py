"""경비 정책 검증 서비스(ExpensePolicyValidator) 단위 테스트 — BR-EXP-NEW-016.

한국 경비처리 표준(법인카드/개인카드/식대/복리후생비) 기반 검증:
- 유형별 1건당 한도 초과 여부
- 영수증/증빙 필수 여부 (한도 이상 경비)
- 부가세 매입세액공제 가능성 (사업 관련 여부)
- 면세 가맹점(병원/학원) 공제 불가 경고
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """ExpensePolicyValidator와 mock repo를 생성한다."""
    with patch("oneerp_expenses_app.services.expense_policy_validator.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_expenses_app.services.expense_policy_validator import ExpensePolicyValidator

        validator = ExpensePolicyValidator(tenant_id="test-tenant")

    return validator, repos.get("expense_types", MagicMock())


class Test정책검증_한도:
    """경비 1건당 한도 초과 검증."""

    def test_식비_한도_이내_통과(self) -> None:
        """식비 기본 한도(50,000원) 이내는 통과해야 한다."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="식비",
            amount=30_000,
            has_receipt=True,
            merchant="김밥천국",
        )

        assert result["valid"] is True
        assert result["violations"] == []

    def test_식비_한도_초과_경고(self) -> None:
        """식비 한도 초과 시 위반 목록에 기록된다."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="식비",
            amount=80_000,
            has_receipt=True,
            merchant="호텔뷔페",
        )

        assert result["valid"] is False
        assert any("한도" in v["message"] for v in result["violations"])
        assert any(v["code"] == "LIMIT_EXCEEDED" for v in result["violations"])

    def test_교통비_한도_이내_통과(self) -> None:
        """교통비 기본 한도(100,000원) 이내는 통과한다."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="교통비",
            amount=52_300,
            has_receipt=True,
            merchant="카카오택시",
        )

        assert result["valid"] is True

    def test_교통비_고액_한도_초과(self) -> None:
        """교통비 한도 초과(150,000원)는 경고 발생."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="교통비",
            amount=150_000,
            has_receipt=True,
            merchant="고급택시",
        )

        assert result["valid"] is False
        assert any(v["code"] == "LIMIT_EXCEEDED" for v in result["violations"])


class Test정책검증_영수증:
    """영수증 필수 여부 검증."""

    def test_소액_영수증_없어도_통과(self) -> None:
        """소액(30,000원 미만)은 영수증 없어도 통과한다."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="식비",
            amount=25_000,
            has_receipt=False,
            merchant="편의점",
        )

        assert result["valid"] is True

    def test_고액_영수증_필수_위반(self) -> None:
        """30,000원 이상은 영수증 없으면 위반."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="식비",
            amount=35_000,
            has_receipt=False,
            merchant="한식당",
        )

        assert result["valid"] is False
        assert any(v["code"] == "RECEIPT_REQUIRED" for v in result["violations"])

    def test_고액_영수증_있으면_통과(self) -> None:
        """30,000원 이상이어도 영수증 있으면 해당 위반 없음."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="식비",
            amount=35_000,
            has_receipt=True,
            merchant="한식당",
        )

        # 한도 초과만 없으면 RECEIPT_REQUIRED 위반은 포함되지 않는다
        violation_codes = [v["code"] for v in result["violations"]]
        assert "RECEIPT_REQUIRED" not in violation_codes


class Test정책검증_부가세공제:
    """부가세 매입세액공제 가능성 판정 (한국 국세청 기준)."""

    def test_식대_일반식당_공제가능(self) -> None:
        """일반 식당 식대는 복리후생비로 공제 가능하다."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="식비",
            amount=20_000,
            has_receipt=True,
            merchant="식당A",
        )

        assert result["vat_deductible"] is True

    def test_면세가맹점_공제불가(self) -> None:
        """병원/의원 등 면세 가맹점은 매입세액공제 불가 경고."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="의료비",
            amount=50_000,
            has_receipt=True,
            merchant="OO병원",
        )

        assert result["vat_deductible"] is False
        assert any(v["code"] == "VAT_NOT_DEDUCTIBLE" for v in result["violations"])

    def test_접대비_공제불가_경고(self) -> None:
        """접대비(기업업무추진비)는 매입세액공제 불가."""
        validator, _type_repo = _make_service()

        result = validator.validate_claim(
            expense_type="접대비",
            amount=100_000,
            has_receipt=True,
            merchant="룸살롱",
        )

        assert result["vat_deductible"] is False
        assert any(v["code"] == "VAT_NOT_DEDUCTIBLE" for v in result["violations"])


class Test정책검증_일괄:
    """여러 경비 항목 일괄 검증."""

    def test_일괄_검증_요약(self) -> None:
        """여러 항목 일괄 검증 시 전체 요약과 개별 결과 반환."""
        validator, _type_repo = _make_service()

        items = [
            {"expense_type": "식비", "amount": 20_000, "has_receipt": True, "merchant": "식당A"},
            {"expense_type": "식비", "amount": 80_000, "has_receipt": True, "merchant": "호텔"},
            {"expense_type": "교통비", "amount": 15_000, "has_receipt": False, "merchant": "버스"},
        ]

        result = validator.validate_claim_items(items=items)

        assert result["total_items"] == 3
        # 1번만 통과 (2번은 한도 초과, 3번은 통과)
        assert result["valid_count"] >= 1
        assert len(result["results"]) == 3

    def test_빈_항목_에러(self) -> None:
        """빈 항목 목록은 400 에러."""
        validator, _type_repo = _make_service()

        with pytest.raises(OneERPError, match="bad_request"):
            validator.validate_claim_items(items=[])
