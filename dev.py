    if not missing_required and not missing_production:
        print("✅ Environment configuration looks good!")
        
        # Show current config
        print("\n📋 Current configuration:")
        print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"   Host: {os.getenv('HOST', '0.0.0.0')}")
        print(f"   Port: {os.getenv('PORT', '8000')}")
        print(f"   Base URL: {os.getenv('BASE_URL', 'http://localhost:8000')}")
        print(f"   Rate limiting: {os.getenv('RATE_LIMIT_ENABLED', 'true')}")
        
        # Check Airtable key format
        api_key = os.getenv('AIRTABLE_API_KEY', '')
        if api_key and not api_key.startswith('pat'):
            print("⚠️  Airtable API key should start with 'pat' (Personal Access Token)")
    
    return len(missing_required) == 0

def status():
    """Show server status"""
    print("📊 Server Status:")
    
    # Check if running locally
    try:
        import httpx
        import asyncio
        
        async def check_health():
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=5)
                return response.json()
        
        health = asyncio.run(check_health())
        print("✅ Local server is running")
        print(f"   Status: {health.get('status')}")
        print(f"   Version: {health.get('version')}")
        print(f"   Environment: {health.get('environment')}")
        
    except Exception as e:
        print("❌ Local server is not running")
    
    # Check Docker container
    try:
        result = run_command("docker ps --filter name=airtable-remote-mcp --format '{{.Status}}'", capture_output=True, check=False)
        if result:
            print(f"🐳 Docker container: {result}")
        else:
            print("🐳 Docker container: Not running")
    except:
        print("🐳 Docker container: Unknown (Docker not available)")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Development utility for Airtable Remote MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  setup       Set up development environment
  run         Run development server
  test        Run tests
  docker      Build and run with Docker
  stop        Stop Docker container
  logs        Show Docker logs
  clean       Clean up Docker resources
  deploy      Deploy to Railway
  secret      Generate secure secret key
  check       Check environment configuration
  status      Show server status

Examples:
  python dev.py setup        # Set up development environment
  python dev.py run          # Run development server
  python dev.py docker       # Build and run with Docker
  python dev.py test         # Run tests
  python dev.py deploy       # Deploy to Railway
        """
    )
    
    parser.add_argument(
        "command",
        choices=[
            "setup", "run", "test", "docker", "stop", "logs", 
            "clean", "deploy", "secret", "check", "status"
        ],
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    print("🛠️  Airtable Remote MCP Server - Development Utility")
    print("=" * 60)
    
    if args.command == "setup":
        success = setup_dev_environment()
        if success:
            print("\n🎉 Setup complete! Next steps:")
            print("   1. Edit .env file with your Airtable API key")
            print("   2. Run: python dev.py run")
            print("   3. Test: python dev.py test")
    
    elif args.command == "run":
        run_server()
    
    elif args.command == "test":
        run_tests()
    
    elif args.command == "docker":
        build_docker()
        run_docker()
    
    elif args.command == "stop":
        stop_docker()
    
    elif args.command == "logs":
        show_logs()
    
    elif args.command == "clean":
        clean()
    
    elif args.command == "deploy":
        deploy_railway()
    
    elif args.command == "secret":
        generate_secret_key()
    
    elif args.command == "check":
        check_env()
    
    elif args.command == "status":
        status()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
