"""업무일지(WorkReport) 라우트 단위 테스트 -- HTTP API 레벨."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_learning_app.workreport.routes.work_report_templates import router as templates_router
from oneerp_learning_app.workreport.routes.work_reports import router as reports_router

_FAKE_USER = CurrentUser(
    sub="test-user",
    tenant_id="test-tenant",
    roles=("admin",),
    permissions=("*:*",),
)

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(reports_router)
_app.include_router(templates_router)
_app.dependency_overrides[get_current_user] = lambda: _FAKE_USER


class TestWorkReportAPI:
    """업무일지 API 엔드포인트 테스트."""

    @patch("oneerp_learning_app.workreport.routes.work_reports._get_repo")
    @patch(
        "oneerp_learning_app.workreport.routes.work_reports.generate_name",
        return_value="WR-2026-00001",
    )
    def test_생성(self, mock_name: MagicMock, mock_repo: MagicMock) -> None:
        """POST /api/v1/work-reports/ -- 201 응답."""
        mock_repo.return_value = MagicMock()
        client = TestClient(_app)

        response = client.post(
            "/api/v1/work-reports/",
            json={
                "employee_id": "EMP-001",
                "employee_name": "홍길동",
                "report_date": datetime.now(tz=UTC).date().isoformat(),
                "title": "일일 업무보고",
                "items": [{"task_name": "개발", "hours": 4}],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    @patch("oneerp_learning_app.workreport.routes.work_reports._get_repo")
    def test_목록조회(self, mock_repo: MagicMock) -> None:
        """GET /api/v1/work-reports/ -- 200 응답."""
        repo = MagicMock()
        repo.find_many.return_value = []
        repo.count.return_value = 0
        mock_repo.return_value = repo
        client = TestClient(_app)

        response = client.get("/api/v1/work-reports/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["total"] == 0

    @patch("oneerp_learning_app.workreport.routes.work_reports._get_repo")
    def test_상세조회_404(self, mock_repo: MagicMock) -> None:
        """GET /api/v1/work-reports/{doc_id} -- 없는 문서 404."""
        repo = MagicMock()
        repo.find_by_id.return_value = None
        mock_repo.return_value = repo
        client = TestClient(_app)

        response = client.get("/api/v1/work-reports/WR-999")
        assert response.status_code == 404

    @patch("oneerp_learning_app.workreport.routes.work_reports._get_repo")
    def test_상세조회_200(self, mock_repo: MagicMock) -> None:
        """GET /api/v1/work-reports/{doc_id} -- 존재하는 문서 200."""
        repo = MagicMock()
        repo.find_by_id.return_value = {
            "_id": "WR-001",
            "tenant_id": "default",
            "employee_id": "EMP-001",
            "status": "draft",
        }
        mock_repo.return_value = repo
        client = TestClient(_app)

        response = client.get("/api/v1/work-reports/WR-001")
        assert response.status_code == 200

    def test_미래일자_생성_실패(self) -> None:
        """BR-WR-002: 미래일자 보고서 생성 불가 -- 422."""
        client = TestClient(_app)
        response = client.post(
            "/api/v1/work-reports/",
            json={
                "employee_id": "EMP-001",
                "report_date": "2099-12-31",
                "title": "미래 보고서",
            },
        )
        assert response.status_code == 422


class TestWorkReportTemplateAPI:
    """업무일지 템플릿 API 엔드포인트 테스트."""

    @patch("oneerp_learning_app.workreport.routes.work_report_templates._get_repo")
    @patch(
        "oneerp_learning_app.workreport.routes.work_report_templates.generate_name",
        return_value="WRT-2026-00001",
    )
    def test_템플릿_생성(self, mock_name: MagicMock, mock_repo: MagicMock) -> None:
        """POST /api/v1/work-report-templates/ -- 201 응답."""
        mock_repo.return_value = MagicMock()
        client = TestClient(_app)

        response = client.post(
            "/api/v1/work-report-templates/",
            json={
                "name": "일일 개발보고 템플릿",
                "category": "daily",
                "department": "개발팀",
                "default_items": [{"task_name": "코드리뷰", "hours": 1}],
            },
        )
        assert response.status_code == 201

    @patch("oneerp_learning_app.workreport.routes.work_report_templates._get_repo")
    def test_템플릿_목록조회(self, mock_repo: MagicMock) -> None:
        """GET /api/v1/work-report-templates/ -- 200 응답."""
        repo = MagicMock()
        repo.find_many.return_value = []
        repo.count.return_value = 0
        mock_repo.return_value = repo
        client = TestClient(_app)

        response = client.get("/api/v1/work-report-templates/")
        assert response.status_code == 200
