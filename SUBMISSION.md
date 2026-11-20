# Assignment Submission Summary

This document provides direct answers and references for each required item listed in the **Intern Assignment Instructions for Submission**.

---

### Item 1: Dockerfile for the Flask Application
- **Location**: [`flask-mongodb-app/Dockerfile`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/flask-mongodb-app/Dockerfile)
- **Features**:
  - Base Image: `python:3.9-slim` for minimal size, fast deployment, and minimal attack surface.
  - Security: Executes as non-root user `appuser` (UID 1000).
  - Healthcheck: Native container health check polling `/healthz` via curl.
  - Layer Caching: Dependency installation separated from application source code.

---

### Item 2: Instructions to Build and Push Docker Image
- **Location in README**: Section 4 of [`README.md`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/README.md#4-docker-instructions-build-tag--push)
- **Commands**:
  ```bash
  # 1. Build Docker image
  docker build -t flask-mongodb-app:latest ./flask-mongodb-app

  # 2. Tag for container registry (Docker Hub / GHCR)
  docker tag flask-mongodb-app:latest <your-username>/flask-mongodb-app:v1.0.0
  docker tag flask-mongodb-app:latest <your-username>/flask-mongodb-app:latest

  # 3. Push to registry
  docker login
  docker push <your-username>/flask-mongodb-app:v1.0.0
  docker push <your-username>/flask-mongodb-app:latest

  # Alternative for Minikube local testing without remote push:
  eval $(minikube docker-env)
  docker build -t flask-mongodb-app:latest ./flask-mongodb-app
  ```

---

### Item 3: Kubernetes YAML Files for All Resources Created
All Kubernetes manifests are located in [`k8s/`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/) and configured for deployment via Kustomize:
1. **Namespace**: [`k8s/00-namespace.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/00-namespace.yaml) — dedicated `flask-mongo-app` namespace.
2. **MongoDB Secret**: [`k8s/01-mongo-secret.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/01-mongo-secret.yaml) — root username & password for MongoDB.
3. **MongoDB ConfigMap**: [`k8s/02-mongo-configmap.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/02-mongo-configmap.yaml) — port & default database name.
4. **Persistent Volume & Claim**: [`k8s/03-mongo-pv-pvc.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/03-mongo-pv-pvc.yaml) — 1Gi storage volume mounted at `/data/db`.
5. **MongoDB StatefulSet**: [`k8s/04-mongo-statefulset.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/04-mongo-statefulset.yaml) — authenticated MongoDB with probes & resource constraints.
6. **MongoDB Service**: [`k8s/05-mongo-service.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/05-mongo-service.yaml) — internal `ClusterIP` service (port 27017).
7. **Flask ConfigMap**: [`k8s/06-flask-configmap.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/06-flask-configmap.yaml) — app configuration parameters.
8. **Flask Secret**: [`k8s/07-flask-secret.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/07-flask-secret.yaml) — authenticated connection URI.
9. **Flask Deployment**: [`k8s/08-flask-deployment.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/08-flask-deployment.yaml) — 2 replicas, probes, and resource constraints.
10. **Flask Service**: [`k8s/09-flask-service.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/09-flask-service.yaml) — external `NodePort` service (port 30005).
11. **Horizontal Pod Autoscaler**: [`k8s/10-flask-hpa.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/10-flask-hpa.yaml) — autoscale min 2 to max 5 replicas at 70% CPU target.
12. **Kustomization**: [`k8s/kustomization.yaml`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/k8s/kustomization.yaml) — unified multi-resource deployer.

---

### Item 4: README with Detailed Steps to Deploy on Minikube
- **Location**: Section 5 of [`README.md`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/README.md#5-part-2-kubernetes-setup-on-minikube)
- **Automated scripts**:
  - Linux/macOS: [`scripts/deploy.sh`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/scripts/deploy.sh)
  - Windows: [`scripts/deploy.ps1`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/scripts/deploy.ps1)

---

### Item 5: Explanation of DNS Resolution for Inter-Pod Communication
- **Location**: Section 6 of [`README.md`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/README.md#6-deep-dive-dns-resolution-in-kubernetes)
- **Summary**:
  - CoreDNS handles service discovery inside Kubernetes.
  - Every pod gets an injected `/etc/resolv.conf` with search domains (`flask-mongo-app.svc.cluster.local`, etc.).
  - Flask resolves `mongodb-service` directly to the `ClusterIP` virtual IP.
  - `kube-proxy` maps the virtual IP to the healthy MongoDB pod endpoint using Linux kernel `iptables` / `IPVS`.
  - StatefulSet also provides predictable pod FQDN: `mongodb-0.mongodb-service.flask-mongo-app.svc.cluster.local`.

---

### Item 6: Explanation of Resource Requests and Limits
- **Location**: Section 7 of [`README.md`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/README.md#7-deep-dive-resource-requests-and-limits)
- **Configured Values**:
  - `requests`: `cpu: 200m` (0.2 CPU), `memory: 250Mi` (250M)
  - `limits`: `cpu: 500m` (0.5 CPU), `memory: 500Mi` (500M)
- **Summary**:
  - **Requests** govern scheduling decisions (`kube-scheduler`) and guarantee reservations.
  - **Limits** are hard caps enforced by Linux `cgroups`. CPU overages result in CFS throttling; memory overages trigger kernel OOM Killer (exit code 137).
  - Both Flask and MongoDB pods run under the **Burstable** QoS class, balancing resource efficiency with burst elasticity.

---

### Item 7: Design Choices & Alternatives Considered
- **Location**: Section 8 of [`README.md`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/README.md#8-design-choices--alternatives-considered)
- **Key Decisions**:
  1. **MongoDB StatefulSet over Deployment**: Prevents split-brain and multi-attach data corruption; guarantees persistent network identity and orderly lifecycle.
  2. **ClusterIP for MongoDB**: Enforces strict internal-only cluster security; prevents external database intrusion.
  3. **NodePort for Flask**: Exposes application on port 30005 for simple local workstation access without needing cloud provider LoadBalancers.
  4. **Native Container Authentication**: Configured `--auth` with credentials in Kubernetes Secrets rather than plaintext in configmaps or hardcoded strings.

---

### Item 8: Cookie Point 1 — Benefits of Virtual Environments for Python
- **Location**: Section 2 of [`README.md`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/README.md#2-cookie-point-1-benefits-of-using-a-virtual-environment-for-python-applications)
- Covers dependency isolation, OS integrity protection, deterministic builds (`requirements.txt`), security sandboxing, and non-root execution.

---

### Item 9: Cookie Point 2 — Testing Scenarios, High Traffic Simulation & Results
- **Location**: Section 9 of [`README.md`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/README.md#9-cookie-point-2-testing-scenarios-high-traffic-simulation--results)
- **Scenarios Documented**:
  1. Functional CRUD test of `/`, POST `/data`, GET `/data`, and `/healthz` with MongoDB authentication.
  2. Data persistence test: forced deletion of `mongodb-0` pod, demonstrating zero data loss upon pod recreation.
  3. High-traffic load simulation via [`scripts/simulate_traffic.py`](file:///c:/Users/dhruv/Downloads/faralpha%20submission/scripts/simulate_traffic.py):
     - Triggered CPU utilization above 70% (reached 145%).
     - Verified HPA auto-scaled pods from 2 -> 3 -> 4 -> 5 replicas.
     - Verified graceful scale-down back to 2 replicas upon load completion.
  4. Complete documentation of issues encountered and resolutions (Metrics-server TLS flags, Werkzeug/MarkupSafe compatibility, and DB initial boot auth race condition).
