#!/usr/bin/env bash
set -e

echo "=== [1/5] Checking Kubernetes cluster status ==="
kubectl cluster-info

echo "=== [2/5] Enabling Minikube metrics-server (required for HPA) ==="
minikube addons enable metrics-server || true

echo "=== [3/5] Building Docker image directly inside Minikube ==="
eval $(minikube docker-env)
docker build -t flask-mongodb-app:latest ./flask-mongodb-app

echo "=== [4/5] Deploying Kubernetes Resources ==="
kubectl apply -k ./k8s

echo "=== [5/5] Waiting for Deployments and StatefulSets to be Ready ==="
kubectl rollout status statefulset/mongodb -n flask-mongo-app --timeout=120s
kubectl rollout status deployment/flask-app-deployment -n flask-mongo-app --timeout=120s

echo "=== Deployment Complete ==="
kubectl get all,hpa,pv,pvc -n flask-mongo-app

echo ""
echo "To access the Flask application:"
echo "minikube service flask-service -n flask-mongo-app"
