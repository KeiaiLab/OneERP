"""법정의무교육 서비스 테스트."""

from __future__ import annotations

from oneerp_learning_app.lms.services.mandatory_education_service import (
    check_completion_status,
    get_mandatory_education_list,
)


def test_법정의무교육_목록_조회() -> None:
    """법정의무교육 목록이 6개임을 확인한다."""
    educations = get_mandatory_education_list()
    assert len(educations) == 6
    names = [e.name for e in educations]
    assert "산업안전보건교육" in names
    assert "성희롱 예방교육" in names


def test_이수현황_점검_전체미이수() -> None:
    """이수 완료된 교육이 없을 때 모두 미이수 상태를 반환한다."""
    result = check_completion_status([])
    assert len(result) == 6
    assert all(not item["completed"] for item in result)


def test_이수현황_점검_부분이수() -> None:
    """일부 교육만 이수했을 때 올바른 상태를 반환한다."""
    result = check_completion_status(["산업안전보건교육", "성희롱 예방교육"])
    completed = [item for item in result if item["completed"]]
    assert len(completed) == 2
