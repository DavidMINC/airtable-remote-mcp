### 1. **Prepare Your Repository**
```bash
git add .
git commit -m "Add production-ready MCP server v2.0.0"
git push origin main
```

### 2. **Deploy to Railway**
1. Connect Railway to your GitHub repository
2. **Set these environment variables in Railway dashboard:**
   ```
   AIRTABLE_API_KEY=your_airtable_api_key
   SECRET_KEY=your_secure_secret_key
   BASE_URL=https://your-app.railway.app
   ```
3. Railway will auto-deploy using the `railway.toml` configuration

### 3. **Configure Claude**
1. Go to **Settings → Connectors** in Claude
2. Add custom connector with your Railway URL
3. **Leave OAuth Client ID empty** - Dynamic Client Registration handles this automatically
4. Claude will automatically register and authenticate

## 🧪 **Local Development Setup**

### **Prerequisites**
- Python 3.11+
- Docker (optional)
- Airtable API key

### **Quick Start**
```bash
# Clone the repository
git clone https://github.com/your-username/airtable-remote-mcp.git
cd airtable-remote-mcp

# Set up environment
cp .env.development .env
# Edit .env with your Airtable API key

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

### **Docker Development**
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run with development profile
docker-compose --profile development up
```

## 📋 **Environment Variables**

### **Required**
```env
AIRTABLE_API_KEY=your_airtable_api_key
SECRET_KEY=your_secure_secret_key  # Production only
BASE_URL=https://your-domain.com   # Production only
```

### **Optional Configuration**
```env
# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# Security
ALLOWED_ORIGINS=https://claude.ai,https://api.anthropic.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# OAuth
OAUTH_CODE_EXPIRY=60
OAUTH_TOKEN_EXPIRY=3600
OAUTH_REFRESH_TOKEN_EXPIRY=86400

# Logging
LOG_LEVEL=INFO
```

## 🛠 **Available MCP Tools**

| Tool | Description | Scope Required |
|------|-------------|----------------|
| `list_bases` | List accessible Airtable bases | `mcp:read` |
| `list_tables` | List tables in a base | `mcp:read` |
| `describe_table` | Get detailed table information | `mcp:read` |
| `list_records` | List records with filtering/sorting | `mcp:read` |
| `search_records` | Search records by text | `mcp:read` |
| `get_record` | Get specific record by ID | `mcp:read` |
| `create_record` | Create new records | `mcp:write` |
| `update_records` | Update existing records | `mcp:write` |
| `delete_records` | Delete records | `mcp:write` |
| `create_table` | Create new tables | `mcp:write` |
| `update_table` | Update table metadata | `mcp:write` |
| `create_field` | Add fields to tables | `mcp:write` |
| `update_field` | Update field metadata | `mcp:write` |

## 🧪 **Testing Your Deployment**

### **Health Check**
```bash
curl https://your-app.railway.app/health
```

### **OAuth Metadata**
```bash
curl https://your-app.railway.app/.well-known/oauth-authorization-server
```

### **Dynamic Client Registration**
```bash
curl -X POST https://your-app.railway.app/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["https://example.com/callback"]
  }'
```

### **Setup Information**
```bash
curl https://your-app.railway.app/setup
```

## 🔍 **API Endpoints**

### **MCP Protocol**
- `POST/GET /mcp` - Main MCP endpoint (Streamable HTTP)
- `GET /sse` - Legacy SSE endpoint (deprecated)

### **OAuth 2.1 Endpoints**
- `GET /.well-known/oauth-authorization-server` - Authorization server metadata
- `GET /.well-known/oauth-protected-resource` - Protected resource metadata
- `POST /oauth/register` - Dynamic client registration
- `GET /oauth/authorize` - Authorization endpoint
- `POST /oauth/token` - Token endpoint
- `POST /oauth/introspect` - Token introspection
- `POST /oauth/revoke` - Token revocation

### **Utility Endpoints**
- `GET /health` - Health check with detailed status
- `GET /setup` - Setup instructions and testing info
- `GET /` - Server information and documentation

## 📊 **Monitoring & Observability**

### **Health Check Response**
```json
{
  "status": "healthy",
  "service": "airtable-remote-mcp-server",
  "version": "2.0.0",
  "components": {
    "airtable": "configured",
    "auth": "ready",
    "mcp_transport": "ready"
  },
  "environment": "production"
}
```

### **Logging**
- Structured JSON logging in production
- Configurable log levels
- Request/response logging
- OAuth event auditing
- Error tracking with context

### **Metrics**
- Request count and latency
- Error rates by endpoint
- OAuth flow success/failure rates
- Active session count
- Rate limit hit rates

## 🔒 **Security Features**

### **OAuth 2.1 Security**
- **Mandatory PKCE** for all authorization flows
- **Constant-time PKCE verification** to prevent timing attacks
- **Secure token generation** with cryptographically secure random
- **Token expiration and cleanup** with configurable lifetimes
- **Rate limiting** on all OAuth endpoints

