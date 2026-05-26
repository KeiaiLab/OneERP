"""투표 서비스 단위 테스트.

UT-SVY-017~020: 투표 생성/투표하기/중복 투표/비율 계산 테스트.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_survey_app.models.poll import Poll, PollOption, PollType
from oneerp_survey_app.services.poll_service import PollService

from .conftest import make_cursor


class TestPollCreation:
    """투표 생성 테스트."""

    def test_투표_생성(self, mock_collection: MagicMock) -> None:
        """UT-SVY-017: Poll 생성."""
        poll = Poll(
            title="금요 회식 장소",
            poll_type=PollType.SINGLE_CHOICE,
            options=[
                PollOption(option_id="opt-1", text="한식", vote_count=0),
                PollOption(option_id="opt-2", text="일식", vote_count=0),
                PollOption(option_id="opt-3", text="중식", vote_count=0),
            ],
        )
        assert poll.status == "active"
        assert poll.total_votes == 0
        assert len(poll.options) == 3


class TestCastVote:
    """투표하기 테스트."""

    def test_투표_성공(self, mock_collection: MagicMock) -> None:
        """UT-SVY-018: PV 생성, vote_count 증가."""
        mock_collection.find_one.return_value = {
            "_id": "POL-T1-00001",
            "title": "금요 회식 장소",
            "status": "active",
            "anonymity": "named",
            "total_votes": 0,
            "options": [
                {"option_id": "opt-1", "text": "한식", "vote_count": 0},
                {"option_id": "opt-2", "text": "일식", "vote_count": 0},
                {"option_id": "opt-3", "text": "중식", "vote_count": 0},
            ],
            "tenant_id": "T1",
        }
        # find_many: 중복 투표 체크 → 빈 결과
        mock_collection.find.return_value = make_cursor([])
        mock_collection.insert_one.return_value = MagicMock()
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = PollService("T1")
        result = svc.cast_vote(
            "POL-T1-00001",
            {
                "voter_id": "EMP-001",
                "selected_options": ["opt-2"],
            },
        )

        assert result["poll_id"] == "POL-T1-00001"
        assert result["selected_options"] == ["opt-2"]
        # update_one으로 options 업데이트 확인
        mock_collection.update_one.assert_called_once()

    def test_중복_투표_거부(self, mock_collection: MagicMock) -> None:
        """UT-SVY-019: 중복 투표 시 ERR-SVY-070."""
        mock_collection.find_one.return_value = {
            "_id": "POL-T1-00001",
            "status": "active",
            "anonymity": "named",
            "tenant_id": "T1",
        }
        # 이미 투표한 기록 존재
        mock_collection.find.return_value = make_cursor([{"_id": "PV-T1-00001"}])

        svc = PollService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.cast_vote(
                "POL-T1-00001",
                {
                    "voter_id": "EMP-001",
                    "selected_options": ["opt-1"],
                },
            )
        assert exc_info.value.error == "ERR-SVY-070"

    def test_마감_투표_거부(self, mock_collection: MagicMock) -> None:
        """EX-SVY-010: 마감된 투표 시 ERR-SVY-071."""
        mock_collection.find_one.return_value = {
            "_id": "POL-T1-00001",
            "status": "closed",
            "tenant_id": "T1",
        }

        svc = PollService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.cast_vote(
                "POL-T1-00001",
                {
                    "voter_id": "EMP-001",
                    "selected_options": ["opt-1"],
                },
            )
        assert exc_info.value.error == "ERR-SVY-071"


class TestPollResults:
    """투표 결과 테스트."""

    def test_투표_비율_계산(self, mock_collection: MagicMock) -> None:
        """UT-SVY-020: 비율 정확 계산."""
        mock_collection.find_one.return_value = {
            "_id": "POL-T1-00001",
            "title": "금요 회식 장소",
            "total_votes": 2,
            "options": [
                {"option_id": "opt-1", "text": "한식", "vote_count": 1},
                {"option_id": "opt-2", "text": "일식", "vote_count": 1},
                {"option_id": "opt-3", "text": "중식", "vote_count": 0},
            ],
            "tenant_id": "T1",
        }

        svc = PollService("T1")
        result = svc.get_results("POL-T1-00001")

        assert result["total_votes"] == 2
        assert len(result["options"]) == 3
        assert result["options"][0]["percentage"] == Decimal("50.0")
        assert result["options"][1]["percentage"] == Decimal("50.0")
        assert result["options"][2]["percentage"] == Decimal(0)

    def test_투표_마감(self, mock_collection: MagicMock) -> None:
        """투표 마감 테스트."""
        mock_collection.find_one.return_value = {
            "_id": "POL-T1-00001",
            "status": "active",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = PollService("T1")
        result = svc.close_poll("POL-T1-00001")
        assert result["status"] == "closed"
