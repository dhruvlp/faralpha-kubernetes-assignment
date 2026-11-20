#!/usr/bin/env bash
# High traffic simulation script using curl in bash

TARGET_URL="${1:-http://localhost:30005}"
CONCURRENCY="${2:-10}"
REQUESTS_PER_WORKER="${3:-150}"

echo "============================================================"
echo "Simulating High Traffic on: $TARGET_URL"
echo "Concurrency: $CONCURRENCY workers | Requests/worker: $REQUESTS_PER_WORKER"
echo "============================================================"

run_worker() {
  local worker_id=$1
  for ((i=1; i<=REQUESTS_PER_WORKER; i++)); do
    # Alternate between GET / and POST /data
    if (( i % 2 == 0 )); then
      curl -s -X POST -H "Content-Type: application/json" \
           -d "{\"worker\": $worker_id, \"seq\": $i, \"timestamp\": $(date +%s)}" \
           "$TARGET_URL/data" > /dev/null
    else
      curl -s "$TARGET_URL/" > /dev/null
    fi
  done
}

export -f run_worker
export TARGET_URL
export REQUESTS_PER_WORKER

START_TIME=$(date +%s)
for ((w=1; w<=CONCURRENCY; w++)); do
  run_worker "$w" &
done

wait
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo "Load generation completed in $TOTAL_TIME seconds."
echo "Check HPA status with: kubectl get hpa -n flask-mongo-app --watch"
