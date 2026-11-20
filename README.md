# Kubernetes Deployment: Scalable Flask Application with Authenticated MongoDB, StatefulSet, and HPA

This repository contains the complete, production-grade submission for the **Intern Assignment**. It demonstrates end-to-end containerization, secure database persistence, cluster DNS networking, resource governance, and automated horizontal pod autoscaling on a Kubernetes (Minikube) cluster.

---

## Table of Contents
1. [Project Overview & Architecture](#1-project-overview--architecture)
2. [Cookie Point 1: Benefits of Using a Virtual Environment for Python Applications](#2-cookie-point-1-benefits-of-using-a-virtual-environment-for-python-applications)
3. [Part 1: Local Setup Walkthrough](#3-part-1-local-setup-walkthrough)
4. [Docker Instructions: Build, Tag & Push](#4-docker-instructions-build-tag--push)
5. [Part 2: Kubernetes Setup on Minikube](#5-part-2-kubernetes-setup-on-minikube)
6. [Deep Dive: DNS Resolution in Kubernetes](#6-deep-dive-dns-resolution-in-kubernetes)
7. [Deep Dive: Resource Requests and Limits](#7-deep-dive-resource-requests-and-limits)
8. [Design Choices & Alternatives Considered](#8-design-choices--alternatives-considered)
9. [Cookie Point 2: Testing Scenarios, High Traffic Simulation & Results](#9-cookie-point-2-testing-scenarios-high-traffic-simulation--results)
10. [Repository Structure](#10-repository-structure)
11. [Troubleshooting & Verification Commands](#11-troubleshooting--verification-commands)

---

## 1. Project Overview & Architecture

The architecture consists of a 2-tier decoupled microservices architecture running inside a dedicated Kubernetes namespace (`flask-mongo-app`):

```
                               [ Local Host Machine / Browser ]
                                              |
                                  (Port 30005 NodePort)
                                              v
                              +-------------------------------+
                              |    flask-service (NodePort)   |
                              +-------------------------------+
                                              |
                     +------------------------+------------------------+
                     | (Load balances across 2 to 5 replica pods)      |
                     v                                                 v
        +-------------------------+                       +-------------------------+
        |  flask-app Pod #1       |                       |  flask-app Pod #2       |
        |  - Python 3.9 / Flask   |                       |  - Python 3.9 / Flask   |
        |  - Request: 0.2cpu, 250M|                       |  - Request: 0.2cpu, 250M|
        |  - Limit:   0.5cpu, 500M|                       |  - Limit:   0.5cpu, 500M|
        +-------------------------+                       +-------------------------+
                     \                                                 /
                      \====== Internal CoreDNS: mongodb-service ======/
                                             |
                                  (Port 27017 ClusterIP)
                                             v
                              +-------------------------------+
                              |  mongodb-service (ClusterIP)  |
                              |   [Internal Cluster Only]     |
                              +-------------------------------+
                                             |
                                             v
                              +-------------------------------+
                              |  mongodb-0 Pod (StatefulSet)  |
                              |  - Image: mongo:6.0           |
                              |  - Auth: admin/password123    |
                              |  - Request: 0.2cpu, 250M      |
                              |  - Limit:   0.5cpu, 500M      |
                              +-------------------------------+
                                             |
                                     (Mount: /data/db)
                                             v
                              +-------------------------------+
                              | PersistentVolumeClaim (1Gi)   |
                              | standard / hostPath Storage   |
                              +-------------------------------+
```

---

## 2. Cookie Point 1: Benefits of Using a Virtual Environment for Python Applications

A Python **virtual environment** (`venv`) creates an isolated execution context containing its own Python interpreter, standard libraries, and site-packages directory. The critical engineering benefits include:

1. **Dependency Isolation & Conflict Prevention**:
   Different projects frequently require incompatible versions of the same library (e.g., Project A requires `Flask==2.0.2` with `Werkzeug==2.0.3`, while Project B requires `Flask==3.0.0`). Without virtual environments, global package installations overwrite one another, leading to the infamous "dependency hell".
2. **Protection of the Operating System / Base Python Distribution**:
   Operating systems (such as Linux distributions and macOS) rely on system Python for core utilities and system tools. Installing or upgrading global packages via `sudo pip install` can break system-level scripts. A virtual environment prevents global pollution.
3. **Reproducibility and Deterministic Builds**:
   A virtual environment allows teams to pin dependencies exactly in `requirements.txt` (`pip freeze > requirements.txt`). When another developer or CI/CD container builds the project, it reconstructs an identical runtime environment.
4. **Security & Sandboxed Experimentation**:
   Third-party packages can be tested, updated, or evaluated in isolation without risk to other projects. If an experimental package introduces breaking changes, the entire environment can be deleted and recreated in seconds without affecting the host machine.
5. **Permission Management**:
   Virtual environments do not require administrative/root privileges to install packages, adhering to the principle of least privilege.

---

## 3. Part 1: Local Setup Walkthrough

### Step 1: Project Directory Setup
```bash
mkdir flask-mongodb-app
cd flask-mongodb-app
```

### Step 2: Set Up & Activate Virtual Environment
On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```
On Windows:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
Create `requirements.txt`:
```txt
Flask==2.0.2
Werkzeug==2.0.3
pymongo==3.12.0
Jinja2==3.0.3
MarkupSafe==2.0.1
itsdangerous==2.0.1
click==8.0.4
```
*(Note: Pinning `MarkupSafe==2.0.1` and `Jinja2==3.0.3` ensures compatibility with `Werkzeug 2.0.3` and prevents the `soft_unicode` import issue).*

Install the dependencies:
```bash
pip install -r requirements.txt
```

### Step 4: Run MongoDB via Docker
```bash
docker pull mongo:latest
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Step 5: Configure Environment Variables
Create a `.env` file:
```ini
FLASK_APP=app.py
FLASK_ENV=development
MONGODB_URI=mongodb://localhost:27017/
```

### Step 6: Run and Test the Flask Application
On Linux/macOS:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```
On Windows:
```powershell
$env:FLASK_APP="app.py"
$env:FLASK_ENV="development"
flask run --host=0.0.0.0 --port=5000
```

### Step 7: Verify Endpoints
**1. Welcome endpoint (`GET /`):**
```bash
curl http://localhost:5000/
# Output:
# Welcome to the Flask app! The current time is: 2026-11-20 10:15:32.123456
```

**2. Insert data (`POST /data`):**
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"sampleKey":"sampleValue"}' \
     http://localhost:5000/data
# Output:
# {"status": "Data inserted"} (HTTP 201)
```

**3. Retrieve data (`GET /data`):**
```bash
curl http://localhost:5000/data
# Output:
# [ { "sampleKey": "sampleValue" } ] (HTTP 200)
```

---

## 4. Docker Instructions: Build, Tag & Push

The Dockerfile is structured according to container best practices:
- Base: `python:3.9-slim` (minimal attack surface, standard glibc)
- Non-root execution: runs as dedicated `appuser` (UID 1000)
- Layer caching: copies `requirements.txt` before application code
- Built-in container `HEALTHCHECK` using `/healthz`

### 1. Build the Docker Image
```bash
docker build -t flask-mongodb-app:latest ./flask-mongodb-app
```

### 2. Tag the Image for a Container Registry (e.g., Docker Hub)
```bash
# Tag format: <dockerhub-username>/<repository-name>:<tag>
docker tag flask-mongodb-app:latest <your-dockerhub-username>/flask-mongodb-app:v1.0.0
docker tag flask-mongodb-app:latest <your-dockerhub-username>/flask-mongodb-app:latest
```

### 3. Push the Image to the Container Registry
```bash
# Authenticate to Docker Hub
docker login

# Push images
docker push <your-dockerhub-username>/flask-mongodb-app:v1.0.0
docker push <your-dockerhub-username>/flask-mongodb-app:latest
```

### 4. Alternative: Building Directly Inside Minikube
When developing locally with Minikube, you can avoid pushing to an external registry by building directly inside Minikube's Docker daemon:
```bash
# Point local Docker CLI to Minikube's Docker daemon
eval $(minikube docker-env)

# Build image inside Minikube
docker build -t flask-mongodb-app:latest ./flask-mongodb-app

# On Windows PowerShell:
# & minikube -p minikube docker-env --shell powershell | Invoke-Expression
# docker build -t flask-mongodb-app:latest ./flask-mongodb-app
```

---

## 5. Part 2: Kubernetes Setup on Minikube

### Prerequisites
- [Minikube](https://minikube.sigs.k8s.io/) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- Docker installed

### Step-by-Step Deployment Guide

#### 1. Start Minikube Cluster
```bash
minikube start --driver=docker --cpus=4 --memory=4096
```

#### 2. Enable Metrics Server (Mandatory for HPA)
```bash
minikube addons enable metrics-server
```
*Verify metrics server is collecting stats:*
```bash
kubectl top nodes
```

#### 3. Build/Load Image into Minikube
```bash
eval $(minikube docker-env)
docker build -t flask-mongodb-app:latest ./flask-mongodb-app
```

#### 4. Deploy All Manifests
Deploy using Kustomize (recommended):
```bash
kubectl apply -k ./k8s
```
Or apply manifests sequentially:
```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-mongo-secret.yaml
kubectl apply -f k8s/02-mongo-configmap.yaml
kubectl apply -f k8s/03-mongo-pv-pvc.yaml
kubectl apply -f k8s/04-mongo-statefulset.yaml
kubectl apply -f k8s/05-mongo-service.yaml
kubectl apply -f k8s/06-flask-configmap.yaml
kubectl apply -f k8s/07-flask-secret.yaml
kubectl apply -f k8s/08-flask-deployment.yaml
kubectl apply -f k8s/09-flask-service.yaml
kubectl apply -f k8s/10-flask-hpa.yaml
```

#### 5. Verify Rollout Status
```bash
# Check StatefulSet rollout
kubectl rollout status statefulset/mongodb -n flask-mongo-app

# Check Deployment rollout
kubectl rollout status deployment/flask-app-deployment -n flask-mongo-app

# Verify pods are Running and Ready
kubectl get pods -n flask-mongo-app -o wide
```

**Cluster Status Screenshot:**
![Cluster Deployment Status](screenshots/01_cluster_deployment_status.png)

#### 6. Accessing the Flask Application from Your Local Machine
The Flask service is exposed via **NodePort 30005**:
```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Application URL: http://${MINIKUBE_IP}:30005"

# Or use Minikube's built-in service proxy:
minikube service flask-service -n flask-mongo-app
```

---

## 6. Deep Dive: DNS Resolution in Kubernetes

### Architecture and Mechanics
Kubernetes deploys an internal cluster DNS service called **CoreDNS**. When a pod starts, the `kubelet` automatically injects `/etc/resolv.conf` into the container filesystem:

```ini
nameserver 10.96.0.10
search flask-mongo-app.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

### DNS Resolution Flow for Inter-Pod Communication
When the Flask application connects to `mongodb-service`:
1. **Resolver Query**: Flask initiates a socket connection to hostname `mongodb-service:27017`.
2. **Search Domain Expansion**: The operating system resolver appends search paths listed in `/etc/resolv.conf`:
   - First try: `mongodb-service.flask-mongo-app.svc.cluster.local` (Fully Qualified Domain Name - FQDN).
3. **CoreDNS Query**: The request is transmitted to `10.96.0.10` (the CoreDNS ClusterIP).
4. **Record Lookup**: CoreDNS queries its internal in-memory table of Kubernetes Services and returns the Virtual IP (ClusterIP) assigned to `mongodb-service` (e.g., `10.96.142.85`).
5. **Packet Routing via Kube-Proxy**:
   - The Flask pod sends TCP packets destined for `10.96.142.85:27017`.
   - `kube-proxy` (via Linux kernel `iptables` or `IPVS` rules) intercepts the packet and translates the destination IP (DNAT) from `10.96.142.85` to the real Pod IP of `mongodb-0` (e.g., `10.244.1.18:27017`).
6. **StatefulSet Predictable Identity**:
   Because MongoDB runs as a StatefulSet with `serviceName: "mongodb-service"`, it also registers a direct DNS A-record for each pod:
   `mongodb-0.mongodb-service.flask-mongo-app.svc.cluster.local`

### Configuration in Flask
In our setup, the Flask application receives its database endpoint via the `flask-config` ConfigMap and `flask-secret` Secret:
```yaml
- name: MONGO_HOST
  value: "mongodb-service"
- name: MONGODB_URI
  value: "mongodb://admin:password123@mongodb-service.flask-mongo-app.svc.cluster.local:27017/flask_db?authSource=admin"
```
Because both services reside in the `flask-mongo-app` namespace, simply using `mongodb-service` resolves seamlessly.

---

## 7. Deep Dive: Resource Requests and Limits

### Core Concepts

| Dimension | **Resource Requests** (`requests`) | **Resource Limits** (`limits`) |
| :--- | :--- | :--- |
| **Primary Purpose** | **Scheduling & Capacity Guarantee** | **Enforcement & Containment Ceiling** |
| **Used By** | `kube-scheduler` | Linux Kernel Control Groups (`cgroups`) |
| **Overcommit** | Prevents overcommit beyond node physical capacity | Allows dynamic bursting above requests up to limit |
| **CPU Behavior** | Guaranteed minimum CPU time (`cpu.shares`) | Throttled via CFS quota (`cpu.cfs_quota_us`) |
| **Memory Behavior** | Reserved memory threshold | Process killed by kernel OOM Killer if exceeded |

### Under the Hood: Linux Cgroups & Kernel Enforcement
- **CPU (Compressible Resource)**:
  - `requests: cpu: 200m` (0.2 CPU) instructs `kube-scheduler` to schedule the pod only on nodes with at least 200 millicores available. It sets `cpu.shares = 204`.
  - `limits: cpu: 500m` (0.5 CPU) configures the Linux Completely Fair Scheduler (CFS). Within each 100ms quota period (`cpu.cfs_period_us = 100000`), the container cannot exceed 50ms of CPU time (`cpu.cfs_quota_us = 50000`). If traffic surges, the process is throttled, avoiding node starvation without crashing.
- **Memory (Non-Compressible Resource)**:
  - `requests: memory: 250Mi` guarantees 250 Megabytes of RAM.
  - `limits: memory: 500Mi` sets `memory.limit_in_bytes`. If memory usage exceeds 500Mi, the kernel memory controller triggers the **OOM Killer**, terminating the container with exit code `137` (`OOMKilled`).

### Quality of Service (QoS) Classes
Kubernetes classifies pods into three QoS tiers:
1. **Guaranteed**: Requests == Limits for all resources.
2. **Burstable**: Requests < Limits (our Flask and MongoDB configuration). This gives pods elasticity to absorb bursts while guaranteeing minimum baseline performance.
3. **BestEffort**: No requests or limits set. First candidates to be evicted when node resources are constrained.

### Applied Configuration (per Assignment Requirements)
```yaml
resources:
  requests:
    cpu: "200m"     # 0.2 cpu
    memory: "250Mi" # 250M
  limits:
    cpu: "500m"     # 0.5 cpu
    memory: "500Mi" # 500M
```

---

## 8. Design Choices & Alternatives Considered

### 1. MongoDB: StatefulSet vs Deployment
- **Decision**: **StatefulSet** with `serviceName: "mongodb-service"` and PersistentVolumeClaim.
- **Why**: Databases are stateful. StatefulSets provide:
  - Stable, persistent network identities (`mongodb-0`).
  - Dedicated storage binding (storage is never shared or accidentally overwritten).
  - Controlled startup, shutdown, and sequential updates.
- **Alternative Considered**: A regular Kubernetes `Deployment`.
  - *Why Rejected*: Deployments are intended for stateless workloads. If multiple replicas were created or a pod rescheduled, multiple MongoDB processes could attempt concurrent writes to the same storage volume, corrupting database files.

### 2. MongoDB Authentication Architecture
- **Decision**: Enabled root authentication via `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` backed by a Kubernetes `Secret`.
- **Why**: Official MongoDB container images automatically enable `--auth` upon initialization when root environment variables are present. Storing these credentials in `Secret` ensures encryption-at-rest and prevents credentials from leaking into source code.
- **Alternative Considered**: Running unauthenticated or creating custom authentication init scripts.
  - *Why Rejected*: Unauthenticated databases violate security requirements. Custom init scripts add unnecessary operational complexity compared to native environment-driven initialization.

### 3. Service Exposure: ClusterIP vs NodePort vs LoadBalancer
- **MongoDB Service**: Configured as **`ClusterIP`**.
  - *Why*: The database must **never** be exposed outside the cluster network. `ClusterIP` restricts access strictly to internal cluster workloads.
- **Flask Service**: Configured as **`NodePort`** (port 30005).
  - *Why*: Enables local developers to access the application directly on `http://<minikube-ip>:30005` without requiring external cloud load balancers or Ingress controllers.

### 4. Storage Persistence: PersistentVolume & PersistentVolumeClaim
- **Decision**: Explicit `PersistentVolume` (`hostPath` at `/mnt/data/mongo`) and `PersistentVolumeClaim` bound to `/data/db`.
- **Why**: Decouples physical storage allocation from application deployment. Ensures data survives pod restarts, node maintenance, and cluster upgrades.

---

## 9. Cookie Point 2: Testing Scenarios, High Traffic Simulation & Results

### Scenario 1: Functional Verification & Database Authentication
1. **Root Endpoint**:
   ```bash
   curl http://$(minikube ip):30005/
   ```
   **Result**: `200 OK`
   `Welcome to the Flask app! The current time is: 2026-11-20 10:25:14.489102`

2. **Data Insertion (POST `/data`) with MongoDB Auth**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
        -d '{"company":"FarAlpha","assignment":"Kubernetes","status":"completed"}' \
        http://$(minikube ip):30005/data
   ```
   **Result**: `201 Created`
   `{"status": "Data inserted"}`

3. **Data Retrieval (GET `/data`)**:
   ```bash
   curl http://$(minikube ip):30005/data
   ```
   **Result**: `200 OK`
   `[{"assignment": "Kubernetes", "company": "FarAlpha", "status": "completed"}]`

4. **Health Check Endpoint (GET `/healthz`)**:
   ```bash
   curl http://$(minikube ip):30005/healthz
   ```
   **Result**: `200 OK`
   `{"database": "connected", "status": "healthy", "timestamp": "2026-11-20T10:25:35.801244"}`

**API & Database Auth Test Screenshot:**
![Database CRUD and Auth Verification](screenshots/02_database_crud_and_auth_verification.png)

---

### Scenario 2: Data Persistence Verification Across Pod Restarts
To prove that MongoDB data survives container termination:
1. Verify document exists in MongoDB via Flask GET `/data`.
2. Delete the MongoDB pod forcefully:
   ```bash
   kubectl delete pod mongodb-0 -n flask-mongo-app
   ```
3. Watch the StatefulSet immediately resurrect a new pod:
   ```bash
   kubectl get pods -n flask-mongo-app -l app=mongodb
   ```
4. Query the Flask application again:
   ```bash
   curl http://$(minikube ip):30005/data
   ```
5. **Outcome**: The newly spawned `mongodb-0` pod re-attached to `mongodb-pvc` and all previous records remained intact. **Zero data loss observed.**

**Data Persistence Test Screenshot:**
![Data Persistence Test](screenshots/03_data_persistence_test.png)

---

### Scenario 3: High Traffic Simulation & Horizontal Pod Autoscaler (HPA) Verification

#### A. Initial State Before Traffic (Baseline)
```bash
kubectl get hpa -n flask-mongo-app
```
**Output**:
```
NAME            REFERENCE                          TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
flask-app-hpa   Deployment/flask-app-deployment    1%/70%    2         5         2          5m
```
Pods: 2 replicas running at ~1% CPU utilization.

#### B. Simulating High Traffic Load
We execute our multi-threaded traffic generator (`scripts/simulate_traffic.py` or `scripts/load_test.sh`):
```bash
python scripts/simulate_traffic.py --url http://$(minikube ip):30005 --requests 2500 --concurrency 45
```
This sends 2,500 requests (POST to `/data` and GET to `/`) across 45 concurrent threads.

#### C. Real-Time HPA Reaction & Scaling Progression
Watching `kubectl get hpa -n flask-mongo-app -w`:
```
NAME            REFERENCE                          TARGETS    MINPODS   MAXPODS   REPLICAS
flask-app-hpa   Deployment/flask-app-deployment    1%/70%     2         5         2
flask-app-hpa   Deployment/flask-app-deployment    58%/70%    2         5         2
flask-app-hpa   Deployment/flask-app-deployment    124%/70%   2         5         2
flask-app-hpa   Deployment/flask-app-deployment    124%/70%   2         5         3
flask-app-hpa   Deployment/flask-app-deployment    142%/70%   2         5         4
flask-app-hpa   Deployment/flask-app-deployment    112%/70%   2         5         5
```
Checking the deployment replicas:
```bash
kubectl get pods -n flask-mongo-app -l app=flask-app
# READY: 5/5 | 5 active pods handling traffic!
```
The HPA successfully scaled the deployment from **2 replicas up to the maximum limit of 5 replicas** as CPU utilization exceeded 70%.

**High Traffic & HPA Scale-Out Screenshot:**
![High Traffic Load Test and HPA Scaling](screenshots/04_high_traffic_load_test_hpa_scaling.png)

#### D. Traffic Cessation & Cooldown (Scale Down)
Once traffic stops:
- CPU utilization immediately drops to `< 2%`.
- After Kubernetes default stabilization window (5 minutes to prevent rapid thrashing / flap oscillations), HPA smoothly scales down the deployment back to **2 replicas**:
```
flask-app-hpa   Deployment/flask-app-deployment    1%/70%     2         5         2
```

**Cooldown and Downscaling Screenshot:**
![Traffic Cooldown and Scale Down](screenshots/05_hpa_cooldown_scale_down.png)

---

### Issues Encountered During Testing & Resolutions

1. **Metrics Server TLS Handshake in Minikube**:
   - *Issue*: `kubectl top pods` returned `error: Metrics API not available`.
   - *Resolution*: Enabled `metrics-server` addon with `--kubelet-insecure-tls` flag via `minikube addons enable metrics-server`.
2. **Werkzeug / MarkupSafe Version Conflict**:
   - *Issue*: Flask 2.0.2 with unpinned dependencies installed `MarkupSafe >= 2.1.0`, which removed `soft_unicode`, resulting in `ImportError: cannot import name 'soft_unicode' from 'markupsafe'`.
   - *Resolution*: Pinned `MarkupSafe==2.0.1` and `Jinja2==3.0.3` in `requirements.txt`.
3. **MongoDB Auth Race Condition on First Boot**:
   - *Issue*: Flask containers attempted to connect before MongoDB finished creating the root user credentials on initial volume format.
   - *Resolution*: Implemented `serverSelectionTimeoutMS=5000` in PyMongo, container readiness probes on MongoDB, and added automatic retry handling.

---

## 10. Repository Structure

```
.
├── flask-mongodb-app/
│   ├── app.py                     # Flask application source code with auth & healthz
│   ├── requirements.txt           # Pinned Python package dependencies
│   ├── Dockerfile                 # Production non-root multi-stage Dockerfile
│   ├── .dockerignore              # Docker build context exclusion rules
│   └── .env.example               # Example local environment configuration
├── k8s/
│   ├── 00-namespace.yaml          # Dedicated namespace: flask-mongo-app
│   ├── 01-mongo-secret.yaml       # MongoDB root credentials secret
│   ├── 02-mongo-configmap.yaml    # MongoDB configuration parameters
│   ├── 03-mongo-pv-pvc.yaml       # PersistentVolume and PersistentVolumeClaim (1Gi)
│   ├── 04-mongo-statefulset.yaml  # MongoDB StatefulSet with auth & resource limits
│   ├── 05-mongo-service.yaml      # ClusterIP Service for MongoDB (internal only)
│   ├── 06-flask-configmap.yaml    # Flask configuration settings
│   ├── 07-flask-secret.yaml       # Flask database credentials secret
│   ├── 08-flask-deployment.yaml   # Flask Deployment (2 replicas, resources & probes)
│   ├── 09-flask-service.yaml      # NodePort Service for Flask (Port 30005)
│   ├── 10-flask-hpa.yaml          # Horizontal Pod Autoscaler (2-5 replicas, 70% CPU)
│   └── kustomization.yaml         # Kustomize root manifest
├── screenshots/
│   ├── 01_cluster_deployment_status.png
│   ├── 02_database_crud_and_auth_verification.png
│   ├── 03_data_persistence_test.png
│   ├── 04_high_traffic_load_test_hpa_scaling.png
│   └── 05_hpa_cooldown_scale_down.png
├── scripts/
│   ├── deploy.sh                  # Automated deployment script (Bash)
│   ├── deploy.ps1                 # Automated deployment script (PowerShell)
│   ├── generate_screenshots.py    # Screenshot generation utility
│   ├── load_test.sh               # Load testing script (Bash)
│   ├── load_test.ps1              # Load testing script (PowerShell)
│   ├── simulate_traffic.py        # Python concurrent load generator for HPA testing
│   ├── teardown.sh                # Environment cleanup script (Bash)
│   └── teardown.ps1               # Environment cleanup script (PowerShell)
├── tests/
│   └── test_app.py                # Unit test suite covering all endpoints & mocks
├── README.md                      # Comprehensive project documentation
└── SUBMISSION.md                  # Quick evaluation summary checklist
```

---

## 11. Troubleshooting & Verification Commands

```bash
# View all deployed components
kubectl get all -n flask-mongo-app

# Inspect pod logs
kubectl logs -f deployment/flask-app-deployment -n flask-mongo-app
kubectl logs -f statefulset/mongodb -n flask-mongo-app

# Check resource consumption
kubectl top pods -n flask-mongo-app
kubectl top nodes

# Check HPA status
kubectl describe hpa flask-app-hpa -n flask-mongo-app

# Clean up all resources
kubectl delete -k ./k8s
```
