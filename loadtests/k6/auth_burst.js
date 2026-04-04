import { check, sleep } from "k6";

import {
  buildUser,
  loginUser,
  logout,
  refreshToken,
  registerUser,
} from "./common.js";

export const options = {
  stages: [
    { duration: "1m", target: 20 },
    { duration: "2m", target: 50 },
    { duration: "2m", target: 100 },
    { duration: "1m", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.02"],
    "http_req_duration{endpoint:auth.login}": ["p(95)<500"],
    "http_req_duration{endpoint:auth.refresh}": ["p(95)<500"],
    "http_req_duration{endpoint:auth.logout}": ["p(95)<500"],
  },
};

export default function () {
  const user = buildUser();
  const registerResponse = registerUser(user);
  check(registerResponse, {
    "register is 201": (r) => r.status === 201,
  });

  const loginResponse = loginUser(user);
  check(loginResponse, {
    "login is 200": (r) => r.status === 200,
  });

  if (loginResponse.status === 200) {
    const firstRefreshToken = loginResponse.json("refresh_token");
    const refreshResponse = refreshToken(firstRefreshToken);

    check(refreshResponse, {
      "refresh is 200": (r) => r.status === 200,
    });

    if (refreshResponse.status === 200) {
      const logoutResponse = logout(refreshResponse.json("refresh_token"));
      check(logoutResponse, {
        "logout is 200": (r) => r.status === 200,
      });
    }
  }

  sleep(1);
}
