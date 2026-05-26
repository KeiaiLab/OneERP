"""메일 모델 유효성 검증 단위 테스트."""

from __future__ import annotations

import pytest
from oneerp_portal_comms_app.mail.models.mail_auto_rule import (
    MailAutoRuleCreate,
    RuleAction,
    RuleActionType,
    RuleCondition,
    RuleConditionType,
)
from oneerp_portal_comms_app.mail.models.mail_distribution_list import MailDistributionListCreate
from oneerp_portal_comms_app.mail.models.mail_folder import MailFolderCreate
from oneerp_portal_comms_app.mail.models.mail_message import (
    Attachment,
    MailMessageCreate,
    Recipient,
)


class TestMailMessageCreate:
    """MailMessageCreate 유효성 검증 테스트."""

    def test_정상_생성(self) -> None:
        """정상적인 메시지 생성."""
        msg = MailMessageCreate(
            subject="테스트",
            recipients=[Recipient(user_id="user1")],
        )
        assert msg.subject == "테스트"

    def test_수신자_없으면_에러(self) -> None:
        """BR-MAIL-001: 수신자 없으면 에러."""
        with pytest.raises(ValueError, match="수신자"):
            MailMessageCreate(subject="테스트", recipients=[])

    def test_제목_빈문자열_에러(self) -> None:
        """BR-MAIL-002: 빈 제목은 에러."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            MailMessageCreate(
                subject="",
                recipients=[Recipient(user_id="user1")],
            )

    def test_첨부파일_10개_초과_에러(self) -> None:
        """BR-MAIL-004: 첨부파일 10개 초과 시 에러."""
        attachments = [
            Attachment(file_name=f"file{i}.txt", file_url=f"/files/{i}") for i in range(11)
        ]
        with pytest.raises(ValueError, match="첨부파일"):
            MailMessageCreate(
                subject="테스트",
                recipients=[Recipient(user_id="user1")],
                attachments=attachments,
            )

    def test_첨부파일_크기_초과_에러(self) -> None:
        """BR-MAIL-004: 첨부파일 20MB 초과 시 에러."""
        attachments = [
            Attachment(
                file_name="big.bin",
                file_url="/files/big",
                file_size=21 * 1024 * 1024,
            ),
        ]
        with pytest.raises(ValueError, match="20MB"):
            MailMessageCreate(
                subject="테스트",
                recipients=[Recipient(user_id="user1")],
                attachments=attachments,
            )


class TestMailFolderCreate:
    """MailFolderCreate 유효성 검증 테스트."""

    def test_정상_생성(self) -> None:
        """정상적인 폴더 생성."""
        folder = MailFolderCreate(name="프로젝트")
        assert folder.name == "프로젝트"

    def test_깊이_초과_에러(self) -> None:
        """BR-MAIL-012: 깊이 3 초과 시 에러."""
        with pytest.raises(ValueError, match="폴더 계층"):
            MailFolderCreate(name="깊은폴더", depth=4)


class TestMailDistributionListCreate:
    """MailDistributionListCreate 유효성 검증 테스트."""

    def test_정상_생성(self) -> None:
        """정상적인 배포 목록 생성."""
        dl = MailDistributionListCreate(
            list_name="개발팀",
            members=["user1", "user2"],
        )
        assert dl.list_name == "개발팀"

    def test_구성원_없으면_에러(self) -> None:
        """BR-MAIL-040: 구성원 없으면 에러."""
        with pytest.raises(ValueError, match="구성원"):
            MailDistributionListCreate(list_name="빈팀", members=[])


class TestMailAutoRuleCreate:
    """MailAutoRuleCreate 유효성 검증 테스트."""

    def test_정상_생성(self) -> None:
        """정상적인 자동 규칙 생성."""
        rule = MailAutoRuleCreate(
            rule_name="중요 메일 분류",
            conditions=[
                RuleCondition(condition_type=RuleConditionType.PRIORITY, value="urgent"),
            ],
            actions=[
                RuleAction(action_type=RuleActionType.STAR),
            ],
        )
        assert rule.rule_name == "중요 메일 분류"

    def test_조건_없으면_에러(self) -> None:
        """BR-MAIL-050: 조건 없으면 에러."""
        with pytest.raises(ValueError, match="조건"):
            MailAutoRuleCreate(
                rule_name="규칙",
                conditions=[],
                actions=[RuleAction(action_type=RuleActionType.STAR)],
            )

    def test_동작_없으면_에러(self) -> None:
        """BR-MAIL-050: 동작 없으면 에러."""
        with pytest.raises(ValueError, match="동작"):
            MailAutoRuleCreate(
                rule_name="규칙",
                conditions=[
                    RuleCondition(condition_type=RuleConditionType.SENDER, value="user1"),
                ],
                actions=[],
            )

    def test_우선순위_음수_에러(self) -> None:
        """BR-MAIL-051: 우선순위 음수 시 에러."""
        with pytest.raises(ValueError, match="우선순위"):
            MailAutoRuleCreate(
                rule_name="규칙",
                conditions=[
                    RuleCondition(condition_type=RuleConditionType.SENDER, value="user1"),
                ],
                actions=[
                    RuleAction(action_type=RuleActionType.STAR),
                ],
                priority_order=-1,
            )
