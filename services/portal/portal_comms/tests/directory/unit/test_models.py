"""모델 유효성 검증 단위 테스트."""

from __future__ import annotations

import pytest
from oneerp_portal_comms_app.directory.models.employee_directory import EmployeeDirectoryCreate
from oneerp_portal_comms_app.directory.models.org_unit import OrgUnitCreate
from oneerp_portal_comms_app.directory.models.organization import OrganizationCreate
from oneerp_portal_comms_app.directory.models.position import PositionCreate


class Test조직모델:
    def test_정상_생성(self) -> None:
        """유효한 데이터로 조직을 생성한다."""
        org = OrganizationCreate(org_code="C001", org_name="테스트법인")
        assert org.org_code == "C001"
        assert org.org_name == "테스트법인"

    def test_코드_누락_에러(self) -> None:
        """조직 코드가 비어있으면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-001"):
            OrganizationCreate(org_code="", org_name="테스트법인")

    def test_명칭_누락_에러(self) -> None:
        """조직 명칭이 비어있으면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-002"):
            OrganizationCreate(org_code="C001", org_name="")

    def test_공백만_있는_코드(self) -> None:
        """공백만 있는 조직 코드는 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-001"):
            OrganizationCreate(org_code="   ", org_name="테스트법인")


class Test조직단위모델:
    def test_정상_생성(self) -> None:
        """유효한 데이터로 조직 단위를 생성한다."""
        unit = OrgUnitCreate(org_id="ORG-001", unit_code="DEPT01", unit_name="인사팀")
        assert unit.org_id == "ORG-001"

    def test_조직ID_누락_에러(self) -> None:
        """소속 조직 ID가 누락되면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-003"):
            OrgUnitCreate(org_id="", unit_code="DEPT01", unit_name="인사팀")

    def test_단위코드_누락_에러(self) -> None:
        """조직 단위 코드가 누락되면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-004"):
            OrgUnitCreate(org_id="ORG-001", unit_code="", unit_name="인사팀")

    def test_단위명칭_누락_에러(self) -> None:
        """조직 단위 명칭이 누락되면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-005"):
            OrgUnitCreate(org_id="ORG-001", unit_code="DEPT01", unit_name="")


class Test직위모델:
    def test_정상_생성(self) -> None:
        """유효한 데이터로 직위를 생성한다."""
        pos = PositionCreate(
            org_unit_id="UNIT-001",
            position_code="MGR",
            position_title="과장",
        )
        assert pos.headcount == 1

    def test_조직단위_누락_에러(self) -> None:
        """소속 조직 단위가 누락되면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-006"):
            PositionCreate(
                org_unit_id="",
                position_code="MGR",
                position_title="과장",
            )

    def test_정원_0이하_에러(self) -> None:
        """정원이 0 이하이면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-008"):
            PositionCreate(
                org_unit_id="UNIT-001",
                position_code="MGR",
                position_title="과장",
                headcount=0,
            )


class Test인명부모델:
    def test_정상_생성(self) -> None:
        """유효한 데이터로 인명부 엔트리를 생성한다."""
        entry = EmployeeDirectoryCreate(
            employee_id="EMP-001",
            employee_name="홍길동",
            org_unit_id="UNIT-001",
        )
        assert entry.is_primary is True

    def test_직원ID_누락_에러(self) -> None:
        """직원 ID가 누락되면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-009"):
            EmployeeDirectoryCreate(
                employee_id="",
                employee_name="홍길동",
                org_unit_id="UNIT-001",
            )

    def test_조직단위_누락_에러(self) -> None:
        """조직 단위 ID가 누락되면 에러를 발생시킨다."""
        with pytest.raises(ValueError, match="ERR-DIR-010"):
            EmployeeDirectoryCreate(
                employee_id="EMP-001",
                employee_name="홍길동",
                org_unit_id="",
            )
