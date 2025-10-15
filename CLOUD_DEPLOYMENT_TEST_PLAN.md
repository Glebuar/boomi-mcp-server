# Cloud Deployment Test Plan

This document outlines the step-by-step plan to test and deploy the Boomi MCP Server to actual cloud infrastructure.

## Testing Strategy

We'll follow a progressive deployment approach:
1. Local Docker testing
2. Local docker-compose testing
3. GCP Cloud Run deployment (simplest serverless option)
4. Full production setup with GCP Secret Manager and Google OAuth

## Prerequisites Check

- [x] Docker installed
- [x] gcloud CLI installed and configured
- [ ] GCP project created
- [ ] Billing enabled on GCP project
- [ ] Boomi credentials available
- [ ] Google OAuth client credentials (for production auth)

## Phase 1: Local Docker Testing

### Step 1.1: Build Docker Image

```bash
cd /home/gleb/boomi/boomi-mcp-server

# Build the image
docker build -t boomi-mcp-server:test .

# Verify image was built
docker images | grep boomi-mcp-server
```

**Expected output:** Image listed with tag `test`

### Step 1.2: Test Container Locally

```bash
# Create a test environment file
cat > .env.test <<EOF
# Server Configuration
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp
LOG_LEVEL=info

# JWT Authentication (Development - HS256)
MCP_JWT_ALG=HS256
MCP_JWT_SECRET=test-secret-for-local-testing
MCP_JWT_ISSUER=https://local-issuer
MCP_JWT_AUDIENCE=boomi-mcp

# Secrets Storage (SQLite for local testing)
SECRETS_BACKEND=sqlite
SECRETS_DB=/app/data/secrets.sqlite

# CORS Configuration
CORS_ORIGINS=*

# Boomi Credentials (from your existing .env)
BOOMI_ACCOUNT=${BOOMI_ACCOUNT}
BOOMI_USER=${BOOMI_USER}
BOOMI_SECRET=${BOOMI_SECRET}
EOF

# Run the container
docker run -d \
    --name boomi-mcp-test \
    -p 8000:8000 \
    --env-file .env.test \
    -v $(pwd)/test-data:/app/data \
    boomi-mcp-server:test

# Check if container is running
docker ps | grep boomi-mcp-test

# View logs
docker logs -f boomi-mcp-test
```

### Step 1.3: Test Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected: {"status":"healthy","service":"boomi-mcp"}

# Test ready endpoint
curl http://localhost:8000/ready

# Expected: {"status":"ready","service":"boomi-mcp"}

# Test metrics endpoint
curl http://localhost:8000/metrics

# Test root endpoint
curl http://localhost:8000/

# Generate test JWT token
python3 generate_token.py test-user@example.com 60

# Test MCP endpoint with JWT
export TEST_JWT='<token-from-above>'
curl -H "Authorization: Bearer $TEST_JWT" http://localhost:8000/mcp
```

### Step 1.4: Cleanup Local Test

```bash
# Stop and remove container
docker stop boomi-mcp-test
docker rm boomi-mcp-test

# Clean up test data
rm -rf test-data/
rm .env.test
```

## Phase 2: Docker Compose Testing

### Step 2.1: Configure Docker Compose

```bash
# Copy cloud env example
cp .env.cloud.example .env.cloud

# Edit .env.cloud with your credentials
vim .env.cloud

# Update these values:
# - MCP_JWT_SECRET (generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
# - BOOMI_ACCOUNT
# - BOOMI_USER
# - BOOMI_SECRET
# - Keep SECRETS_BACKEND=sqlite for now
```

### Step 2.2: Start Services

```bash
# Start the server
docker-compose up -d

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f boomi-mcp
```

### Step 2.3: Test Docker Compose Deployment

```bash
# Test endpoints (same as Phase 1.3)
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/metrics

# Generate token and test MCP
python3 generate_token.py test-user@example.com 60
export TEST_JWT='<token>'
curl -H "Authorization: Bearer $TEST_JWT" http://localhost:8000/mcp
```

### Step 2.4: Test with NGINX Proxy (Optional)

```bash
# Create nginx.conf
cat > nginx.conf <<'EOF'
events {
    worker_connections 1024;
}

