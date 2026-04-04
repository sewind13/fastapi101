import http from "k6/http";
import { check, fail } from "k6";

export const config = {
  baseUrl: __ENV.BASE_URL || "http://localhost:8000",
  usernamePrefix: __ENV.USERNAME_PREFIX || "k6user",
  password: __ENV.PASSWORD || "strongpassword123",
  itemsEnabled: (__ENV.ITEMS_ENABLED || "true").toLowerCase() === "true",
};

export function uniqueSuffix() {
  return `${__VU}-${__ITER}-${Date.now()}`;
}

export function buildUser() {
  const suffix = uniqueSuffix();
  return {
    username: `${config.usernamePrefix}-${suffix}`,
    email: `${config.usernamePrefix}-${suffix}@example.com`,
    password: config.password,
  };
}

export function registerUser(user) {
  const response = http.post(
    `${config.baseUrl}/api/v1/users/`,
    JSON.stringify(user),
    {
      headers: { "Content-Type": "application/json" },
      tags: { scenario_group: "auth", endpoint: "users.register" },
    },
  );

  check(response, {
    "register status is 201": (r) => r.status === 201,
  });

  return response;
}

export function loginUser(user) {
  const response = http.post(
    `${config.baseUrl}/api/v1/auth/login`,
    {
      username: user.username,
      password: user.password,
    },
    {
      tags: { scenario_group: "auth", endpoint: "auth.login" },
    },
  );

  check(response, {
    "login status is 200": (r) => r.status === 200,
    "login returns access token": (r) => Boolean(r.json("access_token")),
  });

  return response;
}

export function authHeaders(accessToken) {
  return {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  };
}

export function ensureAuthenticatedUser() {
  const user = buildUser();
  const registerResponse = registerUser(user);
  if (registerResponse.status !== 201) {
    fail(`user registration failed with status ${registerResponse.status}`);
  }

  const loginResponse = loginUser(user);
  if (loginResponse.status !== 200) {
    fail(`user login failed with status ${loginResponse.status}`);
  }

  return {
    user,
    accessToken: loginResponse.json("access_token"),
    refreshToken: loginResponse.json("refresh_token"),
  };
}

export function getCurrentUser(accessToken) {
  return http.get(`${config.baseUrl}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    tags: { scenario_group: "read", endpoint: "auth.me" },
  });
}

export function listItems(accessToken) {
  return http.get(`${config.baseUrl}/api/v1/items/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    tags: { scenario_group: "read", endpoint: "items.list" },
  });
}

export function createItem(accessToken, payload) {
  return http.post(
    `${config.baseUrl}/api/v1/items/`,
    JSON.stringify(payload),
    {
      headers: authHeaders(accessToken),
      tags: { scenario_group: "write", endpoint: "items.create" },
    },
  );
}

export function refreshToken(refreshToken) {
  return http.post(
    `${config.baseUrl}/api/v1/auth/refresh`,
    JSON.stringify({ refresh_token: refreshToken }),
    {
      headers: { "Content-Type": "application/json" },
      tags: { scenario_group: "auth", endpoint: "auth.refresh" },
    },
  );
}

export function logout(refreshToken) {
  return http.post(
    `${config.baseUrl}/api/v1/auth/logout`,
    JSON.stringify({ refresh_token: refreshToken }),
    {
      headers: { "Content-Type": "application/json" },
      tags: { scenario_group: "auth", endpoint: "auth.logout" },
    },
  );
}
