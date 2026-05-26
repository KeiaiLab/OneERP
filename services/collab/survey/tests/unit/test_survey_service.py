"""설문 서비스 단위 테스트.

UT-SVY-001~016, UT-SVY-021~025: 설문 생성/배포/응답/집계/조건부 로직/템플릿 테스트.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_survey_app.models.survey import Survey, SurveyType
from oneerp_survey_app.models.survey_question import QuestionType, SurveyQuestion
from oneerp_survey_app.services.survey_service import SurveyService

from .conftest import make_cursor


class TestSurveyCreation:
    """설문 생성 테스트."""

    def test_설문_생성_기본(self, mock_collection: MagicMock) -> None:
        """UT-SVY-001: 설문 생성 시 status=draft."""
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = MagicMock(inserted_id="SVY-T1-00001")

        survey = Survey(title="직원 만족도", survey_type=SurveyType.SURVEY)
        assert survey.status == "draft"
        assert survey.response_count == 0


class TestQuestionCreation:
    """질문 추가 테스트."""

    def test_객관식_질문_추가(self, mock_collection: MagicMock) -> None:
        """UT-SVY-002: 객관식 질문에 options 포함."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "draft",
            "tenant_id": "T1",
        }
        mock_collection.insert_one.return_value = MagicMock()

        svc = SurveyService("T1")
        result = svc.add_question(
            "SVY-T1-00001",
            {
                "question_text": "이직 의향?",
                "question_type": "single_choice",
                "required": True,
                "order": 1,
                "options": [
                    {"option_id": "opt-yes", "text": "��", "order": 1},
                    {"option_id": "opt-no", "text": "아니오", "order": 2},
                ],
            },
        )
        assert result["question_text"] == "이직 의향?"
        assert len(result["options"]) == 2

    def test_척도_질문_추가(self, mock_collection: MagicMock) -> None:
        """UT-SVY-003: 척도 질문에 scale_min/max 포함."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "draft",
            "tenant_id": "T1",
        }
        mock_collection.insert_one.return_value = MagicMock()

        svc = SurveyService("T1")
        result = svc.add_question(
            "SVY-T1-00001",
            {
                "question_text": "만족도 (1~5)",
                "question_type": "scale",
                "required": True,
                "order": 1,
                "scale_min": 1,
                "scale_max": 5,
            },
        )
        assert result["scale_min"] == 1
        assert result["scale_max"] == 5

    def test_매트릭스_질문_추가(self, mock_collection: MagicMock) -> None:
        """UT-SVY-004: 매트릭스 질문에 rows/columns 포함."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "draft",
            "tenant_id": "T1",
        }
        mock_collection.insert_one.return_value = MagicMock()

        svc = SurveyService("T1")
        result = svc.add_question(
            "SVY-T1-00001",
            {
                "question_text": "부서별 만족도",
                "question_type": "matrix",
                "required": True,
                "order": 1,
                "matrix_rows": ["팀 분위기", "업무 강도", "보상"],
                "matrix_columns": ["매우 불만", "불만", "보통", "만족", "매우 만족"],
            },
        )
        assert len(result["matrix_rows"]) == 3
        assert len(result["matrix_columns"]) == 5

    def test_NPS_질문_추가(self, mock_collection: MagicMock) -> None:
        """UT-SVY-005: NPS 질문 생성."""
        q = SurveyQuestion(
            question_text="추천지수",
            question_type=QuestionType.NPS,
            required=True,
            order=1,
            scale_min=0,
            scale_max=10,
        )
        assert q.question_type == "nps"
        assert q.scale_min == 0
        assert q.scale_max == 10

    def test_조건부_로직_설정(self, mock_collection: MagicMock) -> None:
        """UT-SVY-006: logic_rules 저장."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "draft",
            "tenant_id": "T1",
        }
        mock_collection.insert_one.return_value = MagicMock()

        svc = SurveyService("T1")
        result = svc.add_question(
            "SVY-T1-00001",
            {
                "question_text": "이직 의향?",
                "question_type": "single_choice",
                "required": True,
                "order": 5,
                "options": [
                    {"option_id": "opt-yes", "text": "예", "order": 1},
                    {"option_id": "opt-no", "text": "아니오", "order": 2},
                ],
                "logic_rules": [
                    {
                        "condition_option_id": "opt-yes",
                        "action": "jump_to",
                        "target_question_id": "SQ-006",
                    },
                    {"condition_option_id": "opt-no", "action": "skip", "target_question_id": None},
                ],
            },
        )
        assert len(result["logic_rules"]) == 2


class TestSurveyPublish:
    """설문 배포 테스트."""

    def test_설문_배포_성공(self, mock_collection: MagicMock) -> None:
        """UT-SVY-007: draft → active 전이."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "draft",
            "tenant_id": "T1",
        }
        mock_collection.count_documents.return_value = 3
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = SurveyService("T1")
        result = svc.publish_survey("SVY-T1-00001")
        assert result["status"] == "active"

    def test_설문_배포_질문_없음(self, mock_collection: MagicMock) -> None:
        """UT-SVY-008: 질문 없이 배포 시 ERR-SVY-081."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "draft",
            "tenant_id": "T1",
        }
        mock_collection.count_documents.return_value = 0

        svc = SurveyService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.publish_survey("SVY-T1-00001")
        assert exc_info.value.error == "ERR-SVY-081"


class TestSurveyResponse:
    """설문 응답 테스트."""

    def test_기명_응답_제출(self, mock_collection: MagicMock) -> None:
        """UT-SVY-009: 기명 응답 시 respondent_id 포함."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "active",
            "anonymity": "named",
            "allow_multiple": False,
            "starts_at": datetime.now(tz=UTC) - timedelta(hours=1),
            "tenant_id": "T1",
        }
        # find_many 호출 순서:
        # 1) 중복 응답 확인 → 빈 결과
        # 2) 필수 질문 조회 → 빈 결과
        mock_collection.find.side_effect = [make_cursor([]), make_cursor([])]
        mock_collection.insert_one.return_value = MagicMock()
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = SurveyService("T1")
        result = svc.submit_response(
            "SVY-T1-00001",
            {
                "respondent_id": "EMP-001",
                "respondent_department": "영업팀",
                "answers": [
                    {"question_id": "SQ-001", "scale_value": 4},
                ],
            },
        )
        assert result["respondent_id"] == "EMP-001"
        assert result["survey_id"] == "SVY-T1-00001"

    def test_익명_응답_제출(self, mock_collection: MagicMock) -> None:
        """UT-SVY-010: 익명 응답 시 respondent_id=null."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "active",
            "anonymity": "anonymous",
            "allow_multiple": True,
            "starts_at": datetime.now(tz=UTC) - timedelta(hours=1),
            "tenant_id": "T1",
        }
        # allow_multiple=True이므로 중복 체크 안 함 → 필수 질문 조회만
        mock_collection.find.return_value = make_cursor([])
        mock_collection.insert_one.return_value = MagicMock()
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = SurveyService("T1")
        result = svc.submit_response(
            "SVY-T1-00001",
            {
                "respondent_id": "EMP-001",
                "respondent_department": "영업팀",
                "answers": [],
            },
        )
        assert result["respondent_id"] is None

    def test_중복_응답_거부(self, mock_collection: MagicMock) -> None:
        """UT-SVY-011: allow_multiple=false일 때 중복 응답 ERR-SVY-050."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "active",
            "anonymity": "named",
            "allow_multiple": False,
            "starts_at": datetime.now(tz=UTC) - timedelta(hours=1),
            "tenant_id": "T1",
        }
        # 이미 응답한 기록 존재
        mock_collection.find.return_value = make_cursor([{"_id": "SR-T1-00001"}])

        svc = SurveyService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.submit_response(
                "SVY-T1-00001",
                {
                    "respondent_id": "EMP-001",
                    "answers": [],
                },
            )
        assert exc_info.value.error == "ERR-SVY-050"

    def test_필수_질문_미응답(self, mock_collection: MagicMock) -> None:
        """UT-SVY-012: 필수 질문에 응답하지 않으면 ERR-SVY-060."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "active",
            "anonymity": "named",
            "allow_multiple": True,
            "starts_at": datetime.now(tz=UTC) - timedelta(hours=1),
            "tenant_id": "T1",
        }
        # 필수 질문 조회 → 1개 있음
        mock_collection.find.return_value = make_cursor([{"_id": "SQ-001", "required": True}])

        svc = SurveyService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.submit_response(
                "SVY-T1-00001",
                {
                    "respondent_id": "EMP-001",
                    "answers": [],
                },
            )
        assert exc_info.value.error == "ERR-SVY-060"

    def test_마감_설문_응답_거부(self, mock_collection: MagicMock) -> None:
        """UT-SVY-013: status=closed일 때 ERR-SVY-051."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "closed",
            "tenant_id": "T1",
        }

        svc = SurveyService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.submit_response(
                "SVY-T1-00001",
                {
                    "respondent_id": "EMP-001",
                    "answers": [],
                },
            )
        assert exc_info.value.error == "ERR-SVY-051"


