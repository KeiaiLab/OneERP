"""CAPA 효과성 검증 서비스(CAPAEffectivenessService) 단위 테스트.

BR-QI-CAPA-EXT-001: 8D Report 단계별 진행 관리 (D0~D8)
BR-QI-CAPA-EXT-002: 마감 후 재발 여부 추적 (6/8개월 effectiveness check)
BR-QI-CAPA-EXT-003: 효과성 검증 실패 시 CAPA 재개 (reopen)
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _make_service():
    """CAPAEffectivenessService 인스턴스와 mock repo를 생성한다."""
    with patch(
        "oneerp_qm_app.quality.services.capa_effectiveness_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _factory
        from oneerp_qm_app.quality.services.capa_effectiveness_service import (
            CAPAEffectivenessService,
        )

        svc = CAPAEffectivenessService(tenant_id="T1")
    return svc, repos


class Test8DReport:
    """8D Report 단계 진행 테스트 — BR-QI-CAPA-EXT-001."""

    def test_D0부터_D8까지_모든_단계가_정의된다(self) -> None:
        """8D 단계 상수가 D0~D8로 정의되어 있다."""
        from oneerp_qm_app.quality.services.capa_effectiveness_service import EIGHT_D_STEPS

        assert EIGHT_D_STEPS[0] == "D0"
        assert "D1" in EIGHT_D_STEPS
        assert "D8" in EIGHT_D_STEPS
        assert len(EIGHT_D_STEPS) == 9

    def test_단계_진행은_순차여야_한다(self) -> None:
        """D2에서 D5로 건너뛸 수 없다 — 반드시 D3, D4 순서."""
        svc, repos = _make_service()
        capa_repo = repos["capas"]
        capa_repo.find_by_id.return_value = {
            "_id": "CAPA-001",
            "current_8d_step": "D2",
            "corrective_action": "중간 조치",
        }

        with pytest.raises(ValueError, match="단계 순서"):
            svc.advance_8d_step("CAPA-001", "D5")

    def test_다음_단계로_정상_진행(self) -> None:
        """현재 단계가 D2일 때 D3으로 정상 진행."""
        svc, repos = _make_service()
        capa_repo = repos["capas"]
        capa_repo.find_by_id.return_value = {
            "_id": "CAPA-001",
            "current_8d_step": "D2",
        }

        result = svc.advance_8d_step("CAPA-001", "D3", notes="문제 봉쇄 조치 수행")

        assert result["capa_id"] == "CAPA-001"
        assert result["current_step"] == "D3"
        capa_repo.update_by_id.assert_called_once()
        call_args = capa_repo.update_by_id.call_args[0]
        assert call_args[1]["current_8d_step"] == "D3"
        # 진행 이력 기록 확인
        assert "step_history" in call_args[1]

    def test_존재하지_않는_CAPA는_에러(self) -> None:
        """존재하지 않는 CAPA에 단계 진행 시도 시 에러."""
        svc, repos = _make_service()
        repos["capas"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            svc.advance_8d_step("CAPA-999", "D3")

    def test_D8_도달_시_자동_마감(self) -> None:
        """D8 단계 도달 시 is_closed=True로 자동 마감된다."""
        svc, repos = _make_service()
        capa_repo = repos["capas"]
        capa_repo.find_by_id.return_value = {
            "_id": "CAPA-001",
            "current_8d_step": "D7",
            "corrective_action": "조치 완료",
        }

        result = svc.advance_8d_step("CAPA-001", "D8")

        assert result["is_closed"] is True
        update_payload = capa_repo.update_by_id.call_args[0][1]
        assert update_payload["is_closed"] is True


class TestEffectivenessCheck:
    """효과성 검증 스케줄링 테스트 — BR-QI-CAPA-EXT-002."""

    def test_마감_CAPA의_효과성_체크_예정일_계산(self) -> None:
        """마감일 + 6개월(기본) = 효과성 검증 예정일."""
        svc, repos = _make_service()
        close_date = date(2026, 1, 15)
        repos["capas"].find_by_id.return_value = {
            "_id": "CAPA-001",
            "is_closed": True,
            "closed_at": close_date,
        }

        result = svc.schedule_effectiveness_check("CAPA-001", check_after_months=6)

        # 약 6개월 후 (180일 기준)
        expected_min = close_date + timedelta(days=170)
        expected_max = close_date + timedelta(days=190)
        assert expected_min <= result["check_date"] <= expected_max

    def test_미마감_CAPA는_예정_불가(self) -> None:
        """is_closed=False 인 CAPA에 대한 효과성 체크는 스케줄 불가."""
        svc, repos = _make_service()
        repos["capas"].find_by_id.return_value = {
            "_id": "CAPA-001",
            "is_closed": False,
        }

        with pytest.raises(ValueError, match="마감된 CAPA만"):
            svc.schedule_effectiveness_check("CAPA-001")

    def test_재발_없음_검증_통과(self) -> None:
        """검증 기간 내 동일 NC가 발생하지 않았으면 effectiveness_verified=True."""
        svc, repos = _make_service()
        repos["capas"].find_by_id.return_value = {
            "_id": "CAPA-001",
            "is_closed": True,
            "root_cause": "공정 B 불량",
            "closed_at": date(2026, 1, 15),
        }
        # 재발 NC 0건
        repos["non_conformances"].count.return_value = 0

        result = svc.verify_effectiveness("CAPA-001")

        assert result["effectiveness_verified"] is True
        assert result["recurrence_count"] == 0

    def test_재발_발생시_검증_실패(self) -> None:
        """검증 기간 내 동일 원인의 NC가 1건 이상이면 검증 실패 + CAPA 재개."""
        svc, repos = _make_service()
        repos["capas"].find_by_id.return_value = {
            "_id": "CAPA-001",
            "is_closed": True,
            "root_cause": "공정 B 불량",
            "closed_at": date(2026, 1, 15),
        }
        repos["non_conformances"].count.return_value = 3

        result = svc.verify_effectiveness("CAPA-001")

        assert result["effectiveness_verified"] is False
        assert result["recurrence_count"] == 3
        # CAPA 재개 확인 — is_closed=False로 업데이트되어야 함
        repos["capas"].update_by_id.assert_called()
        update_payload = repos["capas"].update_by_id.call_args[0][1]
        assert update_payload["is_closed"] is False
        assert update_payload["effectiveness_verified"] is False
