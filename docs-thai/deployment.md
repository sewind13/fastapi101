# Deployment Guide

ไฟล์นี้อธิบายว่า template นี้ควรถูกนำไปรันนอก local development อย่างไร และมีเรื่องอะไรที่ควรเช็กก่อนถือว่า deployment พร้อม

## แนวคิดหลัก

deployment ที่ดีของ repo นี้ควร:

- ใช้ image เดียวกันระหว่าง app, jobs, worker, และ dispatcher
- ใช้ Alembic migrations เป็น source of truth
- แยก API, worker, และ outbox dispatcher เป็นคนละ process
- มี health checks, metrics, และ monitoring ขั้นต่ำ
- ไม่ใช้ค่าตัวอย่าง local เป็น production secrets

## baseline deployment แบบ end-to-end ที่แนะนำ

ถ้าจะใช้ template นี้ใน shared env หรือ production-like env จริง ให้คิดเป็นหลาย runtime units:

- API deployment
- worker deployment
- outbox-dispatcher deployment
- migration job หรือ release step
- Postgres ที่แยกจาก app
- Redis ที่แยกจาก app เมื่อเปิด distributed features
- broker ที่แยกจาก app เมื่อเปิด worker flow
- ingress / reverse proxy / load balancer
- metrics และ log pipeline

baseline ที่แนะนำ:

- API เป็น stateless replicas
- worker แยกจาก API
- outbox dispatcher แยกจาก API และ worker
- migrations รันก่อนเปิด traffic ให้ version ใหม่
- Postgres และ Redis อยู่นอก app deployment boundary

ตัวอย่าง production-oriented env baseline ดูได้ที่:

- [/.env.prod.example](/Users/pluto/Documents/git/fastapi101/.env.prod.example)
- [deploy/helm/fastapi-template](/Users/pluto/Documents/git/fastapi101/deploy/helm/fastapi-template)

ตอนนี้ workflow CI หลักก็มี deployment guardrails พื้นฐานเพิ่มแล้ว:

- [/.github/workflows/ci.yml](/Users/pluto/Documents/git/fastapi101/.github/workflows/ci.yml)
- รัน `actionlint` เพื่อตรวจ workflow files
- รัน `helm lint`, `helm template`, และ `kubeconform` กับ Helm chart ที่มากับ repo
- ให้ validation พวกนี้ผ่านก่อนค่อยไปรัน Python quality job หลัก

## Production-like Docker Flow

ถ้าจะลอง runtime shape ที่ใกล้ production มากขึ้นใน local ให้ใช้:

```bash
make up-prod
make down-prod
make ps-prod
make logs-prod
```

mode นี้:

- ใช้ image ที่ build แล้วจริง
- ไม่ bind mount source code
- ไม่ต้องติดตั้ง packages ระหว่าง container startup
- ใกล้กับ runtime จริงมากกว่า dev mode
- bind ports เป็น `127.0.0.1` เป็นค่าเริ่มต้นเพื่อให้ปลอดภัยขึ้นใน local
- แยก local credentials ออกจาก production secrets ชัดกว่าเดิม

## Container start flow

web container ปกติจะเริ่มผ่าน script ที่ทำประมาณนี้:

1. `alembic upgrade head`
2. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

ถ้าเปิด worker/outbox:

- worker ควรรันเป็น process แยก
- outbox dispatcher ก็ควรรันเป็น process แยก

แนวทาง production ที่แนะนำ:

- scale worker แยกจาก API
- ใช้ image เดียวกันแต่ command คนละตัว
- ใช้ Redis-backed idempotency ถ้ามีหลาย worker replicas
- lock down ops endpoints ด้วย role model ที่ชัด

## Migration Strategy

Alembic คือ schema source of truth ของระบบนี้

workflow ปกติ:

1. แก้ SQLModel models
2. สร้าง migration
3. apply migration
4. รัน tests

คำสั่งที่เกี่ยวข้อง:

