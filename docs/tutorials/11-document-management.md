# 문서 관리 튜토리얼

## 사용자 시나리오
1. 사용자는 문서 분류와 보존 정책을 준비한다.
2. 사용자는 템플릿으로 문서를 작성하고 초안을 저장한다.
3. 사용자는 문서를 제출·승인·배포한 뒤 외부 공유 링크와 전자서명을 설정한다.
4. 사용자는 문서 워크벤치에서 공유/서명/보존 상태를 확인한다.
5. 관리자는 보존 정책 워크벤치에서 연결 분류, 만료 임박 문서, 폐기 승인 필요 여부를 점검한다.

## 예시 흐름

```bash
curl -s -X POST http://localhost:8017/api/v1/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: demo' \
  -H 'X-User-Sub: manager-001' \
  -H 'X-User-Permissions: *:*' \
  -d '{
    "title": "2026년 영업 운영 지침",
    "category": "DC-2026-00001",
    "template_id": "DT-2026-00001",
    "template_variables": {
      "department": "영업팀",
      "author_name": "김철수"
    },
    "summary": "영업 운영 지침"
  }'

curl -s -X POST http://localhost:8017/api/v1/documents/DOC-2026-00001/submit \
  -H 'X-Tenant-Id: demo' \
  -H 'X-User-Sub: manager-001' \
  -H 'X-User-Permissions: *:*'

curl -s -X POST http://localhost:8017/api/v1/documents/DOC-2026-00001/approve \
  -H 'X-Tenant-Id: demo' \
  -H 'X-User-Sub: approver-001' \
  -H 'X-User-Permissions: *:*'

curl -s -X POST http://localhost:8017/api/v1/documents/DOC-2026-00001/publish \
  -H 'X-Tenant-Id: demo' \
  -H 'X-User-Sub: approver-001' \
  -H 'X-User-Permissions: *:*'

curl -s "http://localhost:8017/api/v1/documents?q=영업 운영&status=published" \
  -H 'X-Tenant-Id: demo' \
  -H 'X-User-Sub: manager-001' \
  -H 'X-User-Permissions: *:*' | jq

curl -s http://localhost:8017/api/v1/documents/DOC-2026-00001/summary \
  -H 'X-Tenant-Id: demo' \
  -H 'X-User-Sub: manager-001' \
  -H 'X-User-Permissions: *:*' | jq

curl -s http://localhost:8001/api/v1/retention-policies \
  -H 'X-Tenant-Id: demo' \
  -H 'X-User-Sub: admin-001' \
  -H 'X-User-Roles: admin' \
  -H 'X-User-Tier: tenant_admin' \
  -H 'X-User-Permissions: *:*' | jq

curl -s http://localhost:8001/api/v1/retention-policies/RP-0001/summary \
  -H 'X-Tenant-Id: demo' \
  -H 'X-User-Sub: admin-001' \
  -H 'X-User-Roles: admin' \
  -H 'X-User-Tier: tenant_admin' \
  -H 'X-User-Permissions: *:*' | jq
```

## 기대 결과
- 목록 응답 `summary`에 상태/공유/서명/보존 만료 카운트가 표시된다.
- 행별 `status_badge`와 `recommended_action`으로 운영 우선순위를 바로 파악할 수 있다.
- `/summary`에서 버전/공유/서명/감사 로그 요약을 한 번에 확인할 수 있다.
- 보존 정책 워크벤치 `summary`에는 활성 정책 수, 연결 분류 수, 만료 임박 문서 수가 표시된다.
- 보존 정책 `/summary`는 연결 분류 이름, 만료 임박 문서 수, 폐기 승인 필요 여부를 반환한다.