### **Transport Security**
- **HTTPS enforcement** in production
- **Secure headers** (HSTS, CSP, etc.)
- **CORS configuration** with origin validation
- **Input validation** and sanitization
- **SQL injection prevention** (parameterized queries)

### **Application Security**
- **Non-root container execution**
- **Minimal container image** with security updates
- **Environment-based configuration**
- **Secrets management** best practices
- **Request size limits** and timeout handling

## 🚦 **Migration from v1.x**

If upgrading from the previous version:

### **Breaking Changes**
1. **Transport Protocol**: Now uses Streamable HTTP instead of basic SSE
2. **Authentication**: Proper OAuth 2.1 implementation with security fixes
3. **Environment Variables**: New configuration structure
4. **API Responses**: Structured error responses and proper HTTP status codes

### **Migration Steps**
1. **Update environment variables** using the new `.env.example`
2. **Update Claude connector** to use the new `/mcp` endpoint
3. **Test OAuth flow** with dynamic client registration
4. **Monitor logs** for any compatibility issues

## 🐛 **Troubleshooting**

### **Common Issues**

**Claude connector fails to add:**
```bash
# Check server accessibility
curl https://your-app.railway.app/health

# Verify OAuth metadata
curl https://your-app.railway.app/.well-known/oauth-authorization-server

# Test client registration
curl -X POST https://your-app.railway.app/oauth/register \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Test", "redirect_uris": ["https://example.com"]}'
```

**OAuth flow issues:**
1. Verify `BASE_URL` matches your actual deployment URL
2. Check Railway environment variables are set correctly
3. Review server logs for detailed error messages
4. Ensure HTTPS is properly configured

**Rate limiting errors:**
```bash
# Check current rate limits
curl -H "Authorization: Bearer your-token" \
  https://your-app.railway.app/oauth/introspect
```

**MCP transport errors:**
1. Verify MCP protocol version compatibility
2. Check request format (JSON-RPC 2.0)
3. Ensure proper authentication headers
4. Review session management

## 🔧 **Development**

### **Project Structure**
```
airtable-remote-mcp/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── auth.py                # OAuth 2.1 authentication manager
├── mcp_transport.py       # MCP Streamable HTTP transport
├── airtable_client.py     # Enhanced Airtable API client
├── models.py              # Pydantic data models
├── requirements.txt       # Python dependencies
├── Dockerfile            # Production container
├── docker-compose.yml    # Development environment
├── railway.toml          # Railway deployment config
├── deploy.sh/.bat        # Deployment scripts
└── README.md             # This file
```

### **Code Quality**
- **Type hints** throughout codebase
- **Pydantic models** for data validation
- **Comprehensive error handling**
- **Async/await** for I/O operations
- **Security best practices**

### **Testing**
```bash
# Run with pytest (if test files are added)
pytest tests/ -v

# Test with Docker
docker-compose run --rm airtable-mcp python -m pytest
```

## 📜 **Compliance & Standards**

- ✅ **MCP Specification 2025-03-26** - Full compliance
- ✅ **OAuth 2.1 (RFC 6749 bis)** - Complete implementation
- ✅ **RFC 7591** - Dynamic Client Registration
- ✅ **RFC 8414** - Authorization Server Metadata
- ✅ **RFC 9728** - Protected Resource Metadata
- ✅ **RFC 7636** - PKCE (Proof Key for Code Exchange)
- ✅ **RFC 7662** - Token Introspection
- ✅ **RFC 7009** - Token Revocation

## 🎯 **Production Deployment Checklist**

- [ ] Set `SECRET_KEY` to a secure random value
- [ ] Configure `AIRTABLE_API_KEY` with proper permissions
- [ ] Set `BASE_URL` to your actual HTTPS domain
- [ ] Enable rate limiting (`RATE_LIMIT_ENABLED=true`)
- [ ] Configure `ALLOWED_ORIGINS` for your use case
- [ ] Set up monitoring and logging
- [ ] Test OAuth flow end-to-end
- [ ] Verify MCP tools work with Claude
- [ ] Set up backup and recovery procedures
- [ ] Configure SSL/TLS properly
- [ ] Review security headers and CORS policy

## 🤝 **Contributing**

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### **Development Setup**
```bash
git clone https://github.com/your-username/airtable-remote-mcp.git
cd airtable-remote-mcp
pip install -r requirements.txt
cp .env.development .env
# Edit .env with your Airtable API key
python main.py
```

## 📄 **License**

MIT License - see LICENSE file for details.

## 🙏 **Acknowledgments**

- **Anthropic** for the MCP specification and Claude
- **Airtable** for their excellent API
- **FastAPI** for the amazing web framework
- **Python community** for the ecosystem

---

## 🆘 **Support**

For issues, questions, or contributions:

- **GitHub Issues**: [Report bugs or request features](https://github.com/your-username/airtable-remote-mcp/issues)
- **MCP Documentation**: [Model Context Protocol](https://modelcontextprotocol.io/)
- **Airtable API**: [Official Documentation](https://airtable.com/developers/web/api/introduction)

**Built with ❤️ for the MCP community**
