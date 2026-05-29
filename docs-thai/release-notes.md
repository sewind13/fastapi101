# Release Notes

## v1.0.3 - 2026-05-30

patch release สำหรับ production-readiness quality gates และ immutable deployment examples

### สิ่งที่แก้

- เพิ่ม `types-pyyaml` ใน dev dependencies เพื่อให้ `uv run mypy app tests` ผ่านตาม quality gate ที่ repo ระบุไว้
- ปรับ typing ของ test ที่ validate Helm values settings ให้ mypy ยอมรับ `_env_file=None` ซึ่งเป็น runtime override ที่ตั้งใจใช้
- เปลี่ยน image tag แบบ mutable `latest` ใน raw Kubernetes manifests และ release workflow examples เป็น example tag แบบ immutable คือ `1.0.3`
- bump package, lockfile, และ Helm chart/app versions เป็น `1.0.3`

### สิ่งที่ adopter ต้องทำ

- adopter ใหม่ควรใช้ `v1.0.3`
- ก่อน deploy ให้เปลี่ยน image repository และ immutable tag ตัวอย่างเป็น image ของ product จริง

## v1.0.2 - 2026-05-30

patch release สำหรับ Helm release safety และ CI coverage

### สิ่งที่แก้

- เพิ่ม CI validation ที่โหลด Helm values ผ่าน startup settings validation ของแอปจริง ไม่ใช่ตรวจแค่ manifest schema
- เพิ่ม `scripts/validate_helm_settings.py` เพื่อให้ local และ CI ตรวจ Helm values ก่อน release ได้
- เปลี่ยน Helm default image tag จาก `latest` เป็น example tag แบบ immutable คือ `1.0.2`

### สิ่งที่ adopter ต้องทำ

- adopter ใหม่ควรใช้ `v1.0.2`
- ก่อน deploy ให้เปลี่ยน image repository และ immutable tag ตัวอย่างเป็น image ของ product จริง

## v1.0.1 - 2026-05-30

patch release สำหรับ Helm chart baseline

### สิ่งที่แก้

- แก้ `deploy/helm/fastapi-template/values.yaml` ให้ Helm default แบบ lean `core-only` ผ่าน production settings validation
- default chart จะปิด auth rate limiting เมื่อยังไม่ได้เปิด Redis ส่วน Redis-backed rate limiting ยังใช้ได้ผ่าน preset `redis-enabled` และ `full-async`
- เพิ่ม unit test ที่โหลด default Helm values เข้า `Settings(_env_file=None)` เพื่อกัน chart/config drift ในอนาคต

### สิ่งที่ adopter ต้องทำ

- ถ้าใช้ default Helm values ให้ใช้ `v1.0.1` แทน `v1.0.0`
- ถ้าจะเปิด auth rate limiting ใน production ให้ตั้ง `AUTH_RATE_LIMIT__ENABLED=true`, `AUTH_RATE_LIMIT__BACKEND=redis`, และ `AUTH_RATE_LIMIT__REDIS_URL`

## v1.0.0 - 2026-05-29

baseline แรกที่ถือว่า stable สำหรับ production-grade product template

### สถานะ

- Stability: stable template baseline
- Breaking changes สำหรับ adopter เดิม: ไม่มี เพราะเป็น stable release แรก
- tag ที่แนะนำ: `v1.0.0`

### สิ่งสำคัญใน release นี้

- โครงสร้าง FastAPI แบบ production-minded: routes บาง, service/repository layering, schemas ชัด, และใช้ `app.main:app` เป็น ASGI entrypoint
- settings แยกตาม domain, มี production validation, compatibility shims สำหรับ env เก่า, และใช้ nested env variables
- workflow DB ยึด Alembic เป็นหลัก และแยก migration ออกจาก API startup
- Docker runtime แข็งขึ้นด้วย multi-stage build, optional runtime extras, และ non-root user
- มี Helm/Kubernetes baseline โดย Helm default เป็น profile แบบ lean `core-only` ส่วน `values.prod.example.yaml` เป็นตัวอย่าง full async/Redis/ops
- auth baseline มี JWT access/refresh tokens, revocation, email verification, password reset, account lockout, rate limiting, และ password policy
- observability และ operations surfaces ถูกวางเป็น opt-in production capabilities
- CI ครอบคลุม format, lint, typecheck, tests, workflow validation, dependency audit, secret scan, Docker builds, Trivy image scan, และ SBOM
- docs อังกฤษและไทยครอบคลุม architecture, configuration, deployment, security, operations, และ adoption profiles

### สิ่งที่ adopter ต้องทำ

- เปลี่ยน secrets และ URLs ตัวอย่างทั้งหมดก่อน deploy
- เลือก adoption preset: `core-only`, `redis-enabled`, หรือ `full-async`
- ตัดสินใจว่าจะเก็บ sample `items` module และ entitlement example ไว้หรือไม่
- รัน quality gates ครบก่อน tag product-specific fork
- บันทึกว่า product เริ่มจาก template baseline `v1.0.0`

### Validation

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run pytest -q`
- `helm lint deploy/helm/fastapi-template`
- `helm template fastapi-template deploy/helm/fastapi-template`
- `actionlint .github/workflows/ci.yml`
- `pip-audit --no-deps --disable-pip`
- `gitleaks detect`
- Docker core และ full image smoke checks
