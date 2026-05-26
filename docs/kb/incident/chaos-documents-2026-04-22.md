---
chaos_id: chaos-documents-2026-04-22
module: documents
severity: P2-simulated
conducted_at: 2026-04-22T08:00:00Z
duration_minutes: 9
---

# chaos-documents-2026-04-22 — S3 throttle 대응

## 가설
S3 throttle 시 업로드 재시도 전략이 사용자 경험 손상 최소화.

## 주입
S3 SDK 에 429 50% 주입.

## 관측
- 업로드 p95 980ms → 2.4s.
- 재시도 성공률 99.7%.
- 클라이언트 fail 0건.

## 결론
exponential backoff 정상. S3 provisioning 증설 검토.
