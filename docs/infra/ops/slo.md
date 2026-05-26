# SLO (서비스 수준 목표)

## 대상 규모

| 항목 | 값 |
|------|-----|
| ERP 활성 사용자 | ~50,000명 |
| 동시 접속(일반) | 10,000명 |
| 동시 접속(피크) | 30,000명 |
| 일일 트랜잭션 | 1,000,000건+ |

## SLI 정의

| SLI | 측정 방법 | 데이터 소스 |
|-----|----------|-----------|
| 가용성 | 1 - (5xx 응답 수 / 전체 요청 수) | Ingress 로그, Prometheus |
| API 지연 | 요청-응답 시간 히스토그램 (p95, p99) | 애플리케이션 미들웨어 |
| 에러율 | (4xx + 5xx) / 전체 요청 | Ingress 로그 |
| 비동기 작업 지연 | 큐 진입 ~ 처리 완료 시간 (p95) | 작업 큐 메트릭 |
| 비동기 작업 실패율 | 실패 작업 수 / 전체 작업 수 | 작업 큐 메트릭 |
| DB 쿼리 지연 | 쿼리 실행 시간 (p95) | FerretDB/PostgreSQL slow query log |

## SLO 목표

| SLI | SLO | 측정 기간 |
|-----|-----|----------|
| 가용성 | ≥ 99.9% | 월간 (30일 롤링) |
| API 지연 (p95) | < 200ms | 월간 |
| API 지연 (p99) | < 500ms | 월간 |
| 리스트 조회 지연 (p95) | < 300ms | 월간 |
| 리포트 집계 지연 (p95) | < 3초 | 월간 |
| 에러율 | < 0.1% | 월간 |
| 비동기 작업 지연 (p95) | < 30초 | 월간 |
| 비동기 작업 실패율 | < 0.5% | 월간 |
| DB 쿼리 지연 (p95) | < 50ms | 월간 |

## 에러 버짓 계산

### 가용성 에러 버짓 (99.9%)

| 기간 | 총 시간 | 허용 다운타임 |
|------|--------|-------------|
| 월간 (30일) | 43,200분 | 43.2분 (≈ 43분) |
| 분기 (90일) | 129,600분 | 129.6분 (≈ 2시간 10분) |
| 연간 (365일) | 525,600분 | 525.6분 (≈ 8시간 46분) |

### 에러율 에러 버짓 (< 0.1%)

일일 100만 트랜잭션 기준:

| 기간 | 총 요청 | 허용 에러 수 |
|------|--------|-------------|
| 일간 | 1,000,000건 | 1,000건 |
| 월간 | 30,000,000건 | 30,000건 |

### 에러 버짓 소진 정책

| 소진율 | 대응 |
|--------|------|
| < 50% | 정상 운영, 신규 배포 허용 |
| 50% ~ 80% | 경고 알림, 배포 시 추가 검증 필수 |
| 80% ~ 100% | 신규 기능 배포 동결, 안정성 작업만 허용 |
| 100% 초과 | 전면 배포 동결, 포스트모템 수행, 버짓 복구까지 안정성 집중 |

## 모니터링 대상 E2E 시나리오

다음 5개 핵심 시나리오의 성공률/지연을 SLI로 측정한다 (→ `docs/product/scope/03-e2e-scenarios.md`):

1. 판매 (Quotation → Payment)
2. 구매 (Material Request → Payment)
3. 재고 (입출고, 재고평가)
4. 회계 (전표 생성/승인, 기간 마감)
5. 권한/감사 (Role 변경, 민감 데이터 접근)

### 시나리오별 SLO

| 시나리오 | 성공률 SLO | 지연 SLO (p95) |
|----------|----------|---------------|
| 판매 플로우 (전체) | ≥ 99.9% | < 500ms (개별 API) |
| 구매 플로우 (전체) | ≥ 99.9% | < 500ms (개별 API) |
| 재고 입출고 | ≥ 99.9% | < 300ms |
| 회계 전표 | ≥ 99.9% | < 300ms |
| 월말 마감 집계 | ≥ 99.5% | < 1시간 (배치) |

## 알림 규칙

