"""법정의무교육 관리 서비스 — 한국 법정의무교육 이수 점검."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MandatoryEducation:
    """법정의무교육 정의."""

    name: str
    law_reference: str
    target: str
    frequency: str


# 한국 법정의무교육 목록
MANDATORY_EDUCATIONS: list[MandatoryEducation] = [
    MandatoryEducation(
        name="산업안전보건교육",
        law_reference="산안법 제29조",
        target="전 직원",
        frequency="분기/반기",
    ),
    MandatoryEducation(
        name="성희롱 예방교육",
        law_reference="남녀고용평등법 제13조",
        target="전 직원",
        frequency="연 1회",
    ),
    MandatoryEducation(
        name="개인정보보호 교육",
        law_reference="개인정보보호법 제28조",
        target="전 직원",
        frequency="연 1회",
    ),
    MandatoryEducation(
        name="장애인 인식개선 교육",
        law_reference="장애인고용촉진법 제5조의2",
        target="전 직원",
        frequency="연 1회",
    ),
    MandatoryEducation(
        name="직장 내 괴롭힘 예방교육",
        law_reference="근로기준법 제93조의2",
        target="전 직원",
        frequency="연 1회",
    ),
    MandatoryEducation(
        name="퇴직연금 교육",
        law_reference="근로자퇴직급여보장법 제32조",
        target="가입 직원",
        frequency="연 1회",
    ),
]


def get_mandatory_education_list() -> list[MandatoryEducation]:
    """한국 법정의무교육 목록을 반환한다."""
    return MANDATORY_EDUCATIONS


def check_completion_status(
    completed_courses: list[str],
) -> list[dict[str, object]]:
    """법정의무교육 이수 현황을 점검한다.

    Args:
        completed_courses: 이수 완료된 교육명 목록.

    Returns:
        각 법정의무교육의 이수 여부 목록.
    """
    return [
        {
            "name": edu.name,
            "law_reference": edu.law_reference,
            "completed": edu.name in completed_courses,
        }
        for edu in MANDATORY_EDUCATIONS
    ]
