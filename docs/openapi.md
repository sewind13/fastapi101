# OpenAPI And Docs

This template exposes OpenAPI for local development and API exploration.

## OpenAPI Location

The OpenAPI schema is mounted at:

- `<API__V1_PREFIX>/openapi.json`

With the default config, that means:

- `/api/v1/openapi.json`

Source:

- [`app/main.py`](../app/main.py)

## Swagger UI

Because the template uses standard FastAPI app wiring, Swagger UI is available at:

- `/docs`

And ReDoc is available at:

- `/redoc`

Unless you later customize or disable them.

## Why This Matters

OpenAPI is useful for:

- browsing available endpoints quickly
- checking schema changes while developing
- testing request payloads in the browser
- generating API clients if your workflow needs that

## Recommended Local Workflow

1. Start the app with `make up`.
2. Open `/docs`.
3. Use `POST /api/v1/auth/login` to get a token pair if you want to test the raw login response.
4. Click `Authorize` for protected routes.
5. In this project, Swagger usually shows the OAuth2 password form, so fill in:
   - `username`
   - `password`
   - leave `client_id` and `client_secret` empty unless you add a real OAuth client later
6. Swagger will fetch and attach the bearer token for you.
7. Exercise new endpoints while building them.

## Notes About `Authorize`

If the Swagger dialog shows a username/password form instead of a single bearer-token field, that is expected for this template.

This app uses FastAPI's OAuth2 password flow for the docs UI, so the most common way to authorize in Swagger is:

1. create or bootstrap a user
2. click `Authorize`
3. enter the user's username and password
4. submit the form

If you prefer testing with a raw token, you can still call `POST /api/v1/auth/login` manually, copy the returned `access_token`, and use another client such as curl or Postman.

## Useful Routes To Try In Swagger

After authorizing successfully, a good local smoke flow is:

1. `GET /api/v1/auth/me`
2. `GET /api/v1/billing/me/summary`
3. `GET /api/v1/billing/me/balance/item_create`
4. `POST /api/v1/items/`
5. `GET /api/v1/billing/me/usage`
6. `GET /api/v1/billing/me/usage/report`

This sequence is useful because it exercises auth, self-service billing, the quota example on `items`, and usage reporting in one pass.

## Production Notes

For real production you may want to:

- keep docs enabled only in internal/staging environments
- protect docs behind auth or network controls
- keep OpenAPI public only if your product intentionally exposes a public API surface

If you want that behavior, the template can be extended later with env-based docs toggles.
