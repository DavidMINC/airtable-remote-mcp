# Changelog

All notable changes to the Airtable Remote MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-XX

### 🚀 **Major Release - Complete Rewrite**

This version represents a complete rewrite and redesign of the Airtable Remote MCP Server to address all security vulnerabilities, implement proper MCP protocol support, and provide production-ready functionality.

### ✨ **Added**

#### **MCP Protocol Implementation**
- **Full MCP 2025-03-26 specification compliance** with Streamable HTTP transport
- **Proper JSON-RPC 2.0 message handling** with batch support
- **MCP initialization handshake** with capability negotiation
- **Session management** with unique session IDs and state tracking
- **Server-Sent Events (SSE) streaming** for real-time communication
- **Backward compatibility** with deprecated SSE transport (with warnings)

#### **Security & Authentication**
- **OAuth 2.1 implementation** with mandatory PKCE for all flows
- **Dynamic Client Registration (RFC 7591)** for automatic client onboarding
- **Authorization Server Metadata (RFC 8414)** for endpoint discovery
- **Protected Resource Metadata (RFC 9728)** for resource discovery
- **Token Introspection (RFC 7662)** and **Token Revocation (RFC 7009)**
- **Constant-time PKCE verification** to prevent timing attacks
- **Comprehensive rate limiting** for all OAuth endpoints
- **Secure token generation** with proper entropy and expiration
- **Input validation and sanitization** for all endpoints

#### **Production Features**
- **Comprehensive error handling** with structured responses
- **Health check endpoint** with detailed component status
- **Environment-based configuration** (development/production)
- **Structured logging** with configurable levels
- **Security headers** and HTTPS enforcement in production
- **Docker containerization** with security best practices
- **Automated deployment scripts** for multiple platforms

#### **Enhanced Airtable Integration**
- **Complete Airtable API coverage** with all CRUD operations
- **Batch operations** for creating, updating, and deleting records
- **Advanced filtering and sorting** with formula support
- **Field management** (create, update, delete fields)
- **Table management** (create, update tables)
- **Comprehensive error handling** with retry logic
- **Rate limit handling** and proper HTTP status code responses

#### **Developer Experience**
- **Development utility script** (`dev.py`) for easy local development
- **Test suite** (`test_server.py`) for comprehensive functionality testing
- **Multiple environment configurations** (.env.development, .env.example)
- **Docker Compose** setup for local development
- **Makefile** with convenient commands
- **Comprehensive documentation** with setup guides and troubleshooting

### 🔒 **Security Fixes**

#### **Critical Vulnerabilities Fixed**
- **In-memory storage vulnerabilities** - Added proper token expiration and cleanup
- **PKCE timing attacks** - Implemented constant-time comparison
- **Token security issues** - Proper token generation, validation, and lifecycle
- **Authorization code vulnerabilities** - Single-use codes with proper expiration
- **Client registration security** - Validation and rate limiting

#### **Security Enhancements**
- **Non-root container execution** with dedicated user
- **Secure headers** (HSTS, CSP, X-Frame-Options, etc.)
- **CORS policy** with configurable origins
- **Request size limits** and timeout handling
- **Environment-based secrets management**

### 🛠 **Changed**

#### **Breaking Changes from v1.x**
- **Transport Protocol**: Changed from basic SSE to MCP Streamable HTTP
- **Authentication**: Complete OAuth 2.1 implementation replacing simple API key
- **API Endpoints**: New endpoint structure with proper REST conventions
- **Configuration**: New environment variable structure
- **Error Responses**: Structured error responses with proper HTTP status codes

#### **API Changes**
- **Main MCP endpoint**: Now `/mcp` instead of separate `/sse` and `/messages`
- **OAuth endpoints**: Complete set of OAuth 2.1 endpoints
- **Health check**: Enhanced with component status and environment info
- **Setup endpoint**: Comprehensive setup and testing information

### 🐛 **Fixed**

#### **Functional Issues**
- **Missing MCP transport implementation** - Now fully implements Streamable HTTP
- **Improper OAuth flow** - Complete OAuth 2.1 implementation with all required endpoints
- **Error handling** - Comprehensive error handling with proper status codes
- **Session management** - Proper session lifecycle with cleanup
- **Rate limiting** - Configurable rate limiting for all endpoints