http {
    upstream boomi_mcp {
        server boomi-mcp:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://boomi_mcp;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Start with NGINX
docker-compose --profile with-proxy up -d

# Test through NGINX
curl http://localhost/health
```

### Step 2.5: Cleanup Docker Compose

```bash
docker-compose down
docker-compose --profile with-proxy down
```

## Phase 3: GCP Cloud Run Deployment

### Step 3.1: GCP Project Setup

```bash
# Set your GCP project
export PROJECT_ID=<your-project-id>
export REGION=us-central1
export SERVICE_NAME=boomi-mcp-server

# Configure gcloud
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled | grep -E "(run|cloudbuild|secretmanager|containerregistry)"
```

### Step 3.2: Create Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create boomi-mcp-sa \
    --display-name="Boomi MCP Server Service Account" \
    --description="Service account for Boomi MCP Server on Cloud Run"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Grant Secret Manager admin (for creating secrets)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.admin"

# Verify service account was created
gcloud iam service-accounts list | grep boomi-mcp-sa
```

### Step 3.3: Build and Push Container to GCR

```bash
# Build and submit to Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Verify image was pushed
gcloud container images list --repository=gcr.io/$PROJECT_ID | grep $SERVICE_NAME
gcloud container images list-tags gcr.io/$PROJECT_ID/$SERVICE_NAME
```

### Step 3.4: Deploy to Cloud Run (Development Mode - SQLite)

First deployment with simple SQLite storage for testing:

```bash
# Generate a JWT secret
JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --service-account boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --min-instances 1 \
    --max-instances 5 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --set-env-vars "MCP_HOST=0.0.0.0,MCP_PORT=8080,MCP_PATH=/mcp" \
    --set-env-vars "LOG_LEVEL=info" \
    --set-env-vars "MCP_JWT_ALG=HS256" \
    --set-env-vars "MCP_JWT_SECRET=$JWT_SECRET" \
    --set-env-vars "MCP_JWT_ISSUER=https://cloud-issuer" \
    --set-env-vars "MCP_JWT_AUDIENCE=boomi-mcp" \
    --set-env-vars "SECRETS_BACKEND=sqlite" \
    --set-env-vars "CORS_ORIGINS=*" \
    --set-env-vars "BOOMI_ACCOUNT=$BOOMI_ACCOUNT" \
    --set-env-vars "BOOMI_USER=$BOOMI_USER" \
    --set-env-vars "BOOMI_SECRET=$BOOMI_SECRET"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Service URL: $SERVICE_URL"
```

### Step 3.5: Test Cloud Run Deployment

```bash
# Test health endpoint
curl $SERVICE_URL/health

# Test ready endpoint
curl $SERVICE_URL/ready

# Test metrics endpoint
curl $SERVICE_URL/metrics

# Generate JWT token for cloud deployment
python3 generate_token.py cloud-user@example.com 60

# Save token
export CLOUD_JWT='<token-from-above>'

# Test authenticated MCP endpoint
curl -H "Authorization: Bearer $CLOUD_JWT" $SERVICE_URL/mcp
```

### Step 3.6: Test with Claude Code

```bash
# Add to Claude Code configuration
claude mcp add-json boomi-cloud "{
  \"type\": \"http\",
  \"url\": \"$SERVICE_URL/mcp\",
  \"headers\": { \"Authorization\": \"Bearer $CLOUD_JWT\" }
}"

# Verify connection
claude mcp list

# Test in Claude Code
# Open Claude Code and run:
# "Show me my Boomi account info"
```

## Phase 4: Production Setup with GCP Secret Manager

### Step 4.1: Store Secrets in GCP Secret Manager

```bash
# Create a test secret for a user
echo -n "{\"username\":\"$BOOMI_USER\",\"password\":\"$BOOMI_SECRET\",\"account_id\":\"$BOOMI_ACCOUNT\"}" | \
    gcloud secrets create boomi-mcp-test-user-at-example-com-default \
    --data-file=- \
    --replication-policy=automatic

# Verify secret was created
gcloud secrets list | grep boomi-mcp

# Grant service account access
gcloud secrets add-iam-policy-binding boomi-mcp-test-user-at-example-com-default \
    --member="serviceAccount:boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 4.2: Update Cloud Run to Use GCP Secret Manager

```bash
# Update the deployment to use GCP Secret Manager
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --update-env-vars "SECRETS_BACKEND=gcp,GCP_PROJECT_ID=$PROJECT_ID"

# Verify update
gcloud run services describe $SERVICE_NAME --region $REGION --format yaml | grep -A 5 "env:"
```

### Step 4.3: Test Secret Manager Integration

```bash
# Test that the service can read secrets
curl -H "Authorization: Bearer $CLOUD_JWT" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"method":"tools/list"}' \
    $SERVICE_URL/mcp

# Try to call boomi_account_info
# This should work if Secret Manager is configured correctly
```

## Phase 5: Production Google OAuth Setup

### Step 5.1: Create Google OAuth Client

1. Go to GCP Console > APIs & Services > Credentials
2. Click "Create Credentials" > "OAuth 2.0 Client ID"
3. Application type: "Web application"
4. Name: "Boomi MCP Server"
5. Authorized redirect URIs: `$SERVICE_URL/auth/callback`
6. Save CLIENT_ID and CLIENT_SECRET

### Step 5.2: Configure OAuth in Cloud Run

```bash
# Store OAuth credentials in Secret Manager
echo -n "<YOUR_CLIENT_ID>" | gcloud secrets create boomi-mcp-oauth-client-id --data-file=-
echo -n "<YOUR_CLIENT_SECRET>" | gcloud secrets create boomi-mcp-oauth-client-secret --data-file=-

# Get the JWKS URI for Google
GOOGLE_JWKS_URI="https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUER="https://accounts.google.com"
GOOGLE_CLIENT_ID="<YOUR_CLIENT_ID>"

# Update Cloud Run with RS256 + Google OAuth
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --update-env-vars "MCP_JWT_ALG=RS256" \
    --update-env-vars "MCP_JWT_JWKS_URI=$GOOGLE_JWKS_URI" \
    --update-env-vars "MCP_JWT_ISSUER=$GOOGLE_ISSUER" \
    --update-env-vars "MCP_JWT_AUDIENCE=$GOOGLE_CLIENT_ID"
```

### Step 5.3: Get Real Google OAuth Token

```bash
# Install Google Auth library
pip install google-auth google-auth-oauthlib google-auth-httplib2

# Create token fetcher script
cat > get_google_token.py <<'EOF'
import google.auth.transport.requests
import google.oauth2.id_token

def get_id_token(audience):
    """Get Google ID token for the current user."""
    request = google.auth.transport.requests.Request()
    token = google.oauth2.id_token.fetch_id_token(request, audience)
    return token

if __name__ == "__main__":
    import sys
    audience = sys.argv[1] if len(sys.argv) > 1 else "boomi-mcp"
    token = get_id_token(audience)
    print(token)
EOF

# Get real OAuth token
REAL_TOKEN=$(python3 get_google_token.py $GOOGLE_CLIENT_ID)

# Test with real token
curl -H "Authorization: Bearer $REAL_TOKEN" $SERVICE_URL/health
```

### Step 5.4: Final End-to-End Test

```bash
# Update Claude Code with real OAuth token
claude mcp add-json boomi-cloud "{
  \"type\": \"http\",
  \"url\": \"$SERVICE_URL/mcp\",
  \"headers\": { \"Authorization\": \"Bearer $REAL_TOKEN\" }
}"

