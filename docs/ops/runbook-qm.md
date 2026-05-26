---
owner: QM Ops
host: qm
modules: [quality, maintenance]
related_runbooks:
  - docs/ops/runbook-manufacturing.md
  - docs/ops/runbook-incident-response.md
last_updated: 2026-04-22
---

# qm (quality + maintenance) 운영 런북

qm 플레인은 품질(quality) 과 설비 유지보수(maintenance) 를 번들 호스팅한다.

## quality

품질 검사 계획·결과·부적합·시정조치(CAPA). manufacturing 공정 이벤트 수신.

```bash
curl -s http://qm:8000/v1/quality/inspections?state=pending
```

## maintenance

설비 master·점검 일정·고장 이력. PM (Predictive Maintenance) 파이프라인.

```bash
curl -s http://qm:8000/v1/maintenance/assets?status=down
```

## 자주 발생 이슈

| 증상 | 원인 | 조치 |
|---|---|---|
| 검사 결과 미반영 | manufacturing 이벤트 누락 | NATS consumer re-subscribe |
| PM 예측 실패 | 이상감지 모델 drift | 모델 재학습 큐 투입 |
| 설비 down 경보 지연 | iot 게이트웨이 연결 | iot 런북 참조 |

## 에스컬레이션

- Primary: `@qm-ops`
- Cross: `@manufacturing-ops` (공정 영향), `@iot-ops` (설비 센서)
