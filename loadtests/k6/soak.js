import { check, sleep } from "k6";

import {
  config,
  ensureAuthenticatedUser,
  getCurrentUser,
  listItems,
  refreshToken,
} from "./common.js";

export const options = {
  stages: [
    { duration: "5m", target: 20 },
    { duration: "45m", target: 20 },
    { duration: "5m", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{endpoint:auth.me}": ["p(95)<300"],
    "http_req_duration{endpoint:auth.refresh}": ["p(95)<500"],
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

  const refreshResponse = refreshToken(data.refreshToken);
  check(refreshResponse, {
    "refresh is 200": (r) => r.status === 200,
  });

  if (refreshResponse.status === 200) {
    data.refreshToken = refreshResponse.json("refresh_token");
  }

  sleep(1);
}