| 조건 | 심각도 | 알림 채널 |
|------|--------|----------|
| 5분간 에러율 > 1% | Critical | Slack + PagerDuty |
| 5분간 p95 > 500ms | Warning | Slack |
| 에러 버짓 소진 > 50% | Warning | Slack (일간 리포트) |
| 에러 버짓 소진 > 80% | Critical | Slack + 배포 동결 알림 |
| DB 쿼리 p95 > 100ms | Warning | Slack |

## 산출물(DoD)

- [x] SLI/SLO 정의 완료
- [x] 에러 버짓 계산 완료
- [ ] Prometheus 알림 규칙 적용됨
- [ ] Grafana SLO 대시보드 구성됨
- [ ] 에러 버짓 소진 자동 알림 설정됨

## 모듈별 SLO

각 모듈의 세부 SLO — 전사 기본 SLO 를 승계하되, 도메인 특수성을 반영.

### gateway

- 가용성 ≥ 99.95% (전 모듈 진입점이므로 상향).
- 인증 엔드포인트 p95 < 150ms.
- rate limit 오탐 < 0.1% (redis fallback 고려).

### directory

- 가용성 ≥ 99.95% — SSO 연쇄 장애 방지.
- SAML metadata 재읽기 p95 < 800ms (dual-read 포함).
- 세션 정합성 오차 허용: 0.

### accounting

- API 가용성 ≥ 99.9%.
- 분개 쓰기 p99 < 400ms.
- GL 무결성 불변식: 차대 일치 100%, balance_reconcile 100%.

### hr

- API 가용성 ≥ 99.9%.
- PII 응답 마스킹 정책 위반: 0/월 (chaos-hr-2026-04-22 검증).
- 로그 평문 주민번호 노출: 0.

### payroll

- 집행 성공률 ≥ 99.5% (은행 실패 수동 보전 포함 시 100%).
- 월 지급 시한 준수율 100% (법적 요구).
- B-bank fallback MTTA < 15분.

### selling

- API 가용성 ≥ 99.9%.
- checkout 완료 성공률 ≥ 98% (PG A/B 전환 포함).
- SO 상태 역진: 0.

### buying

- API 가용성 ≥ 99.9%.
- 승인 체인 역진: 0.
- 3-way match 불일치 ≥5% 경보 MTTA < 30분.

### stock

- API 가용성 ≥ 99.9%.
- movement 쓰기 p95 < 250ms.
- 실사 reconcile 허용 오차 ±0.5%.

### portal

- 가용성 ≥ 99.5% (CDN 우회 fallback 포함).
- 첫 페이지 로드 p95 < 2.0s.
- 세션 강제 만료 실패율: 0.

### projects

- API 가용성 ≥ 99.9%.
- WBS 집계 지연 p95 < 1.5s.
- SLA 오보 자동 발송: 0 (auto-guard 필수).

### expenses

- API 가용성 ≥ 99.9%.
- fraud-detection 배치 완료 SLA: 일일 08:00 KST.
- 영수증 blob 재연결 허용 누락: < 2%/월.

### crm

- API 가용성 ≥ 99.9%.
- 이메일 발송 성공률 ≥ 95% (급락 시 자동 중단).
- 관계 그래프 무결성: opp→lead 참조율 ≥ 99%.

### manufacturing
- API 가용성 ≥ 99.9%. MRP 일괄 계산 < 90s (1000 BOM).

### quality
- API 가용성 ≥ 99.9%. 검사 결과 쓰기 p95 < 138ms.

### assets
- API 가용성 ≥ 99.9%. 감가상각 배치 < 25min (100K 자산).

### maintenance
- API 가용성 ≥ 99.9%. iot 이벤트 처리량 ≥ 1200/s sustained.

### ecommerce
- API 가용성 ≥ 99.9%. 체크아웃 p95 < 483ms.

### pos
- 단말 동기화 성공률 ≥ 99.5%. 중복 병합 성공률 ≥ 99.9%.

### subscriptions
- 갱신 배치 < 45min (10K 구독). dunning SLA ≤ 72h.

### integration-hub
- 메시지 변환 p95 < 48ms. circuit breaker open→half-open ≤ 30s.

### documents
- 업로드 p95 < 598ms (2MB). S3 재시도율 < 2%.

### compliance
- 감사 리포트 생성 < 60s. 정책 위반 경보 MTTA < 30분.