```bash
make migration m="add orders table"
make migrate
make psql
```

สำหรับ deploy จริง ควรเลือกวิธีใดวิธีหนึ่ง:

- init job รัน migration ก่อน app รับ traffic
- release pipeline รัน migration ก่อน switch traffic
- migration job แยกจาก app rollout

ค่า default ที่แนะนำสำหรับ production:

- ให้ migration job หรือ release step รันก่อน
- API rollout เกิดหลัง migration ผ่านแล้ว
- อย่าคิดว่า rollback ของ release เท่ากับ rollback ของ database schema เสมอไป

สำคัญ:

- อย่า fallback ไปใช้ `create_all()` แทน migration flow

## Health Endpoints

endpoint ที่มี:

- `/health`
- `/health/live`
- `/health/ready`

หลักการใช้:

- `/health/live` สำหรับ liveness
- `/health/ready` สำหรับ readiness
- อย่าใช้ `/health` แทน readiness

คำแนะนำในการ wire production:

- ingress หรือ load balancer ใช้ `/health/ready`
- process supervisor หรือ container runtime ใช้ `/health/live`
- dashboard และ monitoring เก็บทั้งสองแบบ

readiness อาจเช็ก:

- database
- Redis
- S3
- queue/broker

ขึ้นกับว่าคุณเปิด dependency checks อะไรไว้

## Reverse Proxy / Ingress

ในการ deploy จริง มักมี reverse proxy หรือ ingress อยู่หน้าระบบ

ชั้นนี้มักรับผิดชอบ:

- TLS termination
- public routing
- edge rate limiting / WAF
- forwarded client IP

ถ้าจะ trust `X-Forwarded-For` หรือ `X-Real-IP` ใน app:

- เปิด `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS=true`
- ตั้ง `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`
- เช็กให้ชัดว่า direct peer ที่ app เห็นเป็น proxy tier จริง

อย่า trust forwarded IP headers จาก arbitrary clients

### Kubernetes / Ingress note

ถ้าใช้ ingress:

- ใช้ `/health/live` เป็น liveness probe
- ใช้ `/health/ready` เป็น readiness probe
- เช็กว่าการ forward client IP ยังถูกต้องหลัง ingress/load balancer เปลี่ยน
- อย่าปล่อย `/metrics` ไป public route โดยไม่ตั้งใจ

## Metrics และ Monitoring

ถ้าเปิด metrics:

- path หลักคือ `/metrics`
- production ควรมี `METRICS__AUTH_TOKEN`
- ควร scrape ผ่าน internal network
- ไม่ควร expose สู่ public internet โดยไม่ตั้งใจ

baseline metrics ตอนนี้ครอบ:

- HTTP request count / latency / in-flight
- application exceptions
- readiness checks
- auth events
- maintenance jobs
- worker events / queue depth
- outbox dispatch

ตัวอย่าง Kubernetes ใน repo ตอนนี้แยก:

- non-secret config ไว้ใน [deploy/kubernetes/app-configmap.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/app-configmap.yaml)
- secret-bearing values ไว้ใน [deploy/kubernetes/app-secret.example.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/app-secret.example.yaml)
- migration job แยกอยู่ที่ [deploy/kubernetes/migration-job.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/migration-job.yaml)
- Helm baseline อยู่ที่ [deploy/helm/fastapi-template](/Users/pluto/Documents/git/fastapi101/deploy/helm/fastapi-template)

## Alerting starting points

ตัวอย่าง threshold เริ่มต้น:

- `5xx rate > 1%` นาน 5 นาที
- `p95 latency > 500ms` นาน 10 นาที
- in-flight requests สูงผิดปกตินาน 5-10 นาที
- database readiness failed นาน 2 นาที
- critical dependency readiness failed นาน 2-5 นาที

threshold เหล่านี้ต้อง tune ตาม product จริง ไม่ใช่ใช้เป็นค่าตายตัวเสมอไป

## Rate Limiting ใน production

