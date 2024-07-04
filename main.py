import logging
import time
from fastapi import FastAPI, HTTPException, Request
from kubernetes.client import ApiException
from prometheus_client import Counter, Histogram
from model import AppConfig
from kub import KubernetesClient

app = FastAPI()

# Define Prometheus metrics
REQUEST_COUNT = Counter("app_request_count", "Total number of requests")
REQUEST_ERROR_COUNT = Counter("app_request_error_count", "Total number of failed requests")
REQUEST_LATENCY = Histogram("app_request_latency_seconds", "Request latency in seconds",
                            buckets=[0.1, 0.5, 1, 2, 5, 10, float("inf")])
DB_ERROR_COUNT = Counter("app_db_error_count", "Total number of database errors")
DB_LATENCY = Histogram("app_db_latency_seconds", "Database response latency in seconds",
                       buckets=[0.1, 0.5, 1, 2, 5, 10, float("inf")])


@app.middleware("http")
async def add_metrics(request: Request, call_next):
    # Count the number of requests
    REQUEST_COUNT.inc()

    # Measure the latency of each request
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    REQUEST_LATENCY.observe(latency)

    # Log errors if request fails
    if response.status_code >= 400:
        REQUEST_ERROR_COUNT.inc()

    return response


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/api/create")
async def create(conf: AppConfig):
    try:
        if conf.Service is not None:
            KubernetesClient.create_service(conf)
        if conf.Secret is not None:
            KubernetesClient.create_secret(conf)
        if conf.Ingress is not None:
            KubernetesClient.create_ingress(conf)
        KubernetesClient.create_deployment(conf)
        KubernetesClient.create_hpa(conf)
        return {"Message": f"Deployment {conf.AppName} successfully created!"}
    except ApiException:
        REQUEST_ERROR_COUNT.inc()
        return {"message": "Could not create deployment"}


@app.get("/api/{app_name}")
async def get(app_name: str):
    try:
        deployment_status, pod_statuses = KubernetesClient.get_deployment_status(app_name.lower())

        replicas = deployment_status.spec.replicas
        ready_replicas = deployment_status.status.ready_replicas

        return {
            "DeploymentName": app_name.lower(),
            "Replicas": replicas,
            "ReadyReplicas": ready_replicas,
            "PodStatuses": pod_statuses
        }
    except ApiException:
        REQUEST_ERROR_COUNT.inc()
        raise HTTPException(status_code=404, detail=f"Deployment {app_name} not found")
    except Exception as e:
        REQUEST_ERROR_COUNT.inc()
        logging.info(e)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api")
async def get_all_deployments():
    try:
        all_deployments_status = KubernetesClient.get_all_deployments_status()
        return all_deployments_status
    except ApiException:
        REQUEST_ERROR_COUNT.inc()
        raise HTTPException(status_code=500, detail="Could not retrieve deployments status")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
