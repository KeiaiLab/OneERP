# OneERP RPA 서비스 / RPA Service

Appium 기반 모바일 앱 자동화 서비스.
홈택스, 뱅킹, 보험 앱에 대한 RPA(Robotic Process Automation) 작업을 관리한다.

Appium-based mobile app automation service.
Manages RPA (Robotic Process Automation) tasks for HomeTax, banking, and insurance apps.

## 기능 / Features

- **홈택스 자동화 / HomeTax Automation**: 전자세금계산서 발급/조회
- **뱅킹 자동화 / Banking Automation**: 거래내역 조회, 잔액 확인
- **보험 자동화 / Insurance Automation**: 보험 계약 상태, 납부 내역 조회
- **기기 관리 / Device Management**: ADB를 통한 Android 기기 연결 관리

## 실행 / Run

```bash
uv run --package oneerp-rpa --directory services/rpa uvicorn app.main:app --port 8006
```

## 테스트 / Test

```bash
uv run pytest services/rpa/tests/
```

## API 엔드포인트 / API Endpoints

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/rpa/tasks/` | RPA 작업 생성 |
| GET | `/api/v1/rpa/tasks/` | 작업 목록 조회 |
| GET | `/api/v1/rpa/tasks/{task_id}` | 작업 상세 조회 |
| POST | `/api/v1/rpa/tasks/{task_id}/run` | 작업 수동 실행 |
| POST | `/api/v1/rpa/tasks/{task_id}/cancel` | 작업 취소 |
| GET | `/api/v1/rpa/tasks/devices` | 연결된 기기 목록 |
| POST | `/api/v1/rpa/results/` | RPA 결과 생성 |
| GET | `/api/v1/rpa/results/` | 결과 목록 조회 |
