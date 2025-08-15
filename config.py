import os
from typing import List
from datetime import timedelta

class Config:
    """Configuration management for the MCP server"""
    
    def __init__(self):
        # Server configuration
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", 8000))
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.base_url = os.getenv("BASE_URL", "https://airtable-mcp-server-production.railway.app")
        
        # Security configuration
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.allowed_origins = self._parse_allowed_origins()
        
        # Rate limiting configuration
        self.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", 3600))  # 1 hour
        
        # OAuth configuration
        self.oauth_code_expiry = int(os.getenv("OAUTH_CODE_EXPIRY", 60))  # 1 minute
        self.oauth_token_expiry = int(os.getenv("OAUTH_TOKEN_EXPIRY", 3600))  # 1 hour
        self.oauth_refresh_token_expiry = int(os.getenv("OAUTH_REFRESH_TOKEN_EXPIRY", 86400))  # 24 hours
        
        # Storage configuration
        self.redis_url = os.getenv("REDIS_URL")  # Optional Redis for production
        self.database_url = os.getenv("DATABASE_URL")  # Optional database for production
        
        # Cleanup configuration
        self.cleanup_interval = int(os.getenv("CLEANUP_INTERVAL", 300))  # 5 minutes
        
        # Airtable configuration
        self.airtable_api_key = os.getenv("AIRTABLE_API_KEY")
        self.airtable_base_url = os.getenv("AIRTABLE_BASE_URL", "https://api.airtable.com/v0")
        self.airtable_timeout = int(os.getenv("AIRTABLE_TIMEOUT", 30))
        
        # MCP configuration
        self.mcp_protocol_version = os.getenv("MCP_PROTOCOL_VERSION", "2025-03-26")
        self.mcp_server_name = os.getenv("MCP_SERVER_NAME", "airtable-remote-mcp")
        self.mcp_server_version = os.getenv("MCP_SERVER_VERSION", "2.0.0")
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # Development vs Production settings
        if self.environment == "development":
            self.oauth_code_expiry = 300  # 5 minutes for dev
            self.oauth_token_expiry = 7200  # 2 hours for dev
        
        self._validate_config()
    
    def _parse_allowed_origins(self) -> List[str]:
        """Parse allowed origins from environment variable"""
        origins_str = os.getenv("ALLOWED_ORIGINS", "*")
        if origins_str == "*":
            return ["*"]
        return [origin.strip() for origin in origins_str.split(",")]
    
    def _validate_config(self):
        """Validate configuration values"""
        if self.environment == "production":
            if self.secret_key == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            
            if not self.base_url.startswith("https://"):
                raise ValueError("BASE_URL must use HTTPS in production")
            
            if not self.airtable_api_key:
                print("⚠️  WARNING: AIRTABLE_API_KEY not set - some functionality will be limited")
        
        if self.oauth_code_expiry < 30 or self.oauth_code_expiry > 600:
            raise ValueError("OAUTH_CODE_EXPIRY must be between 30 and 600 seconds")
        
        if self.oauth_token_expiry < 300:  # 5 minutes minimum
            raise ValueError("OAUTH_TOKEN_EXPIRY must be at least 300 seconds")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"
    
    def get_oauth_code_expiry_delta(self) -> timedelta:
        """Get OAuth code expiry as timedelta"""
        return timedelta(seconds=self.oauth_code_expiry)
    
    def get_oauth_token_expiry_delta(self) -> timedelta:
        """Get OAuth token expiry as timedelta"""
        return timedelta(seconds=self.oauth_token_expiry)
    
    def get_oauth_refresh_token_expiry_delta(self) -> timedelta:
        """Get OAuth refresh token expiry as timedelta"""
        return timedelta(seconds=self.oauth_refresh_token_expiry)
