#!/bin/bash

# AWS Deployment Script for Sean GPT
# Choose your deployment method by commenting/uncommenting sections

set -e

echo "🚀 Sean GPT AWS Deployment Script"
echo "=================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it:"
    echo "   pip install awscli"
    echo "   or visit: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop"
    exit 1
fi

# Check AWS credentials
echo "🔑 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured or expired"
    echo "💡 Run: aws configure"
    echo "   You'll need:"
    echo "   - AWS Access Key ID"
    echo "   - AWS Secret Access Key"
    echo "   - Default region (recommend: us-east-1)"
    echo ""
    echo "📖 Get credentials from: AWS Console → IAM → Users → Your user → Security credentials"
    exit 1
fi

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="sean-gpt"
IMAGE_TAG="latest"

echo "📋 Configuration:"
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo "  Region: $AWS_REGION" 
echo "  Repository: $ECR_REPOSITORY"

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable not set"
    echo "💡 Set it with: export OPENAI_API_KEY=sk-your-key-here"
    exit 1
fi

echo "✅ OpenAI API key found"

# 1. Create ECR repository if it doesn't exist
echo "🔧 Setting up ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION >/dev/null 2>&1 || \
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

# 2. Login to ECR
echo "🔑 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 3. Build production image
echo "🔨 Building production Docker image..."
docker build -f Dockerfile.production -t $ECR_REPOSITORY:$IMAGE_TAG .

# 4. Tag and push to ECR
echo "📤 Pushing to ECR..."
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

echo "✅ Image pushed to ECR successfully!"
echo "📝 Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"

# Choose deployment method
echo ""
echo "🎯 Choose deployment method:"
echo "1. AWS App Runner (Easiest)"
echo "2. AWS ECS Fargate (More control)"
echo "3. AWS Lightsail (Budget-friendly)"
echo ""

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🏃 Setting up App Runner..."
        echo "📋 Next steps:"
        echo "1. Go to AWS App Runner console"
        echo "2. Create service → Container registry → Amazon ECR"
        echo "3. Use image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
        echo "4. Set port: 8501"
        echo "5. Add environment variable: OPENAI_API_KEY=$OPENAI_API_KEY"
        echo "6. Deploy!"
        ;;
    2)
        echo "🐳 Setting up ECS Fargate..."
        # Update task definition with actual values
        sed "s/<account-id>/$AWS_ACCOUNT_ID/g" aws/task-definition.json > aws/task-definition-updated.json
        sed -i "s/YOUR_OPENAI_API_KEY_HERE/$OPENAI_API_KEY/g" aws/task-definition-updated.json
        
        # Create cluster and task definition
        aws ecs create-cluster --cluster-name sean-gpt-cluster --region $AWS_REGION || true
        aws ecs register-task-definition --cli-input-json file://aws/task-definition-updated.json --region $AWS_REGION
        
        echo "✅ ECS cluster and task definition created!"
        echo "📋 Next steps:"
        echo "1. Update aws/network-config.json with your VPC subnets and security groups"
        echo "2. Run: aws ecs create-service --cli-input-json file://create-service.json"
        ;;
    3)
        echo "💡 Setting up Lightsail..."
        # Update deployment config
        sed "s/YOUR_OPENAI_API_KEY_HERE/$OPENAI_API_KEY/g" aws/lightsail-deployment.json > aws/lightsail-deployment-updated.json
        
        # Create container service
        aws lightsail create-container-service \
            --service-name sean-gpt \
            --power small \
            --scale 1 || true
        
        # Push container image
        aws lightsail push-container-image \
            --service-name sean-gpt \
            --label sean-gpt-latest \
            --image $ECR_REPOSITORY:$IMAGE_TAG
        
        # Deploy
        aws lightsail create-container-service-deployment \
            --service-name sean-gpt \
            --cli-input-json file://aws/lightsail-deployment-updated.json
        
        echo "✅ Lightsail deployment initiated!"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment process initiated!"
echo "⏱️  It may take 5-10 minutes for your service to be available"
echo "📊 Monitor progress in the AWS console"
echo ""
echo "🔗 Don't forget to set up GitHub webhooks later for auto-updates!"
echo "📖 See aws-deployment.md for webhook setup instructions"