ถ้ามีหลาย instance:

- ใช้ `AUTH_RATE_LIMIT__BACKEND="redis"`
- ตั้ง `AUTH_RATE_LIMIT__REDIS_URL`

อย่าใช้ `memory` backend เป็น baseline สำหรับ production multi-instance

## Monitoring examples ที่ repo มีให้

repo นี้มีตัวอย่างไฟล์ monitoring เช่น:

- `deploy/monitoring/prometheus.yml`
- `deploy/monitoring/prometheus-alerts.yml`
- `deploy/monitoring/alertmanager.yml`
- Grafana dashboard/provisioning examples
- `docker-compose.monitoring.yml`

local workflow แบบง่าย:

```bash
make up-monitoring
```

จากนั้นเปิด:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Alertmanager: `http://localhost:9093`

## Deployment artifacts ที่มีใน repo

- Kubernetes manifests ใน `deploy/kubernetes`
- Helm baseline ใน `deploy/helm/fastapi-template`
- Nginx example ใน `deploy/nginx`
- monitoring examples ใน `deploy/monitoring`
- compose files สำหรับ local, monitoring, และ load test

สิ่งเหล่านี้เป็น baseline ไม่ใช่ turnkey production manifests ที่ใช้ได้ทันทีโดยไม่ปรับ

workflow ที่แนะนำ:

- ถ้าใช้ Kustomize:
  apply base manifests ก่อน แล้วค่อย apply `deploy/kubernetes/migration-job.yaml` ตอน release
- ถ้าใช้ Helm:
  copy `values.yaml` หรือใช้ `deploy/helm/fastapi-template/values.prod.example.yaml` เป็นจุดเริ่มต้น, เปลี่ยน image/hostnames/secrets, แล้วตัดสินใจก่อนว่า migration job จะให้ Helm สร้างหรือจะไปรันใน release system แยก

ตัวอย่าง GitHub Actions release workflow ดูได้ที่:

- [/.github/workflows/release-example.yml](/Users/pluto/Documents/git/fastapi101/.github/workflows/release-example.yml)
- [/.github/workflows/helm-validate-example.yml](/Users/pluto/Documents/git/fastapi101/.github/workflows/helm-validate-example.yml)
- [/.github/workflows/release-eks-oidc-example.yml](/Users/pluto/Documents/git/fastapi101/.github/workflows/release-eks-oidc-example.yml)
- [/.github/workflows/release-gke-oidc-example.yml](/Users/pluto/Documents/git/fastapi101/.github/workflows/release-gke-oidc-example.yml)
- [/.github/workflows/release-aks-oidc-example.yml](/Users/pluto/Documents/git/fastapi101/.github/workflows/release-aks-oidc-example.yml)
- [/.github/workflows/workflow-validate-example.yml](/Users/pluto/Documents/git/fastapi101/.github/workflows/workflow-validate-example.yml)

workflow นี้สมมติว่ามี repository secret ชื่อ `KUBE_CONFIG` และจะ:

- build และ push image
- render migration job จาก Helm chart ด้วย image tag เดียวกัน
- deploy release หลักโดยปิด `migrationJob.enabled`
- wait rollout ของ API, worker, และ dispatcher

ก่อนใช้จริงควรปรับให้เข้ากับ auth model, namespace naming, และ release conventions ของทีมก่อน

ถ้าจะดูตัวอย่างที่ผูกกับ provider จริง ฝั่ง EKS OIDC workflow จะสมมติว่ามี repository variables:

- `AWS_REGION`
- `EKS_CLUSTER_NAME`
- `AWS_ROLE_ARN`

และใช้ GitHub OIDC + `aws eks update-kubeconfig` แทนการเก็บ kubeconfig ตรง ๆ

ตอนนี้ EKS workflow เป็นตัวอย่างที่ใกล้ production ที่สุดใน repo แล้ว และมีเพิ่มอีกว่า:

