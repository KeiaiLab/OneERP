"""OneERP API Plane — Runtime-Plane 분해(ADR-0014) P1.

ERP 동기 CRUD 도메인을 단일 uvicorn 프로세스에 마운트한다.
M1: selling 1개 도메인만 마운트. M1.5 이후 stock 외 추가 도메인 확장.
"""
