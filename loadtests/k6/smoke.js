import http from "k6/http";
import { check } from "k6";

import { config } from "./common.js";

export const options = {
  vus: 1,
  iterations: 3,
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<300"],
  },
};

export default function () {
  const live = http.get(`${config.baseUrl}/health/live`, {
    tags: { scenario_group: "smoke", endpoint: "health.live" },
  });
  check(live, {
    "live is 200": (r) => r.status === 200,
  });

  const ready = http.get(`${config.baseUrl}/health/ready`, {
    tags: { scenario_group: "smoke", endpoint: "health.ready" },
  });
  check(ready, {
    "ready is 200 or 503": (r) => r.status === 200 || r.status === 503,
  });

  const metrics = http.get(`${config.baseUrl}/metrics`, {
    tags: { scenario_group: "smoke", endpoint: "metrics" },
  });
  check(metrics, {
    "metrics is 200": (r) => r.status === 200,
  });
}
