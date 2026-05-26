"""SPC 관리도 서비스 — X-bar/R 관리도, Western Electric Rules, 공정능력지수.

BR-QI-SPC-001: X-bar/R 차트 중심선 CL과 관제한선 UCL/LCL 산출
BR-QI-SPC-002: Western Electric Rules 1~4 이상 패턴 자동 감지
BR-QI-SPC-003: 공정능력지수 Cp/Cpk 산출 (공정 적합성 판정)

참고:
- X-bar 관제한선: UCL/LCL = X-bar-bar +/- A2 * R-bar
- R 관제한선: UCL = D4 * R-bar, LCL = D3 * R-bar
- A2/D3/D4 상수는 부분군 크기 n=2~10 범위 지원
- Western Electric Rules는 프로세스 불안정성 조기 경고 패턴
"""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

# n=2~10 부분군 크기에 대응하는 관제한선 상수표
# 출처: ASQ Quality Engineering Handbook, ISO 7870-2
_A2_TABLE: dict[int, float] = {
    2: 1.880,
    3: 1.023,
    4: 0.729,
    5: 0.577,
    6: 0.483,
    7: 0.419,
    8: 0.373,
    9: 0.337,
    10: 0.308,
}

_D3_TABLE: dict[int, float] = {
    2: 0.0,
    3: 0.0,
    4: 0.0,
    5: 0.0,
    6: 0.0,
    7: 0.076,
    8: 0.136,
    9: 0.184,
    10: 0.223,
}

_D4_TABLE: dict[int, float] = {
    2: 3.267,
    3: 2.574,
    4: 2.282,
    5: 2.114,
    6: 2.004,
    7: 1.924,
    8: 1.864,
    9: 1.816,
    10: 1.777,
}


