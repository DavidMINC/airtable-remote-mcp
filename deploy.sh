#!/bin/bash

# Production deployment script for Airtable Remote MCP Server

echo "🚀 Deploying Airtable Remote MCP Server v2.0.0..."

# Check if required environment variables are set
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ Error: $1 environment variable is not set"
        echo "   Please set it before deploying to production"
        exit 1
    fi
}

# Production environment checks
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔍 Checking production environment variables..."
    check_env_var "AIRTABLE_API_KEY"
    check_env_var "SECRET_KEY"
    check_env_var "BASE_URL"
    
    if [ "$SECRET_KEY" = "your-secret-key-change-in-production" ]; then
        echo "❌ Error: SECRET_KEY must be changed from default value in production"
        exit 1
    fi
    
    if [[ ! "$BASE_URL" =~ ^https:// ]]; then
        echo "❌ Error: BASE_URL must use HTTPS in production"
        exit 1
    fi
    
    echo "✅ Production environment checks passed"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Please edit .env file with your actual values before continuing"
        exit 1
    else
        echo "❌ No .env.example file found"
        exit 1
    fi
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t airtable-remote-mcp:latest . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Docker build successful!"

# Run tests if available
if [ -f "test_main.py" ]; then
    echo "🧪 Running tests..."
    docker run --rm --env-file .env airtable-remote-mcp:latest python -m pytest test_main.py -v || {
        echo "⚠️  Tests failed, but continuing deployment..."
    }
fi

# Start the container
echo "🚀 Starting container..."
docker run -d \
    --name airtable-remote-mcp \
    --env-file .env \
    -p 8000:8000 \
    --restart unless-stopped \
    airtable-remote-mcp:latest || {
    echo "❌ Failed to start container"
    exit 1
}

# Wait for health check
echo "⏳ Waiting for service to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✅ Service is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Service failed to start within 30 seconds"
        docker logs airtable-remote-mcp
        exit 1
    fi
    sleep 1
done

# Display deployment information
echo ""
echo "🎉 Deployment successful!"
echo "📋 Service Information:"
echo "   • Container: airtable-remote-mcp"
echo "   • Port: 8000"
echo "   • Health Check: http://localhost:8000/health"
echo "   • Setup Info: http://localhost:8000/setup"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 Next Steps:"
echo "   1. Test the OAuth flow: curl -X POST http://localhost:8000/oauth/register \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"client_name\": \"Test Client\", \"redirect_uris\": [\"https://example.com/callback\"]}'"
echo "   2. Configure Claude with your server URL"
echo "   3. Monitor logs: docker logs -f airtable-remote-mcp"
echo ""
echo "📚 For Railway deployment:"
echo "   1. Push this code to GitHub"
echo "   2. Connect Railway to your repository"
echo "   3. Set environment variables in Railway dashboard"
echo "   4. Deploy automatically"
