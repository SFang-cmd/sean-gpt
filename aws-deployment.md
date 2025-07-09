# AWS Deployment Guide for Sean GPT

## 🚀 Quick AWS Container Deployment

### Option 1: AWS App Runner (Easiest)

1. **Build and Push to ECR:**
```bash
# Create ECR repository
aws ecr create-repository --repository-name sean-gpt --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag production image
docker build -f Dockerfile.production -t sean-gpt:latest .
docker tag sean-gpt:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/sean-gpt:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/sean-gpt:latest
```

2. **Create App Runner Service:**
   - Go to AWS App Runner console
   - Create service → Container registry → Amazon ECR
   - Select your sean-gpt repository
   - Configure:
     - Port: 8501
     - Environment variables: `OPENAI_API_KEY=your-key`
     - CPU: 1 vCPU, Memory: 2 GB
   - Deploy!

### Option 2: AWS ECS with Fargate (More Control)

1. **Create ECS Cluster:**
```bash
aws ecs create-cluster --cluster-name sean-gpt-cluster
```

2. **Create Task Definition:**
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

3. **Create ECS Service:**
```bash
aws ecs create-service \
  --cluster sean-gpt-cluster \
  --service-name sean-gpt-service \
  --task-definition sean-gpt:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration file://network-config.json
```

### Option 3: AWS Lightsail Container (Budget-Friendly)

1. **Create Lightsail Container Service:**
```bash
aws lightsail create-container-service \
  --service-name sean-gpt \
  --power small \
  --scale 1
```

2. **Push and Deploy:**
```bash
aws lightsail push-container-image \
  --service-name sean-gpt \
  --label sean-gpt-latest \
  --image sean-gpt:latest

aws lightsail create-container-service-deployment \
  --service-name sean-gpt \
  --cli-input-json file://lightsail-deployment.json
```

---

## 📋 Required AWS Configuration Files

### Environment Variables Needed:
- `OPENAI_API_KEY=sk-your-key-here`
- `GITHUB_WEBHOOK_SECRET=optional-for-webhooks`

### Estimated Costs:
- **App Runner**: ~$15-25/month
- **ECS Fargate**: ~$20-30/month  
- **Lightsail**: ~$10-15/month

### TODO:
- [ ] Set up GitHub webhooks for real-time updates
- [ ] Configure custom domain (optional)
- [ ] Set up monitoring and logging