# Test in Claude Code
# Should work with full production setup:
# - RS256 + Google OAuth authentication
# - GCP Secret Manager for credentials
# - Cloud Run serverless deployment
```

## Verification Checklist

After completing all phases:

- [ ] Docker image builds successfully
- [ ] Container runs locally with health checks passing
- [ ] Docker Compose deployment works
- [ ] Cloud Run deployment successful
- [ ] Health/ready/metrics endpoints accessible
- [ ] SQLite storage works in Cloud Run
- [ ] GCP Secret Manager integration works
- [ ] Service account has correct permissions
- [ ] Google OAuth authentication works
- [ ] Claude Code can connect to cloud deployment
- [ ] Can retrieve Boomi account info through cloud MCP
- [ ] Logs are visible in Cloud Console
- [ ] Auto-scaling works (test with load)

## Monitoring & Maintenance

### View Cloud Run Logs

```bash
# Real-time logs
gcloud run services logs tail $SERVICE_NAME --region $REGION

# View recent logs
gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50

# Filter logs
gcloud run services logs read $SERVICE_NAME --region $REGION --filter "severity>=ERROR"
```

### Update Deployment

```bash
# Rebuild and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --region $REGION
```

### Scale Service

```bash
# Adjust min/max instances
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --min-instances 2 \
    --max-instances 10
```

## Cost Estimation (GCP)

- **Cloud Run**: $0.00002400 per vCPU-second, $0.00000250 per GiB-second
- **Secret Manager**: $0.06 per 10,000 access operations
- **Cloud Build**: First 120 build-minutes per day free
- **Egress**: First 1 GB per month free

Estimated monthly cost for low-volume usage: **$5-20/month**

## Rollback Plan

If issues occur in production:

```bash
# List revisions
gcloud run revisions list --service $SERVICE_NAME --region $REGION

# Rollback to previous revision
gcloud run services update-traffic $SERVICE_NAME \
    --region $REGION \
    --to-revisions <PREVIOUS_REVISION>=100
```

## Next Steps

1. Follow Phase 1 to test Docker locally
2. Progress through phases incrementally
3. Document any issues or modifications needed
4. Once working, consider:
   - Setting up custom domain
   - Enabling Cloud Armor for DDoS protection
   - Adding Cloud Monitoring alerts
   - Implementing request rate limiting
   - Creating staging environment
