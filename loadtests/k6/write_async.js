import { check, sleep } from "k6";

import {
  buildUser,
  config,
  createItem,
  ensureAuthenticatedUser,
  registerUser,
} from "./common.js";

export const options = {
  stages: [
    { duration: "2m", target: 10 },
    { duration: "3m", target: 25 },
    { duration: "3m", target: 50 },
    { duration: "2m", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.02"],
    "http_req_duration{endpoint:users.register}": ["p(95)<500"],
    "http_req_duration{endpoint:items.create}": ["p(95)<500"],
  },
};

export function setup() {
  return ensureAuthenticatedUser();
}

export default function (data) {
  const user = buildUser();
  const registerResponse = registerUser(user);
  check(registerResponse, {
    "register is 201": (r) => r.status === 201,
  });

  if (config.itemsEnabled) {
    const createResponse = createItem(data.accessToken, {
      title: `k6-item-${__VU}-${__ITER}`,
      description: "load test item",
    });
    check(createResponse, {
      "item create is 201": (r) => r.status === 201,
    });
  }

  sleep(1);
}