class SPCControlChartService:
    """SPC 통계적 공정관리 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id

    def compute_xbar_r(self, subgroups: list[list[float]]) -> dict[str, Any]:
        """부분군 리스트로부터 X-bar/R 관리도 파라미터를 산출한다.

        Args:
            subgroups: 부분군 리스트 (각 부분군은 n개 측정값)

        Returns:
            xbar_values, r_values, xbar_cl, xbar_ucl, xbar_lcl, r_cl, r_ucl, r_lcl

        Raises:
            ValueError: 부분군이 비어있거나 크기가 불일치하거나 n이 지원 범위 밖
        """
        if not subgroups:
            msg = "부분군이 비어 있습니다"
            raise ValueError(msg)

        n = len(subgroups[0])
        if any(len(g) != n for g in subgroups):
            msg = "부분군 크기가 일관되지 않습니다"
            raise ValueError(msg)

        if n not in _A2_TABLE:
            msg = f"부분군 크기 n={n} 미지원 (지원 범위: 2~10)"
            raise ValueError(msg)

        # 부분군별 평균 X-bar 과 범위 R 산출
        xbar_values = [sum(g) / n for g in subgroups]
        r_values = [max(g) - min(g) for g in subgroups]

        # 중심선 CL 산출
        xbar_cl = sum(xbar_values) / len(xbar_values)
        r_cl = sum(r_values) / len(r_values)

        # 관제한선 UCL/LCL 산출
        a2 = _A2_TABLE[n]
        d3 = _D3_TABLE[n]
        d4 = _D4_TABLE[n]

        xbar_ucl = xbar_cl + a2 * r_cl
        xbar_lcl = xbar_cl - a2 * r_cl
        r_ucl = d4 * r_cl
        r_lcl = d3 * r_cl

        logger.debug(
            "X-bar/R 산출: n=%d, 부분군=%d, X-bar-bar=%.4f, R-bar=%.4f",
            n,
            len(subgroups),
            xbar_cl,
            r_cl,
        )

        return {
            "subgroup_size": n,
            "subgroup_count": len(subgroups),
            "xbar_values": xbar_values,
            "r_values": r_values,
            "xbar_cl": xbar_cl,
            "xbar_ucl": xbar_ucl,
            "xbar_lcl": xbar_lcl,
            "r_cl": r_cl,
            "r_ucl": r_ucl,
            "r_lcl": r_lcl,
        }

    def detect_western_electric(
        self,
        points: list[float],
        *,
        center_line: float,
        sigma: float,
    ) -> list[dict[str, Any]]:
        """Western Electric Rules 1~4를 적용해 이상 패턴을 감지한다.

        - Rule 1: 한 점이 CL +/- 3sigma 밖 (3sigma 초과)
        - Rule 2: 연속 3점 중 2점이 같은 쪽 CL +/- 2sigma 밖 (Zone A)
        - Rule 3: 연속 5점 중 4점이 같은 쪽 CL +/- 1sigma 밖 (Zone B)
        - Rule 4: 연속 9점이 중심선의 같은 쪽에 위치 (트렌드)

        Args:
            points: 시간 순서대로 정렬된 측정값 리스트
            center_line: 중심선
            sigma: 1 sigma 값

        Returns:
            위반 리스트 (각 원소에 rule, index, value, reason 포함)
        """
        violations: list[dict[str, Any]] = []

        ucl_3 = center_line + 3 * sigma
        lcl_3 = center_line - 3 * sigma
        ucl_2 = center_line + 2 * sigma
        lcl_2 = center_line - 2 * sigma
        ucl_1 = center_line + sigma
        lcl_1 = center_line - sigma

        # Rule 1: 3 sigma 초과
        for i, v in enumerate(points):
            if v > ucl_3 or v < lcl_3:
                violations.append(
                    {
                        "rule": 1,
                        "index": i,
                        "value": v,
                        "reason": "3 sigma 관제한선 초과",
                    },
                )

        # Rule 2: 연속 3점 중 2점이 같은 쪽 2 sigma 밖
        for i in range(len(points) - 2):
            window = points[i : i + 3]
            above = sum(1 for v in window if v > ucl_2)
            below = sum(1 for v in window if v < lcl_2)
            if above >= 2 or below >= 2:
                violations.append(
                    {
                        "rule": 2,
                        "index": i + 2,
                        "value": points[i + 2],
                        "reason": "연속 3점 중 2점이 2 sigma 밖 (Zone A)",
                    },
                )

        # Rule 3: 연속 5점 중 4점이 같은 쪽 1 sigma 밖
        for i in range(len(points) - 4):
            window = points[i : i + 5]
            above = sum(1 for v in window if v > ucl_1)
            below = sum(1 for v in window if v < lcl_1)
            if above >= 4 or below >= 4:
                violations.append(
                    {
                        "rule": 3,
                        "index": i + 4,
                        "value": points[i + 4],
                        "reason": "연속 5점 중 4점이 1 sigma 밖 (Zone B)",
                    },
                )

        # Rule 4: 연속 9점이 같은 쪽 (편향 트렌드)
        for i in range(len(points) - 8):
            window = points[i : i + 9]
            above = all(v > center_line for v in window)
            below = all(v < center_line for v in window)
            if above or below:
                violations.append(
                    {
                        "rule": 4,
                        "index": i + 8,
                        "value": points[i + 8],
                        "reason": "연속 9점 중심선 편향",
                    },
                )

        if violations:
            logger.info(
                "SPC 이상 감지: 총 %d건 (규칙별: R1=%d, R2=%d, R3=%d, R4=%d)",
                len(violations),
                sum(1 for v in violations if v["rule"] == 1),
                sum(1 for v in violations if v["rule"] == 2),
                sum(1 for v in violations if v["rule"] == 3),
                sum(1 for v in violations if v["rule"] == 4),
            )
        return violations

    def compute_capability(
        self,
        readings: list[float],
        *,
        usl: float,
        lsl: float,
    ) -> dict[str, float]:
        """공정능력지수 Cp/Cpk를 산출한다.

        Cp = (USL - LSL) / (6 * sigma)
        Cpk = min((USL - mean) / (3 * sigma), (mean - LSL) / (3 * sigma))

        Args:
            readings: 측정값 리스트
            usl: 상한 규격 USL
            lsl: 하한 규격 LSL

        Returns:
            mean, sigma, cp, cpk 딕셔너리
        """
        if len(readings) < 2:
            msg = "공정능력지수는 최소 2개 측정값이 필요합니다"
            raise ValueError(msg)
        if usl <= lsl:
            msg = "USL은 LSL보다 커야 합니다"
            raise ValueError(msg)

        mean = sum(readings) / len(readings)
        variance = sum((x - mean) ** 2 for x in readings) / (len(readings) - 1)
        sigma = math.sqrt(variance)

        # 표준편차가 0이면 완전 관리 상태 이므로 inf 반환
        if sigma == 0:
            cp = float("inf")
            cpk = float("inf")
        else:
            cp = (usl - lsl) / (6 * sigma)
            cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

        logger.debug(
            "공정능력지수: mean=%.4f, sigma=%.4f, Cp=%.4f, Cpk=%.4f",
            mean,
            sigma,
            cp,
            cpk,
        )

        return {
            "mean": mean,
            "sigma": sigma,
            "cp": cp,
            "cpk": cpk,
        }
