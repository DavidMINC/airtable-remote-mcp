@echo off
REM Production deployment script for Airtable Remote MCP Server (Windows)

echo 🚀 Deploying Airtable Remote MCP Server v2.0.0...

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from example...
    if exist .env.example (
        copy .env.example .env
        echo 📝 Please edit .env file with your actual values before continuing
        pause
        exit /b 1
    ) else (
        echo ❌ No .env.example file found
        pause
        exit /b 1
    )
)

REM Check if Docker is available
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker is not installed or not in PATH
    pause
    exit /b 1
)

REM Build Docker image
echo 🐳 Building Docker image...
docker build -t airtable-remote-mcp:latest .
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker build failed
    pause
    exit /b 1
)

echo ✅ Docker build successful!

REM Start the container
echo 🚀 Starting container...
docker run -d --name airtable-remote-mcp --env-file .env -p 8000:8000 --restart unless-stopped airtable-remote-mcp:latest
if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to start container
    pause
    exit /b 1
)

REM Wait for health check
echo ⏳ Waiting for service to be ready...
timeout /t 5 /nobreak >nul

REM Check if service is running
curl -f http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ✅ Service is healthy!
) else (
    echo ⚠️  Service may still be starting up...
    echo Check logs with: docker logs airtable-remote-mcp
)

echo.
echo 🎉 Deployment completed!
echo 📋 Service Information:
echo    • Container: airtable-remote-mcp
echo    • Port: 8000
echo    • Health Check: http://localhost:8000/health
echo    • Setup Info: http://localhost:8000/setup
echo    • API Docs: http://localhost:8000/docs
echo.
echo 🔧 Next Steps:
echo    1. Test OAuth registration endpoint
echo    2. Configure Claude with your server URL
echo    3. Monitor logs: docker logs -f airtable-remote-mcp
echo.
echo 📚 For Railway deployment:
echo    1. Push this code to GitHub
echo    2. Connect Railway to your repository
echo    3. Set environment variables in Railway dashboard
echo    4. Deploy automatically

pause
