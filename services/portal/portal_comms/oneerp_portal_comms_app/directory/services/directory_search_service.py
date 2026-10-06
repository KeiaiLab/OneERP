"""인명부 검색 서비스 — 직원 검색/필터링 비즈니스 로직.

BR-DIR-008: 인명부 엔트리는 직원과 조직 단위에 연결되어야 한다.
BR-DIR-009: 동일 직원은 동일 시점에 하나의 주 소속만 가진다.
BR-DIR-014: 인명부 검색은 이름, 부서, 직위, 이메일로 가능하다.
BR-DIR-015: 인명부 배치 등록 시 주 소속 중복을 검증한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 배치 응답용 고정 문구 — 예외 문자열을 클라이언트에 흘리지 않는다.
_ERR_PRIMARY_EXISTS = "ERR-DIR-009: 이미 주 소속이 존재합니다"


class DirectorySearchService:
    """인명부 검색 비즈니스 로직.

    직원 인명부 검색, 필터링, 배치 등록을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._dir_repo = Repository("employee_directories", tenant_id=tenant_id)
        self._unit_repo = Repository("org_units", tenant_id=tenant_id)

    def search_directory(
        self,
        keyword: str = "",
        org_unit_id: str = "",
        designation: str = "",
        status: str = "active",
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """인명부를 검색한다.

        BR-DIR-014: 이름, 부서, 직위, 이메일로 검색 가능하다.

        Args:
            keyword: 검색어 (이름, 이메일)
            org_unit_id: 조직 단위 필터
            designation: 직책 필터
            status: 상태 필터 (기본: active)
            page: 페이지 번호
            page_size: 페이지 크기

        Returns:
            검색 결과 (data + pagination)
        """
        query: dict[str, Any] = {}

        if status:
            query["status"] = status

        if org_unit_id:
            query["org_unit_id"] = org_unit_id

        if designation:
            query["designation"] = designation

        if keyword:
            # MongoDB $or 쿼리로 이름/이메일 검색
            query["$or"] = [
                {"employee_name": {"$regex": keyword, "$options": "i"}},
                {"email": {"$regex": keyword, "$options": "i"}},
            ]

        skip = (page - 1) * page_size
        results = self._dir_repo.find_many(query, skip=skip, limit=page_size)
        total = self._dir_repo.count(query)

        logger.info(
            "인명부 검색: keyword=%s, org_unit=%s, 결과=%d건",
            keyword,
            org_unit_id,
            total,
        )
        return {
            "data": results,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_unit_members(
        self,
        org_unit_id: str,
        *,
        include_sub_units: bool = False,
    ) -> list[dict[str, Any]]:
        """조직 단위의 소속 직원 목록을 조회한다.

        Args:
            org_unit_id: 조직 단위 ID
            include_sub_units: 하위 조직 포함 여부

        Returns:
            인명부 엔트리 목록
        """
        unit_ids = [org_unit_id]

        if include_sub_units:
            sub_units = self._unit_repo.find_many(
                {"parent_unit_id": org_unit_id, "status": "active"},
                limit=10000,
            )
            unit_ids.extend(u.get("_id", "") for u in sub_units)

        results = self._dir_repo.find_many(
            {"org_unit_id": {"$in": unit_ids}, "status": "active"},
            limit=10000,
        )

        logger.info(
            "조직 단위 구성원 조회: %s (%d개 단위, %d명)",
            org_unit_id,
            len(unit_ids),
            len(results),
        )
        return results

    def validate_primary_assignment(
        self,
        employee_id: str,
        *,
        exclude_entry_id: str | None = None,
    ) -> bool:
        """BR-DIR-009: 주 소속 중복을 검증한다.

        Args:
            employee_id: 직원 ID
            exclude_entry_id: 검증에서 제외할 엔트리 ID (수정 시)

        Returns:
            True면 주 소속 없음 (등록 가능)

        Raises:
            ValueError: 이미 주 소속이 존재하는 경우
        """
        existing = self._dir_repo.find_many(
            {
                "employee_id": employee_id,
                "is_primary": True,
                "status": "active",
            },
            limit=10,
        )

        for entry in existing:
            if exclude_entry_id and entry.get("_id") == exclude_entry_id:
                continue
            msg = (
                f"ERR-DIR-009: 직원 '{employee_id}'는 이미 "
                f"주 소속({entry.get('org_unit_id', '')})이 존재합니다"
            )
            raise ValueError(msg)

        return True

    def batch_register(
        self,
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """인명부를 배치로 등록한다.

        BR-DIR-015: 배치 등록 시 주 소속 중복을 검증한다.

        Args:
            entries: 등록할 인명부 엔트리 목록

        Returns:
            등록 결과 (성공/실패 수)
        """
        success_count = 0
        errors: list[dict[str, Any]] = []
        seen_primary: set[str] = set()

        for idx, entry in enumerate(entries):
            employee_id = entry.get("employee_id", "")
            is_primary = entry.get("is_primary", True)

            if not employee_id:
                errors.append({"index": idx, "error": "ERR-DIR-009: 직원 ID 누락"})
                continue

            # 동일 배치 내 주 소속 중복 검사
            if is_primary:
                if employee_id in seen_primary:
                    errors.append(
                        {
                            "index": idx,
                            "error": f"ERR-DIR-015: 배치 내 주 소속 중복 ({employee_id})",
                        }
                    )
                    continue
                seen_primary.add(employee_id)

                # DB 기존 주 소속 중복 검사
                try:
                    self.validate_primary_assignment(employee_id)
                except ValueError:
                    errors.append({"index": idx, "error": _ERR_PRIMARY_EXISTS})
                    continue

            entry["tenant_id"] = self._tenant_id
            self._dir_repo.insert(entry)
            success_count += 1

        logger.info(
            "인명부 배치 등록: 성공=%d, 실패=%d",
            success_count,
            len(errors),
        )
        return {
            "total": len(entries),
            "success": success_count,
            "failed": len(errors),
            "errors": errors,
        }
