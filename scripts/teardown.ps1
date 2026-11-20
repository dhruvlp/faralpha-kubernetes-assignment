# Teardown Script for Windows
Write-Host "Deleting all resources in namespace flask-mongo-app..." -ForegroundColor Red
kubectl delete -k ./k8s --ignore-not-found=true
kubectl delete namespace flask-mongo-app --ignore-not-found=true
kubectl delete pv mongodb-pv --ignore-not-found=true
Write-Host "Teardown complete." -ForegroundColor Green
