from flask import Flask, request, jsonify
import subprocess
import uuid

app = Flask(__name__)


@app.route('/deploy', methods=['POST'])
def deploy_postgres():
    data = request.json
    app_name = data.get('AppName')
    resources = data.get('Resources')
    external = data.get('External')

    username = f"{app_name}-user"
    password = str(uuid.uuid4())

    create_secret(app_name, username, password)
    create_configmap(app_name)
    create_statefulset(app_name, resources, external)

    return jsonify({"message": "Deployment initiated", "username": username, "password": password})


def create_secret(app_name, username, password):
    secret_manifest = f"""
apiVersion: v1
kind: Secret
metadata:
  name: {app_name}-secret
type: Opaque
data:
  username: {username.encode('utf-8').hex()}
  password: {password.encode('utf-8').hex()}
"""
    subprocess.run(["kubectl", "apply", "-f", "-"], input=secret_manifest.encode('utf-8'))


def create_configmap(app_name):
    configmap_manifest = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-config
data:
  postgresql.conf: |
    shared_buffers = 128MB
    max_connections = 100
"""
    subprocess.run(["kubectl", "apply", "-f", "-"], input=configmap_manifest.encode('utf-8'))


def create_statefulset(app_name, resources, external):
    statefulset_manifest = f"""
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {app_name}
spec:
  serviceName: "{app_name}-service"
  replicas: 1
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: postgres:13.3
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: {app_name}-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {app_name}-secret
              key: password
        - name: POSTGRES_DB
          value: mydatabase
        resources:
          requests:
            memory: "{resources['RAM']}"
            cpu: "{resources['CPU']}"
        volumeMounts:
        - name: pgdata
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: pgdata
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 8Gi
"""
    service_manifest = f"""
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-service
spec:
  type: {"LoadBalancer" if external else "ClusterIP"}
  ports:
  - port: 5432
  selector:
    app: {app_name}
"""
    subprocess.run(["kubectl", "apply", "-f", "-"], input=statefulset_manifest.encode('utf-8'))
    subprocess.run(["kubectl", "apply", "-f", "-"], input=service_manifest.encode('utf-8'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