- เช็ก required repository variables ล่วงหน้า
- ล็อก concurrency ตาม Helm release และ namespace
- ดึง migration logs หลัง job สำเร็จ
- เปิดให้เลือกว่าจะ wait worker และ outbox dispatcher rollout หรือไม่
- สรุป deployed workloads หลัง `helm upgrade` เสร็จ

ส่วน GKE OIDC workflow จะสมมติว่ามี repository variables:

- `GCP_PROJECT_ID`
- `GKE_CLUSTER_NAME`
- `GKE_CLUSTER_LOCATION`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

และใช้ `google-github-actions/auth` กับ `get-gke-credentials`

ส่วน AKS OIDC workflow จะสมมติว่ามี repository variables:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AKS_RESOURCE_GROUP`
- `AKS_CLUSTER_NAME`

และใช้ `azure/login` กับ `azure/aks-set-context`

ถ้าอยาก validate workflow files เองใน CI โดยยังไม่แตะ release flow ให้เริ่มจาก:

- [/.github/workflows/workflow-validate-example.yml](/Users/pluto/Documents/git/fastapi101/.github/workflows/workflow-validate-example.yml)

ซึ่งใช้ `actionlint` เพื่อจับ syntax และ mistake ที่พบบ่อยของ GitHub Actions

ส่วน Helm validation workflow ตอนนี้สาธิต:

- `helm lint`
- `helm template` ด้วยค่า default
- `helm template` ด้วย production example values
- `kubeconform` เพื่อตรวจ schema ของ rendered manifests

## หลักการ rollback ที่ควรใช้

application rollback กับ data restore เป็นคนละเรื่อง

rule ที่แนะนำ:

- ถ้า release พัง ให้ rollback app image ก่อน
- ถ้า migration มีปัญหา อย่ารีบ downgrade database แบบ ad hoc ถ้ายังไม่ได้ออกแบบและซ้อมไว้
- ถ้าปัญหาเป็น data corruption หรือ destructive schema issue ให้ใช้ remediation migration หรือ restore-from-backup plan

ลำดับที่ปลอดภัยกว่าคือ:

1. หยุด traffic cutover
2. ย้อน API กลับไป image ก่อนหน้า
3. ย้อน worker และ dispatcher กลับถ้าจำเป็น
4. ตรวจว่า app เก่ายังทำงานกับ schema ปัจจุบันได้ไหม
5. ถ้าปัญหาอยู่ที่ schema จริง ค่อยใช้ plan ที่เตรียมไว้สำหรับ schema remediation หรือ restore

## สิ่งที่ควรมีใน deployment จริง

- app process
- DB ที่ migrate แล้ว
- metrics scraping
- log pipeline
- secret manager / platform secret store
- worker/outbox dispatcher ถ้าเปิด async flow

## Checklist ก่อนถือว่า deploy พร้อม

- เปลี่ยน production secrets แล้ว
- migration ถูก apply แล้ว
- health probes ถูกตั้งถูก path
- metrics ถูกป้องกันด้วย auth/network controls
- ops endpoints ใช้ role ที่ถูกต้อง
- worker/outbox ใช้ broker และ retry/DLQ config ถูกต้อง
- trusted proxy CIDRs ถูกตั้งถูกจริงก่อนเปิด forwarded-header trust
- alert thresholds ถูก tune ตาม profile ของระบบจริง

อ่านต่อ:

- [production-topology.md](/Users/pluto/Documents/git/fastapi101/docs-thai/production-topology.md)
- [observability.md](/Users/pluto/Documents/git/fastapi101/docs-thai/observability.md)
- [first-deploy-checklist.md](/Users/pluto/Documents/git/fastapi101/docs-thai/first-deploy-checklist.md)
- [secret-management.md](/Users/pluto/Documents/git/fastapi101/docs-thai/secret-management.md)

อ่านฉบับอังกฤษละเอียดได้ที่ [docs/deployment.md](/Users/pluto/Documents/git/fastapi101/docs/deployment.md)
