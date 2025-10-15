# Quick Start: Cloud Deployment

## Step-by-Step Guide to Deploy Boomi MCP to GCP Cloud Run

### Prerequisites
- [x] Docker installed and running
- [x] gcloud CLI configured (project: tryitonme)
- [x] Boomi credentials in `.env`

### Phase 1: Local Docker Test (You Run This)

```bash
cd /home/gleb/boomi/boomi-mcp-server

# 1. Build the Docker image
docker build -t boomi-mcp-server:test .

# 2. Create test environment file
cat > .env.test <<EOF
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp
LOG_LEVEL=info
MCP_JWT_ALG=HS256
MCP_JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
MCP_JWT_ISSUER=https://local-issuer
MCP_JWT_AUDIENCE=boomi-mcp
SECRETS_BACKEND=sqlite
SECRETS_DB=/app/data/secrets.sqlite
CORS_ORIGINS=*
EOF

# Load Boomi credentials from existing .env
source .env
echo "BOOMI_ACCOUNT=$BOOMI_ACCOUNT" >> .env.test
echo "BOOMI_USER=$BOOMI_USER" >> .env.test
echo "BOOMI_SECRET=$BOOMI_SECRET" >> .env.test

# 3. Run the container
docker run -d \
    --name boomi-mcp-test \
    -p 8000:8000 \
    --env-file .env.test \
    boomi-mcp-server:test

# 4. Check logs
docker logs -f boomi-mcp-test
# Press Ctrl+C when you see "Starting server"

# 5. Test endpoints
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"boomi-mcp"}

curl http://localhost:8000/ready
# Expected: {"status":"ready","service":"boomi-mcp"}

curl http://localhost:8000/metrics

curl http://localhost:8000/

# 6. Test with JWT token
python3 generate_token.py test-user@example.com 60
# Copy the token from output

export TEST_JWT='<paste-token-here>'

# Test MCP endpoint
curl -H "Authorization: Bearer $TEST_JWT" \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
     http://localhost:8000/mcp

# 7. Cleanup
docker stop boomi-mcp-test
docker rm boomi-mcp-test
```

### Phase 2: Deploy to GCP Cloud Run

```bash
# 1. Set environment variables
export PROJECT_ID=tryitonme
export REGION=us-central1
export SERVICE_NAME=boomi-mcp-server

# Confirm project
gcloud config set project $PROJECT_ID

# 2. Enable required APIs (one-time setup)
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Wait for APIs to be enabled (takes ~1 minute)
echo "Waiting for APIs to be enabled..."
sleep 60

# 3. Create service account
gcloud iam service-accounts create boomi-mcp-sa \
    --display-name="Boomi MCP Server" \
    --description="Service account for Boomi MCP Server on Cloud Run" \
    || echo "Service account may already exist"

# 4. Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.admin"

# 5. Load Boomi credentials
source .env

# 6. Generate JWT secret
JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
echo "Generated JWT Secret: $JWT_SECRET"
echo "Save this secret - you'll need it to generate tokens!"

# 7. Build and deploy to Cloud Run (all-in-one)
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --service-account boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 3 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --port 8000 \
    --set-env-vars "MCP_HOST=0.0.0.0" \
    --set-env-vars "MCP_PORT=8000" \
    --set-env-vars "MCP_PATH=/mcp" \
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

# 8. Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')

echo "================================"
echo "Deployment Complete!"
echo "================================"
echo "Service URL: $SERVICE_URL"
echo "JWT Secret: $JWT_SECRET"
echo "================================"

# Save these for later
echo "SERVICE_URL=$SERVICE_URL" >> .env.cloud.deployed
echo "JWT_SECRET=$JWT_SECRET" >> .env.cloud.deployed
```

### Phase 3: Test Cloud Deployment

```bash
# Load deployment info
source .env.cloud.deployed

# 1. Test health endpoint
curl $SERVICE_URL/health

# 2. Test ready endpoint
curl $SERVICE_URL/ready

# 3. Test metrics endpoint
curl $SERVICE_URL/metrics

# 4. Generate JWT token for cloud
# Set the JWT_SECRET in .env temporarily for token generation
cat > .env.token.temp <<EOF
MCP_JWT_SECRET=$JWT_SECRET
MCP_JWT_ALG=HS256
MCP_JWT_ISSUER=https://cloud-issuer
MCP_JWT_AUDIENCE=boomi-mcp
EOF

# Generate token (valid for 8 hours)
python3 generate_token.py cloud-user@example.com 480

# Copy the token from output
export CLOUD_JWT='<paste-token-here>'

# 5. Test MCP endpoint
curl -H "Authorization: Bearer $CLOUD_JWT" \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
     $SERVICE_URL/mcp

# Clean up temp file
rm .env.token.temp
```

