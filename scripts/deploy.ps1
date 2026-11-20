# Automated Deployment Script for Minikube on Windows
Write-Host "=== [1/5] Checking Kubernetes Cluster Status ===" -ForegroundColor Cyan
kubectl cluster-info

Write-Host "=== [2/5] Enabling Minikube metrics-server (required for HPA) ===" -ForegroundColor Cyan
minikube addons enable metrics-server

Write-Host "=== [3/5] Pointing Docker CLI to Minikube's Docker Daemon ===" -ForegroundColor Cyan
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

Write-Host "Building Docker image inside Minikube..." -ForegroundColor Cyan
docker build -t flask-mongodb-app:latest ./flask-mongodb-app

Write-Host "=== [4/5] Applying Kubernetes Manifests via Kustomize ===" -ForegroundColor Cyan
kubectl apply -k ./k8s

Write-Host "=== [5/5] Waiting for Pods to become Ready ===" -ForegroundColor Cyan
kubectl rollout status statefulset/mongodb -n flask-mongo-app --timeout=120s
kubectl rollout status deployment/flask-app-deployment -n flask-mongo-app --timeout=120s

Write-Host "=== All Resources Successfully Deployed ===" -ForegroundColor Green
kubectl get all,hpa,pv,pvc -n flask-mongo-app

Write-Host "`nTo open the Flask application in your browser run:" -ForegroundColor Yellow
Write-Host "minikube service flask-service -n flask-mongo-app" -ForegroundColor Yellow
