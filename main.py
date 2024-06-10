import logging

from fastapi import FastAPI, HTTPException
from kubernetes.client import ApiException

from model import AppConfig
from kub import KubernetesClient

app = FastAPI()


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

        return {"Message": f"Deployment {conf.AppName} successfully created!"}
    except ApiException:
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
        raise HTTPException(status_code=404, detail=f"Deployment {app_name} not found")
    except Exception as e:
        logging.info(e)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api")
async def get_all_deployments():
    try:
        all_deployments_status = KubernetesClient.get_all_deployments_status()
        return all_deployments_status
    except ApiException:
        raise HTTPException(status_code=500, detail="Could not retrieve deployments status")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
