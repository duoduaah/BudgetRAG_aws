set -e
set -a
source .env
set +a

# Configuration
export AWS_REGION="${AWS_REGION:-ca-central-1}"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO_NAME="budget-agent-api"
export IMAGE_TAG="latest"
export LAMBDA_FUNCTION_NAME="budget-agent-api"
export API_NAME="BudgetAgentAPI"

echo "======================================"
echo "Budget Agent API Deployment"
echo "======================================"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo "ECR Repo: $ECR_REPO_NAME"
echo "======================================"

# Step 1: Build Docker image
echo ""
echo "Step 1: Building Docker image..."
docker build --platform linux/amd64 -t $ECR_REPO_NAME:$IMAGE_TAG .

# Step 2: Create ECR repository (if it doesn't exist)
echo ""
echo "Step 2: Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository \
    --repository-name $ECR_REPO_NAME \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true

# Step 3: Login to ECR
echo ""
echo "Step 3: Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Step 4: Tag and push image
echo ""
echo "Step 4: Pushing image to ECR..."
docker tag $ECR_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG

# Step 5: Create or update Lambda function
echo ""
echo "Step 5: Deploying Lambda function..."

# Check if Lambda function exists
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG \
        --region $AWS_REGION
    
    # Wait for update to complete
    aws lambda wait function-updated --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION
    
    # Update environment variables
    aws lambda update-function-configuration \
        --function-name $LAMBDA_FUNCTION_NAME \
        --timeout 300 \
        --memory-size 1024 \
        --environment Variables="{BEDROCK_KB_ID=$BEDROCK_KB_ID,BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID,S3_BUCKET=$S3_BUCKET,DATA_SOURCE_ID=$DATA_SOURCE_ID,VISION_AGENT_API_KEY=$VISION_AGENT_API_KEY}" \
        --region $AWS_REGION
else
    echo "Creating new Lambda function..."
    
    # Create execution role if it doesn't exist
    ROLE_NAME="budget-agent-lambda-role"
    
    if ! aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
        echo "Creating IAM role..."
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document '{
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }'
        
        # Attach policies
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
        
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
        
        echo "Waiting for IAM role to be available..."
        sleep 10
    fi
    
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
    
    aws lambda create-function \
        --function-name $LAMBDA_FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG \
        --role $ROLE_ARN \
        --timeout 300 \
        --memory-size 1024 \
        --environment Variables="{BEDROCK_KB_ID=$BEDROCK_KB_ID,BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID,S3_BUCKET=$S3_BUCKET,DATA_SOURCE_ID=$DATA_SOURCE_ID,VISION_AGENT_API_KEY=$VISION_AGENT_API_KEY}" \
        --region $AWS_REGION
fi

# Step 6: Create or update API Gateway
echo ""
echo "Step 6: Setting up API Gateway..."

# Check if API exists
API_ID=$(aws apigatewayv2 get-apis --region $AWS_REGION --query "Items[?Name=='$API_NAME'].ApiId" --output text)

if [ -z "$API_ID" ]; then
    echo "Creating new API Gateway..."
    API_ID=$(aws apigatewayv2 create-api \
        --name $API_NAME \
        --protocol-type HTTP \
        --target arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:$LAMBDA_FUNCTION_NAME \
        --region $AWS_REGION \
        --query 'ApiId' --output text)
    
    echo "API created with ID: $API_ID"
else
    echo "API already exists with ID: $API_ID"
fi

# Configure CORS for the API
echo "Configuring CORS..."
aws apigatewayv2 update-api \
    --api-id $API_ID \
    --cors-configuration AllowOrigins="*",AllowMethods="GET,POST,OPTIONS",AllowHeaders="Content-Type,Authorization" \
    --region $AWS_REGION

# Add Lambda permission for API Gateway
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION_NAME \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$AWS_REGION:$AWS_ACCOUNT_ID:$API_ID/*/*" \
    --region $AWS_REGION 2>/dev/null || echo "Permission already exists"

# Get API endpoint
API_ENDPOINT=$(aws apigatewayv2 get-apis --region $AWS_REGION --query "Items[?Name=='$API_NAME'].ApiEndpoint" --output text)

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo "API Endpoint: $API_ENDPOINT"
echo ""
echo "Test with:"
echo "curl -X POST $API_ENDPOINT \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"What is the carbon tax?\"}'"
echo "======================================"
