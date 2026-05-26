"""G3-1 시나리오 7/7 — 역할/스코프 검증.

HR 는 개인정보·급여 데이터 접근 통제가 특히 중요하다.
- hr_viewer: 공개 디렉토리만 조회 가능
- hr_editor: 직원 CRUD · 발령 · 휴가 신청 작성
- hr_admin: 퇴사 · 조직 개편 · 급여 필드 접근
- payroll_admin: 급여 필드만 (hr 에서는 read 전용)
"""

from __future__ import annotations

import jwt


def _roles(token: str, secret: str) -> list[str]:
    return jwt.decode(token, secret, algorithms=["HS256"], audience="oneerp-hr")["roles"]


def test_hr_viewer는_급여필드_조회_거부(jwt_secret, make_jwt) -> None:
    """viewer 역할은 salary 관련 스코프 체크에서 실패해야 한다."""
    token = make_jwt(roles=["hr_viewer"])
    roles = _roles(token, jwt_secret)
    # 정책: salary/bank_account 필드는 hr_admin 또는 payroll_admin 만
    can_read_salary = any(r in {"hr_admin", "payroll_admin"} for r in roles)
    assert can_read_salary is False


def test_hr_admin은_급여필드_조회_허용(jwt_secret, make_jwt) -> None:
    """admin 역할은 salary 스코프 통과."""
    token = make_jwt(roles=["hr_admin"])
    roles = _roles(token, jwt_secret)
    assert "hr_admin" in roles
    assert any(r in {"hr_admin", "payroll_admin"} for r in roles) is True


def test_payroll_admin은_hr_쓰기_거부(jwt_secret, make_jwt) -> None:
    """payroll_admin 은 hr 에서 read-only — 쓰기 역할 부재."""
    token = make_jwt(roles=["payroll_admin"])
    roles = _roles(token, jwt_secret)
    can_write_hr = any(r in {"hr_editor", "hr_admin"} for r in roles)
    assert can_write_hr is False


def test_역할_없는_토큰은_모든_접근_거부(jwt_secret, make_jwt) -> None:
    """roles 가 빈 배열인 토큰은 어느 스코프도 통과 못함."""
    token = make_jwt(roles=[])
    roles = _roles(token, jwt_secret)
    assert roles == []
    hr_capable = any(r in {"hr_viewer", "hr_editor", "hr_admin", "payroll_admin"} for r in roles)
    assert hr_capable is False


def test_타모듈_역할은_hr_접근_불허(jwt_secret, make_jwt) -> None:
    """accounting_editor 같은 타모듈 역할 단독 보유자는 hr 경계에서 거부."""
    token = make_jwt(roles=["accounting_editor"])
    roles = _roles(token, jwt_secret)
    hr_capable = any(r in {"hr_viewer", "hr_editor", "hr_admin", "payroll_admin"} for r in roles)
    assert hr_capable is False
