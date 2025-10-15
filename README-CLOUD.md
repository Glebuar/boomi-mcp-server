# Boomi MCP Cloud Deployment Guide

Production-ready deployment guide for Boomi MCP Server on cloud platforms.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Cloud Platforms](#cloud-platforms)
  - [Google Cloud Platform (GCP)](#google-cloud-platform-gcp)
  - [Amazon Web Services (AWS)](#amazon-web-services-aws)
  - [Microsoft Azure](#microsoft-azure)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Docker Deployment](#docker-deployment)
- [Authentication Setup](#authentication-setup)
- [Secret Management](#secret-management)
- [Monitoring & Observability](#monitoring--observability)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The cloud version of Boomi MCP Server extends the local development server with:

- **Production-grade authentication** (RS256 + JWKS)
- **Cloud secret management** (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
- **Container orchestration** (Kubernetes, Cloud Run, ECS, Container Apps)
- **High availability** (Load balancing, auto-scaling, health checks)
- **Monitoring & logging** (Structured logs, metrics, error tracking)

## Architecture

```
┌─────────────┐
│   Claude    │
│    Code     │
└──────┬──────┘
       │ JWT Auth
       ▼
┌─────────────────┐
│  Load Balancer  │
│   (Ingress)     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────┐   ┌─────┐
│ Pod │   │ Pod │  MCP Server (FastAPI)
└──┬──┘   └──┬──┘
   │         │
   └────┬────┘
        ▼
┌────────────────┐
│ Cloud Secrets  │  AWS/GCP/Azure
│   Manager      │  Secret Storage
└────────────────┘
        │
        ▼
┌────────────────┐
│   Boomi API    │
└────────────────┘
```

## Prerequisites

- Docker (20.10+)
- Kubernetes cluster (1.24+) or managed service (GKE, EKS, AKS)
- Cloud CLI tools (gcloud, aws, or az)
- kubectl (1.24+)
- Identity Provider account (Auth0, Okta, Google, Azure AD, etc.)
- Cloud provider account with appropriate permissions

## Quick Start

### Local Testing with Docker

```bash
# 1. Build the container
docker build -t boomi-mcp-server:latest .

# 2. Run with docker-compose
cp .env.cloud.example .env.cloud
# Edit .env.cloud with your configuration
docker-compose up

# 3. Test the server
curl http://localhost:8000/health
```

### Quick Deploy to Cloud

See platform-specific sections below for detailed deployment instructions.

## Cloud Platforms

### Google Cloud Platform (GCP)

#### Option 1: Cloud Run (Serverless)

Cloud Run is the simplest deployment option for GCP:

```bash
# 1. Set up environment
export PROJECT_ID=your-project-id
export REGION=us-central1
export SERVICE_NAME=boomi-mcp-server

# 2. Configure gcloud
gcloud config set project $PROJECT_ID

# 3. Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# 4. Create service account
gcloud iam service-accounts create boomi-mcp-sa \
    --display-name="Boomi MCP Server Service Account"

# 5. Grant Secret Manager permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# 6. Build and push container
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# 7. Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --service-account boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars "SECRETS_BACKEND=gcp,GCP_PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "MCP_JWT_ALG=RS256,MCP_JWT_ISSUER=https://accounts.google.com" \
    --set-env-vars "MCP_JWT_JWKS_URI=https://www.googleapis.com/oauth2/v3/certs" \
    --set-env-vars "MCP_JWT_AUDIENCE=your-client-id" \
    --allow-unauthenticated \
    --min-instances 1 \
    --max-instances 10
```

#### Option 2: Google Kubernetes Engine (GKE)

```bash
# 1. Create GKE cluster
gcloud container clusters create boomi-mcp-cluster \
    --region $REGION \
    --num-nodes 2 \
    --machine-type n1-standard-2 \
    --enable-autoscaling --min-nodes 2 --max-nodes 10 \
    --enable-workload-identity

# 2. Get credentials
gcloud container clusters get-credentials boomi-mcp-cluster --region $REGION

# 3. Set up Workload Identity
kubectl create serviceaccount boomi-mcp -n default

gcloud iam service-accounts add-iam-policy-binding \
    boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$PROJECT_ID.svc.id.goog[default/boomi-mcp]"

kubectl annotate serviceaccount boomi-mcp \
    iam.gke.io/gcp-service-account=boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com

# 4. Update k8s/configmap.yaml with your values
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# 5. Check deployment
kubectl get pods
kubectl get svc
kubectl get ingress
```

### Amazon Web Services (AWS)

#### Option 1: ECS Fargate (Serverless Containers)

```bash
# 1. Set up environment
export AWS_REGION=us-east-1
export CLUSTER_NAME=boomi-mcp-cluster
export SERVICE_NAME=boomi-mcp-server

# 2. Create ECS cluster
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION

# 3. Create IAM role for task execution
aws iam create-role \
    --role-name boomiMcpTaskExecutionRole \
    --assume-role-policy-document file://aws-task-execution-role.json

aws iam attach-role-policy \
    --role-name boomiMcpTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# 4. Create IAM role for Secrets Manager access
aws iam create-role \
    --role-name boomiMcpTaskRole \
    --assume-role-policy-document file://aws-task-role.json

aws iam attach-role-policy \
    --role-name boomiMcpTaskRole \
    --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

# 5. Build and push to ECR
aws ecr create-repository --repository-name $SERVICE_NAME --region $AWS_REGION

# Get ECR login
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin <account-id>.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push
docker build -t $SERVICE_NAME .
docker tag $SERVICE_NAME:latest <account-id>.dkr.ecr.$AWS_REGION.amazonaws.com/$SERVICE_NAME:latest
docker push <account-id>.dkr.ecr.$AWS_REGION.amazonaws.com/$SERVICE_NAME:latest

# 6. Create task definition and service (use AWS Console or CLI)
```

#### Option 2: Amazon EKS

```bash
# 1. Create EKS cluster
eksctl create cluster \
    --name boomi-mcp-cluster \
    --region $AWS_REGION \
    --nodegroup-name standard-workers \
    --node-type t3.medium \
    --nodes 2 \
    --nodes-min 2 \
    --nodes-max 10 \
    --managed

# 2. Set up IRSA (IAM Roles for Service Accounts)
eksctl create iamserviceaccount \
    --name boomi-mcp \
    --namespace default \
    --cluster boomi-mcp-cluster \
    --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
    --approve

# 3. Deploy with kubectl (same as GKE section above)
kubectl apply -f k8s/
```

### Microsoft Azure

#### Option 1: Azure Container Apps

```bash
# 1. Set up environment
export RESOURCE_GROUP=boomi-mcp-rg
export LOCATION=eastus
export CONTAINER_APP_ENV=boomi-mcp-env
export CONTAINER_APP_NAME=boomi-mcp-server

# 2. Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# 3. Create Container Apps environment
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# 4. Create Azure Key Vault
az keyvault create \
    --name boomi-mcp-vault \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# 5. Build and push to ACR
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name boomiMcpRegistry \
    --sku Basic

az acr build \
    --registry boomiMcpRegistry \
    --image $CONTAINER_APP_NAME:latest .

# 6. Deploy Container App
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image boomiMcpRegistry.azurecr.io/$CONTAINER_APP_NAME:latest \
    --target-port 8000 \
    --ingress external \
    --env-vars \
        "SECRETS_BACKEND=azure" \
        "AZURE_KEY_VAULT_URL=https://boomi-mcp-vault.vault.azure.net/" \
        "MCP_JWT_ALG=RS256" \
    --min-replicas 1 \
    --max-replicas 10
```

#### Option 2: Azure Kubernetes Service (AKS)

```bash
# 1. Create AKS cluster
az aks create \
    --resource-group $RESOURCE_GROUP \
    --name boomi-mcp-cluster \
    --node-count 2 \
    --enable-addons monitoring \
    --generate-ssh-keys \
    --enable-workload-identity \
    --enable-oidc-issuer

# 2. Get credentials
az aks get-credentials \
    --resource-group $RESOURCE_GROUP \
    --name boomi-mcp-cluster

# 3. Deploy with kubectl
kubectl apply -f k8s/
```

## Kubernetes Deployment

### Prerequisites

1. Kubernetes cluster (1.24+)
2. kubectl configured
3. Docker image built and pushed to registry

### Deployment Steps

1. **Update configuration files:**

```bash
cd k8s/

# Edit configmap.yaml with your settings
vim configmap.yaml

# Edit secret.yaml with your JWT configuration
vim secret.yaml
```

2. **Apply Kubernetes manifests:**

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

3. **Verify deployment:**

```bash
# Check pods are running
kubectl get pods -l app=boomi-mcp

# Check service
kubectl get svc boomi-mcp-server

# Check ingress
kubectl get ingress boomi-mcp-ingress

# View logs
kubectl logs -l app=boomi-mcp --tail=50 -f
```

4. **Test the deployment:**

```bash
# Get ingress IP/hostname
kubectl get ingress boomi-mcp-ingress

# Test health endpoint
curl https://your-domain.com/health
```

## Docker Deployment

### Build and Run Locally

```bash
# Build the image
docker build -t boomi-mcp-server:latest .

# Run with environment file
docker run -d \
    --name boomi-mcp \
    -p 8000:8000 \
    --env-file .env.cloud \
    boomi-mcp-server:latest

# View logs
docker logs -f boomi-mcp

# Test
curl http://localhost:8000/health
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# With NGINX proxy
docker-compose --profile with-proxy up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Authentication Setup

### RS256 with JWKS (Production)

The cloud deployment uses asymmetric JWT authentication with JWKS:

#### Auth0

```bash
# .env.cloud
MCP_JWT_ALG=RS256
MCP_JWT_JWKS_URI=https://your-tenant.auth0.com/.well-known/jwks.json
MCP_JWT_ISSUER=https://your-tenant.auth0.com/
MCP_JWT_AUDIENCE=your-api-identifier
```

#### Azure AD

```bash
MCP_JWT_ALG=RS256
MCP_JWT_JWKS_URI=https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
MCP_JWT_ISSUER=https://sts.windows.net/{tenant-id}/
MCP_JWT_AUDIENCE=your-client-id
```

#### Google

```bash
MCP_JWT_ALG=RS256
MCP_JWT_JWKS_URI=https://www.googleapis.com/oauth2/v3/certs
MCP_JWT_ISSUER=https://accounts.google.com
MCP_JWT_AUDIENCE=your-client-id
```

### Generating Tokens

For production, tokens should be issued by your IdP. For testing:

```python
# Use your IdP's SDK to get tokens
# Example with Auth0 Python SDK:
from auth0.authentication import GetToken

domain = 'your-tenant.auth0.com'
client_id = 'your-client-id'
client_secret = 'your-client-secret'

get_token = GetToken(domain)
token = get_token.client_credentials(
    client_id,
    client_secret,
    'your-api-identifier'
)
access_token = token['access_token']
```

## Secret Management

### GCP Secret Manager

```bash
# Create secrets
echo -n '{"username":"BOOMI_TOKEN.user@example.com","password":"token","account_id":"account-123"}' | \
    gcloud secrets create boomi-mcp-user-at-example-com-default \
    --data-file=- \
    --replication-policy=automatic

# Grant access to service account
gcloud secrets add-iam-policy-binding boomi-mcp-user-at-example-com-default \
    --member="serviceAccount:boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### AWS Secrets Manager

```bash
# Create secret
aws secretsmanager create-secret \
    --name boomi-mcp/user@example.com/default \
    --secret-string '{"username":"BOOMI_TOKEN.user@example.com","password":"token","account_id":"account-123"}' \
    --region us-east-1

# Grant access to IAM role
aws secretsmanager put-resource-policy \
    --secret-id boomi-mcp/user@example.com/default \
    --resource-policy file://secret-policy.json
```

### Azure Key Vault

```bash
# Create secret
az keyvault secret set \
    --vault-name boomi-mcp-vault \
    --name boomi-mcp-user-at-example-com-default \
    --value '{"username":"BOOMI_TOKEN.user@example.com","password":"token","account_id":"account-123"}'

# Grant access to managed identity
az keyvault set-policy \
    --name boomi-mcp-vault \
    --object-id <managed-identity-id> \
    --secret-permissions get list
```

## Monitoring & Observability

### Structured Logging

The cloud server outputs structured JSON logs:

```json
{
  "timestamp": "2025-01-14T10:30:00Z",
  "level": "INFO",
  "message": "Request: GET /health",
  "service": "boomi-mcp",
  "trace_id": "abc123"
}
```

### Metrics Endpoint

Access metrics at `/metrics`:

```bash
curl https://your-domain.com/metrics
```

### Health Checks

- `/health` - Liveness probe (server is running)
- `/ready` - Readiness probe (server can handle requests)

### Integration with Cloud Monitoring

#### GCP Cloud Logging

Logs are automatically collected when running on Cloud Run or GKE.

#### AWS CloudWatch

Configure CloudWatch Logs in your ECS task definition or EKS deployment.

#### Azure Monitor

Container Apps and AKS automatically send logs to Azure Monitor.

## Security Best Practices

### 1. Use Managed Identities

- **GCP**: Workload Identity
- **AWS**: IRSA (IAM Roles for Service Accounts)
- **Azure**: Workload Identity or Managed Identity

### 2. Enable HTTPS Only

Use TLS certificates from:
- Let's Encrypt (cert-manager on K8s)
- Cloud-managed certificates (Cloud Run, Container Apps)
- AWS Certificate Manager (ALB)

### 3. Restrict Network Access

- Use VPC/VNET for private communication
- Configure firewall rules
- Enable Cloud Armor/WAF for DDoS protection

### 4. Rotate Secrets Regularly

- Set up automatic rotation in secret managers
- Use short-lived JWT tokens (1 hour max)
- Implement token refresh flow

### 5. Enable Audit Logging

- Log all credential access
- Monitor for suspicious activity
- Set up alerts for failed authentication

### 6. Principle of Least Privilege

- Grant minimal IAM permissions
- Use separate service accounts per environment
- Regularly review and audit permissions

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Common issues:
# - Image pull errors: Check registry access
# - Config errors: Verify ConfigMap and Secrets
# - Resource limits: Adjust requests/limits
```

### Authentication Failures

```bash
# Test JWT token
curl -H "Authorization: Bearer $TOKEN" https://your-domain.com/health

# Verify JWKS URI is accessible
curl https://your-idp.com/.well-known/jwks.json

# Check token claims
python3 -c "import jwt; print(jwt.decode('$TOKEN', options={'verify_signature': False}))"
```

### Secret Access Errors

```bash
# GCP: Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:boomi-mcp-sa@*"

# AWS: Check IAM role policies
aws iam get-role-policy --role-name boomiMcpTaskRole --policy-name SecretsAccess

# Azure: Check Key Vault access policies
az keyvault show --name boomi-mcp-vault --query properties.accessPolicies
```

### High Latency

- Check replica count (scale up if needed)
- Verify network connectivity to Boomi API
- Enable connection pooling
- Review resource limits

### Database Lock Errors (SQLite)

SQLite is not recommended for production with multiple replicas. Switch to cloud secret manager:

```bash
# Update configmap
kubectl patch configmap boomi-mcp-config -p '{"data":{"secrets_backend":"gcp"}}'

# Restart pods
kubectl rollout restart deployment boomi-mcp-server
```

## Support

For issues or questions:
- Check logs: `kubectl logs -l app=boomi-mcp`
- Review documentation: [README.md](README.md)
- Open GitHub issue: Include logs and configuration (redact secrets!)

---

**Production Checklist:**

- [ ] RS256 JWT with JWKS configured
- [ ] Cloud secret manager enabled
- [ ] TLS/HTTPS configured
- [ ] Health checks configured
- [ ] Auto-scaling enabled
- [ ] Monitoring and alerting set up
- [ ] Backup and disaster recovery plan
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Documentation updated
