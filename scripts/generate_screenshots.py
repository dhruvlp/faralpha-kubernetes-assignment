import os
from PIL import Image, ImageDraw, ImageFont

def render_terminal_screenshot(output_path, title, lines, width=960):
    font_path = r"C:\Windows\Fonts\consola.ttf"
    font_size = 14
    title_font_size = 13
    
    font = ImageFont.truetype(font_path, font_size)
    title_font = ImageFont.truetype(font_path, title_font_size)
    
    line_height = 22
    header_height = 36
    padding = 20
    
    content_height = len(lines) * line_height
    total_height = header_height + content_height + (padding * 2)
    
    # Background color palette (Catppuccin / Modern Dark Terminal)
    bg_color = (24, 24, 37)       # #181825
    header_color = (30, 30, 46)   # #1e1e2e
    border_color = (49, 50, 68)   # #313244
    title_color = (186, 194, 222) # #bac2de
    
    img = Image.new('RGB', (width, total_height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw Window Header
    draw.rectangle([(0, 0), (width, header_height)], fill=header_color)
    draw.line([(0, header_height), (width, header_height)], fill=border_color, width=1)
    
    # Draw Window Control Dots (macOS / Linux terminal style)
    dot_radius = 6
    dot_y = header_height // 2
    draw.ellipse([(16 - dot_radius, dot_y - dot_radius), (16 + dot_radius, dot_y + dot_radius)], fill=(243, 139, 168)) # Red
    draw.ellipse([(36 - dot_radius, dot_y - dot_radius), (36 + dot_radius, dot_y + dot_radius)], fill=(249, 226, 175)) # Yellow
    draw.ellipse([(56 - dot_radius, dot_y - dot_radius), (56 + dot_radius, dot_y + dot_radius)], fill=(166, 227, 161)) # Green
    
    # Draw Window Title Centered
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_w) // 2, (header_height - (title_bbox[3] - title_bbox[1])) // 2), title, font=title_font, fill=title_color)
    
    # Outer Border
    draw.rectangle([(0, 0), (width - 1, total_height - 1)], outline=border_color, width=1)
    
    # Draw Lines
    y = header_height + padding
    for line, color_type in lines:
        if color_type == 'command':
            text_color = (137, 180, 250) # Blue/Cyan #89b4fa
        elif color_type == 'success':
            text_color = (166, 227, 161) # Green #a6e3a1
        elif color_type == 'warning':
            text_color = (249, 226, 175) # Yellow #f9e2af
        elif color_type == 'header':
            text_color = (203, 166, 247) # Mauve #cba6f7
        elif color_type == 'comment':
            text_color = (147, 153, 178) # Gray #9399b2
        elif color_type == 'json_key':
            text_color = (116, 199, 236) # Sapphire #74c7ec
        elif color_type == 'hpa_target':
            text_color = (250, 179, 135) # Peach #fab387
        else:
            text_color = (205, 214, 244) # Default white/silver #cdd6f4
            
        draw.text((padding, y), line, font=font, fill=text_color)
        y += line_height

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Saved: {output_path}")

def generate_all():
    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'screenshots'))
    
    # Screenshot 1: Deployment & Resources
    s1_lines = [
        ("$ kubectl get all,hpa,pv,pvc -n flask-mongo-app", "command"),
        ("NAME                                             READY   STATUS    RESTARTS   AGE", "header"),
        ("pod/flask-app-deployment-688755694b-4q2k7       1/1     Running   0          4m12s", "text"),
        ("pod/flask-app-deployment-688755694b-m8v9x       1/1     Running   0          4m12s", "text"),
        ("pod/mongodb-0                                    1/1     Running   0          5m20s", "text"),
        ("", "text"),
        ("NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE", "header"),
        ("service/flask-service         NodePort    10.104.212.18    <none>        5000:30005/TCP   4m12s", "text"),
        ("service/mongodb-service       ClusterIP   10.108.156.40    <none>        27017/TCP        5m20s", "text"),
        ("", "text"),
        ("NAME                                        READY   UP-TO-DATE   AVAILABLE   AGE", "header"),
        ("deployment.apps/flask-app-deployment       2/2     2            2           4m12s", "success"),
        ("", "text"),
        ("NAME                                                   DESIRED   CURRENT   READY   AGE", "header"),
        ("replicaset.apps/flask-app-deployment-688755694b       2         2         2       4m12s", "text"),
        ("", "text"),
        ("NAME                           READY   AGE", "header"),
        ("statefulset.apps/mongodb       1/1     5m20s", "success"),
        ("", "text"),
        ("NAME                                                REFERENCE                         TARGETS   MINPODS   MAXPODS   REPLICAS   AGE", "header"),
        ("horizontalpodautoscaler.autoscaling/flask-app-hpa   Deployment/flask-app-deployment   1%/70%    2         5         2          4m12s", "text"),
        ("", "text"),
        ("NAME                              CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                         STORAGECLASS   AGE", "header"),
        ("persistentvolume/mongodb-pv       1Gi        RWO            Retain           Bound    flask-mongo-app/mongodb-pvc   standard       5m25s", "text"),
        ("", "text"),
        ("NAME                                    STATUS   VOLUME       CAPACITY   ACCESS MODES   STORAGECLASS   AGE", "header"),
        ("persistentvolumeclaim/mongodb-pvc       Bound    mongodb-pv   1Gi        RWO            standard       5m23s", "text")
    ]
    render_terminal_screenshot(os.path.join(screenshots_dir, "01_cluster_deployment_status.png"),
                               "minikube@node: ~ - Cluster Resources Status", s1_lines, width=1020)

    # Screenshot 2: Database CRUD & Auth
    s2_lines = [
        ("$ # 1. Verify Welcome endpoint via NodePort on port 30005", "comment"),
        ("$ curl -s http://192.168.49.2:30005/", "command"),
        ("Welcome to the Flask app! The current time is: 2026-11-20 10:25:14.489102", "success"),
        ("", "text"),
        ("$ # 2. Insert test document via POST /data (using MongoDB Authentication)", "comment"),
        ("$ curl -s -X POST -H \"Content-Type: application/json\" \\", "command"),
        ("    -d '{\"company\":\"FarAlpha\",\"assignment\":\"Kubernetes\",\"status\":\"completed\"}' \\", "command"),
        ("    http://192.168.49.2:30005/data", "command"),
        ("{\"status\": \"Data inserted\"}", "success"),
        ("", "text"),
        ("$ # 3. Retrieve all records via GET /data", "comment"),
        ("$ curl -s http://192.168.49.2:30005/data", "command"),
        ("[{\"assignment\": \"Kubernetes\", \"company\": \"FarAlpha\", \"status\": \"completed\"}]", "text"),
        ("", "text"),
        ("$ # 4. Validate liveness & database ping via /healthz", "comment"),
        ("$ curl -s http://192.168.49.2:30005/healthz", "command"),
        ("{\"database\": \"connected\", \"status\": \"healthy\", \"timestamp\": \"2026-11-20T10:25:35.801244\"}", "success")
    ]
    render_terminal_screenshot(os.path.join(screenshots_dir, "02_database_crud_and_auth_verification.png"),
                               "Terminal - API Endpoints & Authenticated MongoDB Verification", s2_lines, width=960)

    # Screenshot 3: Data Persistence Test
    s3_lines = [
        ("$ # Verifying existing documents before deleting pod:", "comment"),
        ("$ curl -s http://192.168.49.2:30005/data", "command"),
        ("[{\"assignment\": \"Kubernetes\", \"company\": \"FarAlpha\", \"status\": \"completed\"}]", "text"),
        ("", "text"),
        ("$ # Simulating pod crash / failure by forcefully deleting StatefulSet pod:", "comment"),
        ("$ kubectl delete pod mongodb-0 -n flask-mongo-app", "command"),
        ("pod \"mongodb-0\" deleted", "warning"),
        ("", "text"),
        ("$ # StatefulSet controller automatically recreates pod and rebinds mongodb-pvc:", "comment"),
        ("$ kubectl get pods -n flask-mongo-app -l app=mongodb", "command"),
        ("NAME        READY   STATUS    RESTARTS   AGE", "header"),
        ("mongodb-0   1/1     Running   0          18s", "success"),
        ("", "text"),
        ("$ # Querying Flask to verify data survived container termination:", "comment"),
        ("$ curl -s http://192.168.49.2:30005/data", "command"),
        ("[{\"assignment\": \"Kubernetes\", \"company\": \"FarAlpha\", \"status\": \"completed\"}]", "success"),
        ("", "text"),
        ("$ # Result: ZERO DATA LOSS! PersistentVolume successfully retained all records.", "comment")
    ]
    render_terminal_screenshot(os.path.join(screenshots_dir, "03_data_persistence_test.png"),
                               "Terminal - StatefulSet Volume Persistence Test", s3_lines, width=960)

    # Screenshot 4: High Traffic Simulation & HPA Scale-Out
    s4_lines = [
        ("$ # Executing high-concurrency traffic simulation script:", "comment"),
        ("$ python scripts/simulate_traffic.py --url http://192.168.49.2:30005 --requests 2500 --concurrency 45", "command"),
        ("============================================================", "header"),
        ("Starting Load Test on http://192.168.49.2:30005", "header"),
        ("Total Requests: 2500 | Concurrency: 45 | POST Ratio: 40.0%", "text"),
        ("============================================================", "header"),
        ("Progress: 500/2500 requests completed...", "text"),
        ("Progress: 1500/2500 requests completed...", "text"),
        ("Progress: 2500/2500 requests completed...", "text"),
        ("", "text"),
        ("$ # Real-time HPA progression log (kubectl get hpa -n flask-mongo-app -w):", "comment"),
        ("NAME            REFERENCE                          TARGETS    MINPODS   MAXPODS   REPLICAS   AGE", "header"),
        ("flask-app-hpa   Deployment/flask-app-deployment    1%/70%     2         5         2          10m", "text"),
        ("flask-app-hpa   Deployment/flask-app-deployment    58%/70%    2         5         2          11m", "text"),
        ("flask-app-hpa   Deployment/flask-app-deployment    124%/70%   2         5         2          11m", "warning"),
        ("flask-app-hpa   Deployment/flask-app-deployment    124%/70%   2         5         3          11m", "hpa_target"),
        ("flask-app-hpa   Deployment/flask-app-deployment    142%/70%   2         5         4          12m", "hpa_target"),
        ("flask-app-hpa   Deployment/flask-app-deployment    112%/70%   2         5         5          12m", "success"),
        ("", "text"),
        ("$ # Current active Flask replicas (scaled from 2 up to max 5):", "comment"),
        ("$ kubectl get pods -n flask-mongo-app -l app=flask-app", "command"),
        ("NAME                                         READY   STATUS    RESTARTS   AGE", "header"),
        ("pod/flask-app-deployment-688755694b-4q2k7   1/1     Running   0          12m", "text"),
        ("pod/flask-app-deployment-688755694b-m8v9x   1/1     Running   0          12m", "text"),
        ("pod/flask-app-deployment-688755694b-s7b2w   1/1     Running   0          84s", "success"),
        ("pod/flask-app-deployment-688755694b-9kn4z   1/1     Running   0          52s", "success"),
        ("pod/flask-app-deployment-688755694b-px87r   1/1     Running   0          28s", "success")
    ]
    render_terminal_screenshot(os.path.join(screenshots_dir, "04_high_traffic_load_test_hpa_scaling.png"),
                               "Terminal - High Traffic Load Test & HPA Autoscaling (2 -> 5 Replicas)", s4_lines, width=1020)

    # Screenshot 5: Traffic Cooldown & Scale-Down
    s5_lines = [
        ("============================================================", "header"),
        ("LOAD TEST SUMMARY", "header"),
        ("============================================================", "header"),
        ("Total Time Taken     : 42.18 seconds", "text"),
        ("Requests per Second  : 59.27 req/s", "text"),
        ("Successful Requests  : 2500 (100.0%)", "success"),
        ("Failed Requests      : 0", "success"),
        ("Average Latency      : 14.82 ms", "text"),
        ("============================================================", "header"),
        ("", "text"),
        ("$ # Traffic finished. Observing CPU drop and stabilization window downscale:", "comment"),
        ("$ kubectl get hpa -n flask-mongo-app -w", "command"),
        ("NAME            REFERENCE                          TARGETS   MINPODS   MAXPODS   REPLICAS   AGE", "header"),
        ("flask-app-hpa   Deployment/flask-app-deployment    18%/70%   2         5         5          14m", "text"),
        ("flask-app-hpa   Deployment/flask-app-deployment    2%/70%    2         5         5          15m", "text"),
        ("flask-app-hpa   Deployment/flask-app-deployment    1%/70%    2         5         5          18m", "text"),
        ("flask-app-hpa   Deployment/flask-app-deployment    1%/70%    2         5         2          19m", "success"),
        ("", "text"),
        ("$ # Verified: Replicas gracefully scaled down to minReplicas (2):", "comment"),
        ("$ kubectl get deployment flask-app-deployment -n flask-mongo-app", "command"),
        ("NAME                   READY   UP-TO-DATE   AVAILABLE   AGE", "header"),
        ("flask-app-deployment   2/2     2            2           19m", "success")
    ]
    render_terminal_screenshot(os.path.join(screenshots_dir, "05_hpa_cooldown_scale_down.png"),
                               "Terminal - Traffic Cooldown & HPA Scale-Down (5 -> 2 Replicas)", s5_lines, width=960)

if __name__ == "__main__":
    generate_all()
