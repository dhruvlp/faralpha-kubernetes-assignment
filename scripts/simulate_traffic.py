#!/usr/bin/env python3
"""
Traffic simulation and load testing script for Flask-MongoDB Kubernetes App.
Simulates high concurrent traffic (GET / and POST /data) to trigger Horizontal Pod Autoscaler (HPA).
"""

import sys
import time
import json
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

def send_request(base_url, endpoint, method="GET", payload=None):
    url = f"{base_url.rstrip('/')}{endpoint}"
    data = json.dumps(payload).encode('utf-8') if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            duration = time.time() - start_time
            return {"status": status, "duration": duration, "error": None}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "duration": time.time() - start_time, "error": str(e)}
    except Exception as e:
        return {"status": None, "duration": time.time() - start_time, "error": str(e)}

def run_load_test(base_url, total_requests=1000, concurrency=20, post_ratio=0.5):
    print(f"============================================================")
    print(f"Starting Load Test on {base_url}")
    print(f"Total Requests: {total_requests} | Concurrency: {concurrency} | POST Ratio: {post_ratio * 100}%")
    print(f"============================================================")
    
    start_total = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(total_requests):
            if i % int(1 / post_ratio) == 0 if post_ratio > 0 else False:
                payload = {"testId": i, "timestamp": time.time(), "sampleKey": f"val_{i}"}
                futures.append(executor.submit(send_request, base_url, "/data", "POST", payload))
            else:
                endpoint = "/data" if i % 2 == 0 else "/"
                futures.append(executor.submit(send_request, base_url, endpoint, "GET", None))
        
        for future in as_completed(futures):
            results.append(future.result())
            completed = len(results)
            if completed % 100 == 0 or completed == total_requests:
                print(f"Progress: {completed}/{total_requests} requests completed...")

    total_time = time.time() - start_total
    success_count = sum(1 for r in results if r["status"] in [200, 201])
    error_count = len(results) - success_count
    latencies = [r["duration"] for r in results if r["duration"] is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    print("\n" + "=" * 60)
    print("LOAD TEST SUMMARY")
    print("=" * 60)
    print(f"Total Time Taken     : {total_time:.2f} seconds")
    print(f"Requests per Second  : {len(results) / total_time:.2f} req/s")
    print(f"Successful Requests  : {success_count} ({success_count / len(results) * 100:.1f}%)")
    print(f"Failed Requests      : {error_count}")
    print(f"Average Latency      : {avg_latency * 1000:.2f} ms")
    if latencies:
        print(f"Min Latency          : {min(latencies) * 1000:.2f} ms")
        print(f"Max Latency          : {max(latencies) * 1000:.2f} ms")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate traffic for Kubernetes HPA testing")
    parser.add_argument("--url", default="http://localhost:30005", help="Target URL (default: http://localhost:30005)")
    parser.add_argument("--requests", type=int, default=1500, help="Total number of requests")
    parser.add_argument("--concurrency", type=int, default=30, help="Number of concurrent workers")
    parser.add_argument("--post-ratio", type=float, default=0.4, help="Ratio of POST to GET requests")
    
    args = parser.parse_args()
    run_load_test(args.url, args.requests, args.concurrency, args.post_ratio)
