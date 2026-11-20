#!/usr/bin/env bash
echo "Deleting all resources in namespace flask-mongo-app..."
kubectl delete -k ./k8s --ignore-not-found=true
kubectl delete namespace flask-mongo-app --ignore-not-found=true
kubectl delete pv mongodb-pv --ignore-not-found=true
echo "Teardown complete."