#### **Protocol Compliance**
- **MCP protocol headers** - Proper MCP-Protocol-Version and Mcp-Session-Id headers
- **JSON-RPC compliance** - Proper JSON-RPC 2.0 message format and error codes
- **OAuth 2.1 compliance** - Full compliance with OAuth 2.1 and related RFCs
- **HTTP standards** - Proper HTTP status codes and headers

### 📦 **Dependencies**

#### **Updated**
- **FastAPI** to 0.104.1 (latest stable)
- **Uvicorn** to 0.24.0 with standard extras
- **httpx** to 0.25.2 for improved HTTP client
- **Pydantic** to 2.5.0 for better data validation

#### **Added**
- **python-jose** for JWT handling (future extension)
- **passlib** for password hashing (future extension)
- **email-validator** for email validation
- **python-multipart** for form data handling

### 🚀 **Deployment**

#### **Railway Deployment**
- **Optimized railway.toml** configuration
- **Environment variable templates** for easy setup
- **Health check configuration** with proper timeouts
- **Automated deployment** with GitHub integration

#### **Docker Improvements**
- **Multi-stage Docker build** for smaller images
- **Security best practices** (non-root user, minimal base image)
- **Health checks** built into container
- **Development and production** configurations

### 📚 **Documentation**

#### **Enhanced Documentation**
- **Complete README** with setup guides and troubleshooting
- **API documentation** with endpoint descriptions and examples
- **Security documentation** with best practices
- **Deployment guides** for multiple platforms
- **Developer documentation** with contribution guidelines

#### **Configuration Documentation**
- **Environment variable reference** with descriptions
- **OAuth flow documentation** with examples
- **MCP protocol documentation** with message formats
- **Troubleshooting guide** with common issues and solutions

### 🧪 **Testing**

#### **Test Suite**
- **Comprehensive test script** covering all endpoints
- **OAuth flow testing** with complete authorization flow
- **MCP protocol testing** with proper message validation
- **Rate limiting testing** to verify security measures
- **Health check validation** for deployment verification

### 🔧 **Development Tools**

#### **Developer Utilities**
- **Development script** (`dev.py`) with commands for common tasks
- **Makefile** with convenient development commands
- **Environment templates** for different deployment scenarios
- **Docker Compose** setup for local development
- **Test automation** for continuous integration

---

## [1.0.0] - 2024-XX-XX (Previous Version)

### ⚠️ **Deprecated - Security Issues**

The previous version had significant security vulnerabilities and incomplete MCP protocol implementation:

#### **Known Issues (Fixed in v2.0.0)**
- In-memory storage without persistence
- Missing MCP transport implementation
- Incomplete OAuth implementation
- Security vulnerabilities in PKCE implementation
- Missing rate limiting
- No proper error handling
- Basic API key authentication only

---

## Migration Guide from v1.x to v2.0.0

### **Required Changes**

1. **Update Environment Variables**
   ```bash
   # Old format
   AIRTABLE_API_KEY=your_key
   
   # New format (see .env.example)
   AIRTABLE_API_KEY=your_key
   SECRET_KEY=your_secure_secret
   BASE_URL=https://your-domain.com
   ```

2. **Update Claude Configuration**
   - Change endpoint from `/sse` to `/mcp`
   - Remove any hardcoded client IDs (use Dynamic Client Registration)
   - Update connector URL to point to new deployment

3. **Test OAuth Flow**
   ```bash
   # Test the new OAuth endpoints
   python test_server.py --url https://your-deployment-url.com
   ```

### **Compatibility**

- **Backward Compatibility**: Limited - the `/sse` endpoint exists but returns deprecation warnings
- **Claude Compatibility**: Full compatibility with Claude's MCP connector requirements
- **API Compatibility**: New API structure - clients must be updated

---

## Future Roadmap

### **v2.1.0 (Planned)**
- Redis backend for token storage
- Database persistence for client registry
- Advanced monitoring and metrics
- Webhook support for real-time notifications

### **v2.2.0 (Planned)**
- Multi-tenant support
- Advanced RBAC (Role-Based Access Control)
- Audit logging
- Performance optimizations

### **v3.0.0 (Future)**
- Support for latest MCP specification updates
- Additional transport mechanisms
- Enterprise features
- Advanced analytics and reporting
