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

export default function () {
  const base = __ENV.GATEWAY_URL || 'https://staging-gateway.oneerp.dev';
  const token = __ENV.JWT || '';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = http.get(`${base}/health`, { headers });
  check(res, { '200': (r) => r.status === 200 });
  p95Latency.add(res.timings.duration);
  sleep(1);
}
