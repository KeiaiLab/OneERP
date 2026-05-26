// G2-2 k6 시나리오 · staging 전용
// source: docs/engineering/data/perf-ecommerce-baseline.md
// target_rps: 400

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 400 },
    { duration: '10m', target: 400 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<470'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const base = __ENV.GATEWAY_URL || 'https://staging-gateway.oneerp.dev';
  const token = __ENV.JWT || '';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = http.get(`${base}/api/ecommerce/health`, { headers });
  check(res, { 'status is not 5xx': (r) => r.status < 500 });
  sleep(1);
}
