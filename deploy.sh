#!/bin/bash

# Contextor MCP Server Deployment Script
# Supports AWS Lambda and Vercel deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PLATFORM=""
ENVIRONMENT="dev"
REGION="us-east-1"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    --env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --help)
      echo "Usage: ./deploy.sh --platform [aws|vercel] [--env dev|prod] [--region region]"
      echo ""
      echo "Options:"
      echo "  --platform    Deployment platform (aws or vercel)"
      echo "  --env         Environment (dev or prod, default: dev)"
      echo "  --region      AWS region (default: us-east-1)"
      echo ""
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Validate platform
if [ -z "$PLATFORM" ]; then
  echo -e "${RED}Error: --platform is required${NC}"
  echo "Use --help for usage information"
  exit 1
fi

echo -e "${GREEN}Contextor MCP Server Deployment${NC}"
echo "================================"
echo "Platform: $PLATFORM"
echo "Environment: $ENVIRONMENT"

# Install dependencies
echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"
if command -v poetry &> /dev/null; then
  poetry install --no-dev -q
else
  echo -e "${RED}Poetry not found. Please install: pip install poetry${NC}"
  exit 1
fi

# Platform-specific deployment
case $PLATFORM in
  aws)
    echo ""
    echo -e "${YELLOW}Deploying to AWS Lambda...${NC}"
    
    # Check for SAM CLI
    if ! command -v sam &> /dev/null; then
      echo -e "${RED}SAM CLI not found. Please install: pip install aws-sam-cli${NC}"
      exit 1
    fi
    
    # Build the application
    echo "Building Lambda package..."
    sam build --use-container
    
    # Deploy based on environment
    if [ "$ENVIRONMENT" = "prod" ]; then
      echo "Deploying to production..."
      sam deploy \
        --stack-name contextor-mcp-prod \
        --region $REGION \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides "Environment=prod" \
        --no-confirm-changeset
    else
      echo "Deploying to development..."
      sam deploy \
        --stack-name contextor-mcp-dev \
        --region $REGION \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides "Environment=dev" \
        --guided
    fi
    
    # Output endpoint
    echo ""
    echo -e "${GREEN}Deployment complete!${NC}"
    echo "API Endpoint:"
    aws cloudformation describe-stacks \
      --stack-name contextor-mcp-$ENVIRONMENT \
      --region $REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
      --output text
    ;;
    
  vercel)
    echo ""
    echo -e "${YELLOW}Deploying to Vercel...${NC}"
    
    # Check for Vercel CLI
    if ! command -v vercel &> /dev/null; then
      echo -e "${RED}Vercel CLI not found. Please install: npm i -g vercel${NC}"
      exit 1
    fi
    
    # Create api directory if it doesn't exist
    mkdir -p api
    
    # Deploy based on environment
    if [ "$ENVIRONMENT" = "prod" ]; then
      echo "Deploying to production..."
      vercel --prod
    else
      echo "Deploying to development..."
      vercel
    fi
    
    echo ""
    echo -e "${GREEN}Deployment complete!${NC}"
    ;;
    
  *)
    echo -e "${RED}Invalid platform: $PLATFORM${NC}"
    echo "Supported platforms: aws, vercel"
    exit 1
    ;;
esac

echo ""
echo "================================"
echo -e "${GREEN}Deployment successful!${NC}"

# Test the deployment
echo ""
echo -e "${YELLOW}Testing deployment...${NC}"

if [ "$PLATFORM" = "aws" ]; then
  ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name contextor-mcp-$ENVIRONMENT \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)
  
  curl -s "${ENDPOINT}health" | jq .
elif [ "$PLATFORM" = "vercel" ]; then
  # Get the deployment URL from Vercel
  DEPLOYMENT_URL=$(vercel ls --json | jq -r '.[0].url')
  curl -s "https://${DEPLOYMENT_URL}/api/health" | jq .
fi

echo ""
echo -e "${GREEN}Deployment test complete!${NC}"