class TestResultsCalculation:
    """결과 집계 테스트."""

    def test_NPS_계산(self, mock_collection: MagicMock) -> None:
        """UT-SVY-014: NPS 점수 정확 계산.

        응답 데이터: 10, 9, 8, 7, 6, 5, 9, 10, 8, 7
        promoters(9~10): 4, passives(7~8): 4, detractors(0~6): 2
        NPS = (4-2)/10*100 = 20.0
        """
        responses = [
            {"answers": [{"question_id": "SQ-NPS", "nps_value": v}]}
            for v in [10, 9, 8, 7, 6, 5, 9, 10, 8, 7]
        ]

        svc = SurveyService("T1")
        result = svc.calculate_nps(responses, "SQ-NPS")

        assert result["nps_score"] == Decimal("20.0")
        assert result["promoters"] == 4
        assert result["passives"] == 4
        assert result["detractors"] == 2

    def test_척도_통계_계산(self, mock_collection: MagicMock) -> None:
        """UT-SVY-015: 척도 평균/중앙값/최빈값 정확.

        입력 데이터: 4, 3, 5, 4, 4, 3, 5, 2
        mean=3.75, median=4, mode=4
        """
        responses = [
            {"answers": [{"question_id": "SQ-SCALE", "scale_value": v}]}
            for v in [4, 3, 5, 4, 4, 3, 5, 2]
        ]

        svc = SurveyService("T1")
        result = svc.calculate_scale_stats(responses, "SQ-SCALE")

        assert result["mean"] == Decimal("3.75")
        assert result["median"] == Decimal("4.0")
        assert result["mode"] == 4
        assert result["count"] == 8

    def test_응답률_계산(self, mock_collection: MagicMock) -> None:
        """UT-SVY-016: 응답률 = (응답 수 / 대상 수) * 100."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "response_count": 120,
            "tenant_id": "T1",
        }

        svc = SurveyService("T1")
        rate = svc.calculate_response_rate("SVY-T1-00001", 150)

        assert rate == Decimal("80.0")


class TestConditionalLogic:
    """조건부 로직 테스트."""

    def test_jump_to(self, mock_collection: MagicMock) -> None:
        """UT-SVY-021: jump_to 시 대상 질문으로 이동."""
        all_questions = [
            {
                "_id": "SQ-005",
                "logic_rules": [
                    {
                        "condition_option_id": "opt-yes",
                        "action": "jump_to",
                        "target_question_id": "SQ-006",
                    },
                ],
            },
            {"_id": "SQ-006"},
            {"_id": "SQ-007"},
        ]

        svc = SurveyService("T1")
        result = svc.evaluate_logic_rules("SQ-005", "opt-yes", all_questions)

        assert result["action"] == "jump_to"
        assert result["next_question_id"] == "SQ-006"

    def test_skip(self, mock_collection: MagicMock) -> None:
        """UT-SVY-022: skip 시 다음 질문 건너뛰기."""
        all_questions = [
            {
                "_id": "SQ-005",
                "logic_rules": [
                    {"condition_option_id": "opt-no", "action": "skip"},
                ],
            },
            {"_id": "SQ-006"},
            {"_id": "SQ-007"},
        ]

        svc = SurveyService("T1")
        result = svc.evaluate_logic_rules("SQ-005", "opt-no", all_questions)

        assert result["action"] == "skip"
        assert result["next_question_id"] == "SQ-007"


class TestAnonymityProtection:
    """소규모 부서 익명 보호 테스트."""

    def test_소규모_부서_기타_합산(self, mock_collection: MagicMock) -> None:
        """UT-SVY-023: 10명 미만 그룹은 '기타'로 합산."""
        responses: list[dict[str, str]] = []
        responses.extend(
            [{"respondent_department": "영업팀", "survey_id": "SVY-T1-00001"} for _ in range(30)]
        )
        responses.extend(
            [{"respondent_department": "법무팀", "survey_id": "SVY-T1-00001"} for _ in range(3)]
        )

        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "tenant_id": "T1",
        }
        mock_collection.find.return_value = make_cursor(responses)

        svc = SurveyService("T1")
        result = svc.get_results_grouped("SVY-T1-00001", group_by="department")

        assert "영업팀" in result["groups"]
        assert "법무팀" not in result["groups"]
        assert "기타" in result["groups"]
        assert result["groups"]["기타"] == 3


class TestQuestionModification:
    """진행 중 설문 질문 수정 테스트."""

    def test_진행_중_질문_수정_거부(self, mock_collection: MagicMock) -> None:
        """UT-SVY-024: active 설문의 질문 수정 ERR-SVY-080."""
        mock_collection.find_one.return_value = {
            "_id": "SVY-T1-00001",
            "status": "active",
            "tenant_id": "T1",
        }

        svc = SurveyService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.add_question(
                "SVY-T1-00001",
                {
                    "question_text": "새 질문",
                    "question_type": "text",
                    "order": 1,
                },
            )
        assert exc_info.value.error == "ERR-SVY-080"


class TestTemplate:
    """템플릿 테스트."""

    def test_템플릿으로_설문_생성(self, mock_collection: MagicMock) -> None:
        """UT-SVY-025: 템플릿에서 질문 자동 복사, usage_count 증가."""
        mock_collection.find_one.return_value = {
            "_id": "ST-T1-00001",
            "name": "직원 만족도 조사",
            "usage_count": 5,
            "questions": [
                {
                    "question_text": "만족도?",
                    "question_type": "scale",
                    "required": True,
                    "order": 1,
                },
                {"question_text": "의견?", "question_type": "text", "required": False, "order": 2},
                {"question_text": "추천?", "question_type": "nps", "required": True, "order": 3},
            ],
            "tenant_id": "T1",
        }
        mock_collection.insert_one.return_value = MagicMock()
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = SurveyService("T1")
        result = svc.create_from_template("ST-T1-00001", {"title": "2026 만족도 조사"})

        assert result["template_id"] == "ST-T1-00001"
        assert result["questions_created"] == 3
        assert mock_collection.insert_one.call_count == 4
        assert mock_collection.update_one.call_count == 1
