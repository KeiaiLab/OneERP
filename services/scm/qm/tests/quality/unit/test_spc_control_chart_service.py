"""SPC 관리도 서비스(SPCControlChartService) 단위 테스트.

BR-QI-확장: 공정능력 관리 — X-bar/R 관리도, Western Electric Rules 이상 감지.
참고: Western Electric Rules 1~4, X-bar A2/D3/D4 상수표.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def spc_service():
    """SPCControlChartService 인스턴스를 반환한다."""
    from oneerp_qm_app.quality.services.spc_control_chart_service import SPCControlChartService

    return SPCControlChartService(tenant_id="T1")


class TestXBarR차트계산:
    """X-bar/R 관리도 계산 테스트 — BR-QI-SPC-001."""

    def test_평균_범위_중심선_계산(self, spc_service) -> None:
        """부분군별 X-bar와 R을 계산하고 CL을 산출한다."""
        # 5개 부분군, 각 부분군 크기 n=4
        subgroups = [
            [10.1, 10.2, 10.0, 10.1],
            [10.3, 10.1, 10.2, 10.0],
            [9.9, 10.0, 10.1, 10.0],
            [10.2, 10.2, 10.3, 10.1],
            [10.0, 10.1, 10.0, 9.9],
        ]
        result = spc_service.compute_xbar_r(subgroups)

        # X-bar-bar 중심선 = (10.1+10.15+10.0+10.2+10.0)/5 = 10.09
        assert result["xbar_cl"] == pytest.approx(10.09, abs=1e-4)
        # R-bar 중심선 = (0.2+0.3+0.2+0.2+0.2)/5 = 0.22
        assert result["r_cl"] == pytest.approx(0.22, abs=1e-4)
        assert len(result["xbar_values"]) == 5
        assert len(result["r_values"]) == 5

    def test_관제한선_n4(self, spc_service) -> None:
        """n=4일 때 A2=0.729, D3=0, D4=2.282 상수로 UCL/LCL을 산출한다."""
        subgroups = [
            [10.0, 10.0, 10.0, 10.0],
            [10.0, 10.0, 10.0, 10.0],
        ]
        result = spc_service.compute_xbar_r(subgroups)
        # 모두 동일값이므로 R-bar=0, UCL=LCL=CL
        assert result["xbar_ucl"] == pytest.approx(10.0)
        assert result["xbar_lcl"] == pytest.approx(10.0)
        assert result["r_ucl"] == pytest.approx(0.0)
        assert result["r_lcl"] == pytest.approx(0.0)

    def test_빈_부분군은_에러(self, spc_service) -> None:
        """부분군이 비어 있으면 ValueError."""
        with pytest.raises(ValueError, match="부분군이 비어"):
            spc_service.compute_xbar_r([])

    def test_부분군_크기_불일치는_에러(self, spc_service) -> None:
        """모든 부분군의 크기가 동일해야 한다."""
        with pytest.raises(ValueError, match="부분군 크기"):
            spc_service.compute_xbar_r([[1.0, 2.0], [1.0, 2.0, 3.0]])

    def test_지원되지_않는_n은_에러(self, spc_service) -> None:
        """n이 상수표 범위(2~10)를 벗어나면 에러."""
        single = [[1.0]]
        with pytest.raises(ValueError, match="부분군 크기"):
            spc_service.compute_xbar_r(single)


class TestWesternElectricRules:
    """Western Electric Rules 이상 감지 테스트 — BR-QI-SPC-002."""

    def test_Rule1_3sigma_초과(self, spc_service) -> None:
        """Rule 1: 어떤 점이든 3 sigma 관제한선을 벗어나면 이상."""
        points = [10.0, 10.1, 10.0, 15.0, 10.1]  # 4번째가 UCL 초과
        violations = spc_service.detect_western_electric(
            points,
            center_line=10.0,
            sigma=0.5,
        )
        rule1 = [v for v in violations if v["rule"] == 1]
        assert len(rule1) >= 1
        assert rule1[0]["index"] == 3

    def test_Rule2_2of3_2sigma(self, spc_service) -> None:
        """Rule 2: 연속 3점 중 2점이 같은 쪽 2 sigma 이상에 있으면 이상."""
        # 3점 중 2점이 CL + 2 sigma (=11.0) 이상
        points = [11.2, 10.0, 11.3]
        violations = spc_service.detect_western_electric(
            points,
            center_line=10.0,
            sigma=0.5,
        )
        rule2 = [v for v in violations if v["rule"] == 2]
        assert len(rule2) >= 1

    def test_Rule3_4of5_1sigma(self, spc_service) -> None:
        """Rule 3: 연속 5점 중 4점이 같은 쪽 1 sigma 이상에 있으면 이상."""
        points = [10.6, 10.7, 10.0, 10.8, 10.9]
        violations = spc_service.detect_western_electric(
            points,
            center_line=10.0,
            sigma=0.5,
        )
        rule3 = [v for v in violations if v["rule"] == 3]
        assert len(rule3) >= 1

    def test_Rule4_연속_9점_동일_쪽(self, spc_service) -> None:
        """Rule 4: 연속 9점이 중심선 같은 쪽에 있으면 이상(트렌드)."""
        points = [10.1, 10.2, 10.3, 10.1, 10.4, 10.2, 10.1, 10.3, 10.2]
        violations = spc_service.detect_western_electric(
            points,
            center_line=10.0,
            sigma=0.5,
        )
        rule4 = [v for v in violations if v["rule"] == 4]
        assert len(rule4) >= 1

    def test_정상_프로세스_이상_없음(self, spc_service) -> None:
        """정상 분포인 경우 이상이 감지되지 않는다."""
        # 중심선 주변에서 위/아래 번갈아
        points = [10.1, 9.9, 10.2, 9.8, 10.0, 9.9, 10.1]
        violations = spc_service.detect_western_electric(
            points,
            center_line=10.0,
            sigma=0.5,
        )
        assert violations == []


class TestCp공정능력:
    """공정능력지수 Cp/Cpk 계산 테스트 — BR-QI-SPC-003."""

    def test_Cp_계산(self, spc_service) -> None:
        """Cp = (USL - LSL) / (6 * sigma)."""
        result = spc_service.compute_capability(
            readings=[10.0, 10.1, 9.9, 10.0, 10.1],
            usl=11.0,
            lsl=9.0,
        )
        # sigma는 표본 표준편차, Cp = 2.0 / (6 * sigma)
        assert "cp" in result
        assert "cpk" in result
        assert result["cp"] > 0
        assert result["mean"] == pytest.approx(10.02, abs=1e-2)

    def test_Cpk는_CL_편차를_반영(self, spc_service) -> None:
        """Cpk = min((USL-mean)/(3*sigma), (mean-LSL)/(3*sigma))."""
        # 중심이 LSL 쪽으로 치우친 측정값
        result = spc_service.compute_capability(
            readings=[10.5, 10.6, 10.4, 10.5, 10.5],
            usl=11.0,
            lsl=9.0,
        )
        assert result["cpk"] <= result["cp"]
