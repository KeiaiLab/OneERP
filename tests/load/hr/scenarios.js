// k6 시나리오 · staging gateway 배포 후 .github/workflows/load-test.yml 로 트리거
// hr 모듈 전용 — gateway scenarios.js 로부터 endpoint + payload 만 교체

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const p95Latency = new Trend('p95_latency');

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<300', 'p(99)<800'],
    http_req_failed: ['rate<0.01'],
  },
};

// hr 타깃 엔드포인트 — staging gateway 배포 이후 실제 응답 검증용
const TARGETS = [
  { path: '/hr/employees', method: 'GET', body: null },
  { path: '/hr/departments', method: 'GET', body: null },
];

export default function () {
  const base = __ENV.GATEWAY_URL || 'https://staging-gateway.oneerp.dev';
  const token = __ENV.JWT || '';
  const headers = token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' };

  for (const t of TARGETS) {
    let res;
    if (t.method === 'POST') {
      res = http.post(`${base}${t.path}`, JSON.stringify(t.body), { headers });
    } else {
      res = http.get(`${base}${t.path}`, { headers });
    }
    check(res, {
      '2xx': (r) => r.status >= 200 && r.status < 300,
    });
    p95Latency.add(res.timings.duration);
    sleep(1);
  }
}
