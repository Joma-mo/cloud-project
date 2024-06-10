from typing import List, Dict
from pydantic import BaseModel


class Resource(BaseModel):
    CPU: str
    RAM: str


class Env(BaseModel):
    Key: str
    Value: str
    IsSecret: bool


class ServicePort(BaseModel):
    Port: int
    TargetPort: int


class Service(BaseModel):
    Type: str
    Ports: List[ServicePort]


class IngressBackend(BaseModel):
    ServiceName: str
    ServicePort: int


class IngressPath(BaseModel):
    Path: str
    PathType: str
    Backend: IngressBackend


class IngressRule(BaseModel):
    Host: str
    Http: Dict[str, List[IngressPath]]


class Ingress(BaseModel):
    Rules: List[IngressRule]


class Secret(BaseModel):
    Data: Dict[str, str]


class AppConfig(BaseModel):
    AppName: str
    Replicas: int
    ImageAddress: str
    ImageTag: str
    DomainAddress: str
    ServicePort: int
    Resources: Resource
    Envs: List[Env]
    Service: Service
    Ingress: Ingress
    Secret: Secret
