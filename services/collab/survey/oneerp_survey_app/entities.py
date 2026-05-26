"""Survey 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

7개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.poll import Poll, PollCreate, PollUpdate
from .models.poll_vote import PollVote, PollVoteCreate, PollVoteUpdate
from .models.survey import Survey, SurveyCreate, SurveyUpdate
from .models.survey_question import SurveyQuestion, SurveyQuestionCreate, SurveyQuestionUpdate
from .models.survey_response import SurveyResponse, SurveyResponseCreate, SurveyResponseUpdate
from .models.survey_template import SurveyTemplate, SurveyTemplateCreate, SurveyTemplateUpdate

# --- 설문 관련 ---

SURVEY = EntityMeta(
    collection="surveys",
    prefix="SVY",
    api_path="/api/v1/surveys",
    tag="설문",
    resource="survey",
    model=Survey,
    create_schema=SurveyCreate,
    update_schema=SurveyUpdate,
    archetype="transaction",
    not_found_message="설문을 찾을 수 없습니다",
)

SURVEY_QUESTION = EntityMeta(
    collection="survey_questions",
    prefix="SQ",
    api_path="/api/v1/survey-questions",
    tag="설문 질문",
    resource="survey_question",
    model=SurveyQuestion,
    create_schema=SurveyQuestionCreate,
    update_schema=SurveyQuestionUpdate,
    archetype="transaction",
    not_found_message="설문 질문을 찾을 수 없습니다",
)

SURVEY_RESPONSE = EntityMeta(
    collection="survey_responses",
    prefix="SR",
    api_path="/api/v1/survey-responses",
    tag="설문 응답",
    resource="survey_response",
    model=SurveyResponse,
    create_schema=SurveyResponseCreate,
    update_schema=SurveyResponseUpdate,
    archetype="transaction",
    not_found_message="설문 응답을 찾을 수 없습니다",
)

# --- 투표 관련 ---

POLL = EntityMeta(
    collection="polls",
    prefix="POL",
    api_path="/api/v1/polls",
    tag="투표",
    resource="poll",
    model=Poll,
    create_schema=PollCreate,
    update_schema=PollUpdate,
    archetype="transaction",
    not_found_message="투표를 찾을 수 없습니다",
)

POLL_VOTE = EntityMeta(
    collection="poll_votes",
    prefix="PV",
    api_path="/api/v1/poll-votes",
    tag="투표 기록",
    resource="poll_vote",
    model=PollVote,
    create_schema=PollVoteCreate,
    update_schema=PollVoteUpdate,
    archetype="transaction",
    not_found_message="투표 기록을 찾을 수 없습니다",
)

# --- 템플릿 ---

SURVEY_TEMPLATE = EntityMeta(
    collection="survey_templates",
    prefix="ST",
    api_path="/api/v1/survey-templates",
    tag="설문 템플릿",
    resource="survey_template",
    model=SurveyTemplate,
    create_schema=SurveyTemplateCreate,
    update_schema=SurveyTemplateUpdate,
    archetype="master",
    not_found_message="설문 템플릿을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    SURVEY,
    SURVEY_QUESTION,
    SURVEY_RESPONSE,
    POLL,
    POLL_VOTE,
    SURVEY_TEMPLATE,
]
