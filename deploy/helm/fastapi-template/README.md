# FastAPI Template Helm Baseline

This chart is a baseline example, not a turnkey production chart.

It includes templates for:

- API deployment and service
- optional ingress
- optional HPA
- worker deployment
- outbox-dispatcher deployment
- migration job
- ConfigMap and Secret split

Typical flow:

1. copy `values.yaml`
2. replace image, hostnames, and secrets
3. decide whether the migration job should be run by Helm or by your release pipeline
4. disable worker or dispatcher if your service does not use them

Useful files:

- `values.yaml`
  baseline chart defaults
- `values.prod.example.yaml`
  production-oriented example values file you can copy into your own environment-specific values file
- `../../../.github/workflows/helm-validate-example.yml`
  example CI workflow for `helm lint`, `helm template`, and `kubeconform` render validation
- `../../../.github/workflows/ci.yml`
  the main CI workflow now includes workflow validation and Helm render validation before the Python checks run
- `../../.github/workflows/release-example.yml`
  example `build -> migrate -> deploy` workflow that renders the migration job from this chart and disables it during the main Helm upgrade
- `../../../.github/workflows/release-eks-oidc-example.yml`
  provider-specific example for GitHub OIDC plus AWS EKS, with preflight variable checks and serialized release concurrency
- `../../../.github/workflows/release-gke-oidc-example.yml`
  provider-specific example for GitHub OIDC plus Google GKE
- `../../../.github/workflows/release-aks-oidc-example.yml`
  provider-specific example for GitHub OIDC plus Azure AKS
- `../../../.github/workflows/workflow-validate-example.yml`
  example `actionlint` workflow for validating GitHub Actions files
