"""이벤트 핸들러 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_cursor(data: list) -> MagicMock:
    """find() → skip() → limit() 체인을 지원하는 cursor mock을 생성한다."""
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.__iter__ = MagicMock(return_value=iter(data))
    return cursor


class Test직원정보변경핸들러:
    def test_인명부_갱신(self) -> None:
        """직원 이름 변경 시 인명부 엔트리를 갱신한다."""
        with (
            patch("oneerp_core.repository.get_client") as mock_client,
            patch("oneerp_core.naming.get_client"),
        ):
            mock_col = MagicMock()
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_client.return_value.__getitem__ = MagicMock(return_value=mock_db)

            mock_col.find.return_value = _make_cursor(
                [
                    {"_id": "EDIR-001", "employee_id": "EMP-001"},
                ]
            )
            mock_col.update_one.return_value.modified_count = 1

            from oneerp_portal_comms_app.directory.events.handlers import handle_employee_updated

            handle_employee_updated(
                {
                    "tenant_id": "T001",
                    "employee_id": "EMP-001",
                    "employee_name": "홍길순",
                }
            )

            mock_col.update_one.assert_called_once()

    def test_직원ID_누락_무시(self) -> None:
        """직원 ID가 누락된 이벤트는 무시한다."""
        from oneerp_portal_comms_app.directory.events.handlers import handle_employee_updated

        # Repository가 호출되지 않아야 한다
        handle_employee_updated({"tenant_id": "T001"})

    def test_변경필드_없으면_스킵(self) -> None:
        """변경할 필드가 없으면 업데이트하지 않는다."""
        with (
            patch("oneerp_core.repository.get_client") as mock_client,
            patch("oneerp_core.naming.get_client"),
        ):
            mock_col = MagicMock()
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_col)
            mock_client.return_value.__getitem__ = MagicMock(return_value=mock_db)

            mock_col.find.return_value = _make_cursor(
                [
                    {"_id": "EDIR-001"},
                ]
            )

            from oneerp_portal_comms_app.directory.events.handlers import handle_employee_updated

            handle_employee_updated(
                {
                    "tenant_id": "T001",
                    "employee_id": "EMP-001",
                    # 변경 필드 없음
                }
            )

            mock_col.update_one.assert_not_called()