### Phase 4: Connect Claude Code to Cloud MCP

```bash
# Load deployment info
source .env.cloud.deployed

# Make sure you have a valid token
# If needed, regenerate:
# MCP_JWT_SECRET=$JWT_SECRET python3 generate_token.py your-email@example.com 480

export CLOUD_JWT='<your-cloud-token>'

# Add to Claude Code
claude mcp add-json boomi-cloud "{
  \"type\": \"http\",
  \"url\": \"$SERVICE_URL/mcp\",
  \"headers\": { \"Authorization\": \"Bearer $CLOUD_JWT\" }
}"

# Verify it's added
claude mcp list

# Test in Claude Code
claude
# Then ask: "Show me my Boomi account information"
```

### Phase 5: Upgrade to Production (GCP Secret Manager)

```bash
source .env
source .env.cloud.deployed

# 1. Create a secret in GCP Secret Manager for your user
echo -n "{\"username\":\"$BOOMI_USER\",\"password\":\"$BOOMI_SECRET\",\"account_id\":\"$BOOMI_ACCOUNT\"}" | \
    gcloud secrets create boomi-mcp-cloud-user-at-example-com-default \
    --data-file=- \
    --replication-policy=automatic

# 2. Grant service account access
gcloud secrets add-iam-policy-binding boomi-mcp-cloud-user-at-example-com-default \
    --member="serviceAccount:boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# 3. Update Cloud Run to use GCP Secret Manager
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --update-env-vars "SECRETS_BACKEND=gcp,GCP_PROJECT_ID=$PROJECT_ID"

# 4. Test that it works
curl -H "Authorization: Bearer $CLOUD_JWT" \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
     $SERVICE_URL/mcp
```

### Monitoring

```bash
# View logs in real-time
gcloud run services logs tail $SERVICE_NAME --region $REGION

# View recent logs
gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50

# View errors only
gcloud run services logs read $SERVICE_NAME \
    --region $REGION \
    --filter "severity>=ERROR"
```

### Update Deployment

```bash
# After making code changes, redeploy:
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION
```

### Cleanup (if needed)

```bash
# Delete Cloud Run service
gcloud run services delete $SERVICE_NAME --region $REGION

# Delete service account
gcloud iam service-accounts delete boomi-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com

# Delete secrets
gcloud secrets delete boomi-mcp-cloud-user-at-example-com-default
```

## Troubleshooting

### Build fails

```bash
# Check Cloud Build logs
gcloud builds list --limit 5

# Get details of last build
BUILD_ID=$(gcloud builds list --limit 1 --format='value(id)')
gcloud builds log $BUILD_ID
```

### Service doesn't start

```bash
# Check logs
gcloud run services logs read $SERVICE_NAME --region $REGION --limit 100

# Check service status
gcloud run services describe $SERVICE_NAME --region $REGION
```

### Authentication fails

```bash
# Verify JWT secret is set correctly
gcloud run services describe $SERVICE_NAME --region $REGION \
    --format yaml | grep -A 10 "env:"

# Generate new token with correct secret
MCP_JWT_SECRET=<your-jwt-secret> python3 generate_token.py user@example.com 60
```

### Can't access Boomi API

```bash
# Check if Boomi credentials are set
gcloud run services describe $SERVICE_NAME --region $REGION \
    --format yaml | grep BOOMI

# Update credentials
gcloud run services update $SERVICE_NAME --region $REGION \
    --update-env-vars "BOOMI_ACCOUNT=$BOOMI_ACCOUNT,BOOMI_USER=$BOOMI_USER,BOOMI_SECRET=$BOOMI_SECRET"
```

## Cost Optimization

Cloud Run pricing:
- **Free tier**: First 2 million requests per month
- **Compute**: $0.00002400 per vCPU-second, $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests

To minimize costs:
- Set `--min-instances 0` (scales to zero when not used)
- Use `--max-instances 3` to cap maximum cost
- Enable `--concurrency 80` for better resource utilization

Expected monthly cost for light usage: **$0-5**

## Next Steps

Once basic deployment is working:
1. Set up custom domain
2. Enable Google OAuth (RS256) for production auth
3. Set up monitoring alerts
4. Create staging environment
5. Implement CI/CD pipeline
