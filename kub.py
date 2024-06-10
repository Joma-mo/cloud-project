import logging
from typing import List, Dict

from kubernetes import client, config
from kubernetes.client import ApiException
from model import AppConfig


class KubernetesClient:
    @staticmethod
    def create_deployment(conf: AppConfig):
        config.load_kube_config()
        api_instance = client.AppsV1Api()
        try:
            # Check if deployment already exists
            api_instance.read_namespaced_deployment(name=conf.AppName.lower(), namespace="default")
            logging.info(f"Deployment {conf.AppName} already exists.")
        except ApiException as e:
            if e.status == 404:
                # Deployment does not exist, create it
                container = client.V1Container(
                    name=conf.AppName.lower(),
                    image=f'{conf.ImageAddress}:{conf.ImageTag}',
                    ports=[client.V1ContainerPort(container_port=conf.ServicePort)],
                    resources=client.V1ResourceRequirements(
                        requests={
                            "cpu": conf.Resources.CPU,
                            "memory": conf.Resources.RAM
                        }
                    ),
                    env=[client.V1EnvVar(name=env.Key, value=env.Value) for env in conf.Envs if not env.IsSecret] + [
                        client.V1EnvVar(
                            name=env.Key,
                            value_from=client.V1EnvVarSource(
                                secret_key_ref=client.V1SecretKeySelector(
                                    name=conf.AppName.lower(),
                                    key=env.Key
                                )
                            )
                        ) for env in conf.Envs if env.IsSecret
                    ]
                )

                template = client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": conf.AppName.lower()}),
                    spec=client.V1PodSpec(containers=[container])
                )

                spec = client.V1DeploymentSpec(
                    replicas=conf.Replicas,
                    template=template,
                    selector={'matchLabels': {"app": conf.AppName.lower()}}
                )

                deployment = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=conf.AppName.lower()),
                    spec=spec
                )

                try:
                    api_instance.create_namespaced_deployment(
                        namespace="default",
                        body=deployment
                    )
                    logging.info(f"Deployment {conf.AppName} created successfully.")
                except ApiException as e:
                    logging.error(f"Exception when creating deployment: {e}")
                    raise e

    @staticmethod
    def create_service(conf: AppConfig):
        config.load_kube_config()
        api_instance = client.CoreV1Api()
        try:
            # Check if service already exists
            api_instance.read_namespaced_service(name=conf.AppName.lower(), namespace="default")
            logging.info(f"Service {conf.AppName} already exists.")
        except ApiException as e:
            if e.status == 404:
                # Service does not exist, create it
                service = client.V1Service(
                    api_version="v1",
                    kind="Service",
                    metadata=client.V1ObjectMeta(name=conf.AppName.lower()),
                    spec=client.V1ServiceSpec(
                        selector={"app": conf.AppName.lower()},
                        ports=[client.V1ServicePort(
                            port=conf.ServicePort,
                            target_port=conf.ServicePort
                        )],
                        type="ClusterIP"
                    )
                )

                try:
                    api_instance.create_namespaced_service(
                        namespace="default",
                        body=service
                    )
                    logging.info(f"Service {conf.AppName} created successfully.")
                except ApiException as e:
                    logging.error(f"Exception when creating service: {e}")
                    raise e

    @staticmethod
    def create_secret(conf: AppConfig):
        config.load_kube_config()
        api_instance = client.CoreV1Api()
        try:
            api_instance.read_namespaced_secret(name=conf.AppName.lower(), namespace="default")
            logging.info(f"Secret {conf.AppName} already exists.")
        except ApiException as e:
            if e.status == 404:
                secret = client.V1Secret(
                    api_version="v1",
                    kind="Secret",
                    metadata=client.V1ObjectMeta(name=conf.AppName.lower()),
                    data={env.Key: env.Value for env in conf.Envs if env.IsSecret}
                )

                try:
                    api_instance.create_namespaced_secret(
                        namespace="default",
                        body=secret
                    )
                    logging.info(f"Secret {conf.AppName} created successfully.")
                except ApiException as e:
                    logging.error(f"Exception when creating secret: {e}")
                    raise e

    @staticmethod
    def create_ingress(conf: AppConfig):
        config.load_kube_config()
        api_instance = client.NetworkingV1Api()
        try:
            # Check if ingress already exists
            api_instance.read_namespaced_ingress(name=conf.AppName.lower(), namespace="default")
            logging.info(f"Ingress {conf.AppName} already exists.")
        except ApiException as e:
            if e.status == 404:
                # Ingress does not exist, create it
                ingress = client.V1Ingress(
                    api_version="networking.k8s.io/v1",
                    kind="Ingress",
                    metadata=client.V1ObjectMeta(name=conf.AppName.lower()),
                    spec=client.V1IngressSpec(
                        rules=[
                            client.V1IngressRule(
                                host=conf.DomainAddress,
                                http=client.V1HTTPIngressRuleValue(
                                    paths=[
                                        client.V1HTTPIngressPath(
                                            path="/",
                                            path_type="Prefix",
                                            backend=client.V1IngressBackend(
                                                service=client.V1IngressServiceBackend(
                                                    name=conf.AppName.lower(),
                                                    port=client.V1ServiceBackendPort(number=conf.ServicePort)
                                                )
                                            )
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )

                try:
                    api_instance.create_namespaced_ingress(
                        namespace="default",
                        body=ingress
                    )
                    logging.info(f"Ingress {conf.AppName} created successfully.")
                except ApiException as e:
                    logging.error(f"Exception when creating ingress: {e}")
                    raise e

    @staticmethod
    def get_deployment_status(deployment_name: str):
        # Load Kubernetes configuration
        config.load_kube_config()

        # Create an instance of the Kubernetes AppsV1Api
        api_instance = client.AppsV1Api()

        try:
            # Retrieve the status of the deployment
            deployment_status = api_instance.read_namespaced_deployment_status(name=deployment_name,
                                                                               namespace="default")

            # Retrieve pod statuses associated with the deployment
            pod_statuses = KubernetesClient.get_pod_statuses(deployment_name)

            return deployment_status, pod_statuses
        except ApiException as e:
            # Handle ApiException appropriately
            print(f"Exception when getting deployment status: {e}")
            raise e

    @staticmethod
    def get_pod_statuses(deployment_name: str):
        # Create an instance of the Kubernetes CoreV1Api
        core_api_instance = client.CoreV1Api()

        try:
            # Retrieve list of pods associated with the deployment
            pods = core_api_instance.list_namespaced_pod(namespace="default", label_selector=f"app={deployment_name}")

            # Extract pod statuses
            pod_statuses = []
            for pod in pods.items:
                pod_statuses.append({
                    "Name": pod.metadata.name,
                    "Phase": pod.status.phase,
                    "HostIP": pod.status.host_ip,
                    "PodIP": pod.status.pod_ip,
                    "StartTime": pod.status.start_time.strftime("%Y-%m-%d %H:%M:%S")
                })

            return pod_statuses
        except ApiException as e:
            # Handle ApiException appropriately
            print(f"Exception when getting pod statuses: {e}")
            raise e

    @staticmethod
    def get_all_deployments_status():
        config.load_kube_config()

        apps_v1_api = client.AppsV1Api()
        core_v1_api = client.CoreV1Api()

        try:
            deployments = apps_v1_api.list_namespaced_deployment(namespace="default")
            all_deployments_status = []

            for deployment in deployments.items:
                deployment_name = deployment.metadata.name
                replicas = deployment.spec.replicas
                ready_replicas = deployment.status.ready_replicas

                pods = core_v1_api.list_namespaced_pod(
                    namespace="default",
                    label_selector=f"app={deployment_name}"
                )

                pod_statuses = []
                for pod in pods.items:
                    pod_statuses.append({
                        "Name": pod.metadata.name,
                        "Phase": pod.status.phase,
                        "HostIP": pod.status.host_ip,
                        "PodIP": pod.status.pod_ip,
                        "StartTime": pod.status.start_time.strftime("%Y-%m-%d %H:%M:%S")
                    })

                all_deployments_status.append({
                    "DeploymentName": deployment_name,
                    "Replicas": replicas,
                    "ReadyReplicas": ready_replicas,
                    "PodStatuses": pod_statuses
                })

            return all_deployments_status
        except ApiException as e:
            print(f"Exception when getting all deployments status: {e}")
            raise e
