import { check, sleep } from "k6";

import {
  config,
  ensureAuthenticatedUser,
  getCurrentUser,
  listItems,
} from "./common.js";

export const options = {
  stages: [
    { duration: "2m", target: 25 },
    { duration: "3m", target: 50 },
    { duration: "3m", target: 100 },
    { duration: "2m", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{endpoint:auth.me}": ["p(95)<300"],
    "http_req_duration{endpoint:items.list}": ["p(95)<300"],
  },
};

export function setup() {
  return ensureAuthenticatedUser();
}

export default function (data) {
  const meResponse = getCurrentUser(data.accessToken);
  check(meResponse, {
    "auth.me is 200": (r) => r.status === 200,
  });

  if (config.itemsEnabled) {
    const itemsResponse = listItems(data.accessToken);
    check(itemsResponse, {
      "items.list is 200": (r) => r.status === 200,
    });
  }

  sleep(1);
}