### ehs
- 사고 보고 법적 기한 위반 0/분기. 법적 리포트 생성 < 45s.

### plm
- BOM 쓰기 p95 < 253ms. ECN 승인 체인 SLA ≤ 5 영업일.

### survey
- 응답 쓰기 p95 < 207ms. NPS 집계 < 20s.

### calendar
- API 가용성 ≥ 99.9%. 일정 조회 p95 < 120ms. 동기화 성공률 ≥ 99.5%.

### board
- API 가용성 ≥ 99.9%. 게시판 쓰기 p95 < 150ms. 첨부 업로드 p95 < 600ms.

### mail
- 메일 발송 성공률 ≥ 95%. 수신 동기화 지연 p95 < 30s.

### messenger
- 메시지 전달 p95 < 200ms. 동시 접속 ≥ 10k 유지.

### wiki
- 페이지 로드 p95 < 300ms. 편집 충돌 dedup 성공률 100%.

### knowledge
- 검색 p95 < 400ms. 인덱스 신선도 < 60s.

### analytics
- 대시보드 로드 p95 < 1.5s. ETL 파이프라인 SLA 일 1회.

### rental
- 예약 조회 p95 < 180ms. 충돌 방지 100%.

### fleet
- 차량 상태 갱신 p95 < 500ms (iot 의존). 경로 최적화 < 5s.

### tms
- 배차 계산 p95 < 2s. 실시간 위치 갱신 p95 < 1s.

### marketing
- 캠페인 목록 p95 < 200ms. 이벤트 추적 손실 < 0.1%.

### marketing-automation
- 트리거 실행 p95 < 500ms. 이메일 발송 성공률 ≥ 95%.

### gtm
- 태그 로드 p95 < 80ms. CDN edge 히트율 ≥ 95%.

### clm
- 계약서 조회 p95 < 200ms. eSign 완료율 95% 이상.

### advanced-planning
- 계획 수립 배치 < 30min (10K SKU). 시나리오 시뮬 < 5min.

### consolidation
- 연결 결산 배치 < 60min. 무결성 검증 100%.

### esg
- ESG 지표 갱신 주기 일 1회. 외부 보고 양식 정확도 ≥ 99%.

### iot
- 센서 이벤트 처리량 ≥ 5000/s. 연결 안정성 ≥ 99.5%.

### rpa
- 봇 실행 성공률 ≥ 95%. 실행 시간 표준편차 < 20%.

### lms
- 코스 조회 p95 < 200ms. 진도율 집계 실시간.

### workreport
- 제출 쓰기 p95 < 150ms. 승인 SLA < 2 영업일.

### reservation
- 예약 생성 p95 < 200ms. 동시 예약 충돌 방지 100%.

## gateway

> Commercial Grade v2 G2-1 기준.
> 최종 갱신: 2026-04-22

### SLO 목표

| 지표 | 목표 | 측정 기간 |
|---|---|---|
| 가용성 | ≥ 99.9% | 월간 (30일 롤링) |
| 요청 지연 p95 | < 200ms | 월간 |
| 요청 지연 p99 | < 500ms | 월간 |
| 에러율 (5xx) | < 0.1% | 월간 |

> 참고: 모듈별 SLO 섹션의 `### gateway` (가용성 ≥ 99.95%)가 더 엄격하며 실운영 기준으로 적용.

### Error Budget

- 월간 가용성 허용 다운타임: **43.2 분** (99.9% 기준)
- 에러버짓 소진 시 배포 동결 + 신뢰성 작업 최우선 처리

### Prometheus 쿼리

- **가용성**:
  ```promql
  1 - sum(rate(gateway_http_requests_total{status=~"5.."}[30d])) / sum(rate(gateway_http_requests_total[30d]))
  ```

- **p95 지연**:
  ```promql
  histogram_quantile(0.95, sum(rate(gateway_request_duration_seconds_bucket[30d])) by (le))
  ```

- 대시보드: `deploy/monitoring/grafana/gateway-overview.json`
- 알림 규칙: `deploy/monitoring/alerts/gateway.yaml`

### 30일 번다운

- 실측 로그: `artifacts/slo/gateway-30d.json`
- staging Prometheus 가동 후 실측값으로 교체 예정 (Spec II.5)
