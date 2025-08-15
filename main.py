#!/usr/bin/env python3

import asyncio
import json
import logging
import os
import secrets
import uuid
import hashlib
import base64
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import time

import httpx
from fastapi import FastAPI, HTTPException, Request, Depends, Header, Response
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from auth import AuthManager
from mcp_transport import MCPTransport
from airtable_client import AirtableClient, AirtableConfig
from config import Config
from models import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize configuration
config = Config()

# Initialize components
auth_manager = AuthManager(config)
airtable_client = AirtableClient(AirtableConfig())
mcp_transport = MCPTransport(auth_manager, airtable_client)

# Create main FastAPI app
app = FastAPI(
    title="Airtable Remote MCP Server",
    description="Production-ready MCP Server for Airtable with OAuth 2.1 and Streamable HTTP",
    version="2.0.0",
    docs_url="/docs" if config.environment == "development" else None,
    redoc_url="/redoc" if config.environment == "development" else None
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # HTTPS enforcement in production
    if config.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id", "WWW-Authenticate"]
)

# Health and discovery endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    try:
        # Check Airtable connectivity if API key is configured
        airtable_status = "configured" if airtable_client.config.api_key != "placeholder" else "not_configured"
        
        return {
            "status": "healthy",
            "service": "airtable-remote-mcp-server",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "airtable": airtable_status,
                "auth": "ready",
                "mcp_transport": "ready"
            },
            "environment": config.environment
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/")
async def root():
    """Root endpoint with server information and setup instructions"""
    return {
        "name": "airtable-remote-mcp-server",
        "version": "2.0.0",
        "description": "Production-ready MCP Server for Airtable with OAuth 2.1 and Streamable HTTP",
        "specification": "MCP 2025-03-26",
        "transport": "Streamable HTTP (with SSE fallback)",
        "authentication": "OAuth 2.1 with Dynamic Client Registration",
        "endpoints": {
            "mcp": f"{config.base_url}/mcp",
            "oauth_metadata": f"{config.base_url}/.well-known/oauth-authorization-server",
            "protected_resource_metadata": f"{config.base_url}/.well-known/oauth-protected-resource",
            "registration": f"{config.base_url}/oauth/register",
            "authorization": f"{config.base_url}/oauth/authorize",
            "token": f"{config.base_url}/oauth/token"
        },
        "setup_instructions": {
            "claude_web": {
                "step1": "Go to Settings → Connectors in Claude",
                "step2": f"Add custom connector with URL: {config.base_url}",
                "step3": "Leave OAuth Client ID empty (Dynamic Client Registration is used)",
                "step4": "Claude will automatically register and authenticate"
            },
            "test_with_curl": f"curl -X POST {config.base_url}/oauth/register -H 'Content-Type: application/json' -d '{{\"client_name\": \"Test Client\", \"redirect_uris\": [\"https://example.com/callback\"]}}'"
        }
    }

# OAuth 2.1 Authorization Server Metadata (RFC 8414)
@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server_metadata():
    """OAuth 2.1 Authorization Server Metadata for Dynamic Client Registration"""
    return {
        "issuer": config.base_url,
        "authorization_endpoint": f"{config.base_url}/oauth/authorize",
        "token_endpoint": f"{config.base_url}/oauth/token",
        "registration_endpoint": f"{config.base_url}/oauth/register",
        "scopes_supported": ["mcp:read", "mcp:write", "mcp:admin"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "subject_types_supported": ["public"],
        "registration_endpoint_auth_methods_supported": ["none"],
        "ui_locales_supported": ["en-US"],
        "service_documentation": "https://docs.airtable.com/api/introduction",
        "op_policy_uri": f"{config.base_url}/privacy",
        "op_tos_uri": f"{config.base_url}/terms"
    }

# OAuth 2.0 Protected Resource Metadata (RFC 9728)
@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource_metadata():
    """OAuth 2.0 Protected Resource Metadata"""
    return {
        "resource": config.base_url,
        "authorization_servers": [config.base_url],
        "scopes_supported": ["mcp:read", "mcp:write", "mcp:admin"],
        "bearer_methods_supported": ["header"],
        "resource_documentation": "https://docs.airtable.com/api/introduction",
        "revocation_endpoint": f"{config.base_url}/oauth/revoke",
        "revocation_endpoint_auth_methods_supported": ["none"],
        "introspection_endpoint": f"{config.base_url}/oauth/introspect",
        "introspection_endpoint_auth_methods_supported": ["none"]
    }

# Dynamic Client Registration (RFC 7591)
@app.post("/oauth/register")
async def dynamic_client_registration(request: Request):
    """Dynamic Client Registration endpoint - Required by Claude MCP"""
    try:
        client_metadata = await request.json()
        
        # Validate required fields
        if not client_metadata.get("client_name"):
            raise HTTPException(status_code=400, detail="client_name is required")
        
        redirect_uris = client_metadata.get("redirect_uris", [])
        if not redirect_uris:
            raise HTTPException(status_code=400, detail="redirect_uris is required")
        
        # Validate redirect URIs
        for uri in redirect_uris:
            if not (uri.startswith("https://") or uri.startswith("http://localhost") or uri.startswith("http://127.0.0.1")):
                raise HTTPException(status_code=400, detail=f"Invalid redirect_uri: {uri}")
        
        # Rate limiting check
        client_ip = request.client.host
        if not auth_manager.check_rate_limit(f"register:{client_ip}", max_requests=5, window_seconds=300):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Register client
        client_response = await auth_manager.register_client(client_metadata)
        
        logger.info(f"Registered new client: {client_response['client_id']} from {client_ip}")
        
        return client_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Client registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

# OAuth Authorization endpoint
@app.get("/oauth/authorize")
async def oauth_authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: str = "mcp:read mcp:write",
    state: str = None,
    code_challenge: str = None,
    code_challenge_method: str = "S256"
):
    """OAuth 2.1 Authorization endpoint with PKCE"""
    try:
        # Rate limiting
        if not auth_manager.check_rate_limit(f"authorize:{client_id}", max_requests=10, window_seconds=300):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Validate and create authorization
        auth_code, redirect_url = await auth_manager.create_authorization(
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        logger.info(f"Authorization granted for client {client_id}")
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=500, detail="Authorization failed")

# OAuth Token endpoint
@app.post("/oauth/token")
async def oauth_token(request: Request):
    """OAuth 2.1 Token endpoint with PKCE verification"""
    try:
        form_data = await request.form()
        
        # Rate limiting
        client_id = form_data.get("client_id")
        if client_id and not auth_manager.check_rate_limit(f"token:{client_id}", max_requests=20, window_seconds=300):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Exchange authorization code for token
        token_response = await auth_manager.exchange_code_for_token(dict(form_data))
        
        logger.info(f"Access token issued for client {client_id}")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise HTTPException(status_code=500, detail="Token exchange failed")

# Token introspection endpoint
@app.post("/oauth/introspect")
async def token_introspection(request: Request):
    """OAuth 2.0 Token Introspection (RFC 7662)"""
    try:
        form_data = await request.form()
        token = form_data.get("token")
        
        if not token:
            raise HTTPException(status_code=400, detail="token parameter required")
        
        introspection_result = await auth_manager.introspect_token(token)
        return introspection_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token introspection error: {e}")
        return {"active": False}

# Token revocation endpoint
@app.post("/oauth/revoke")
async def token_revocation(request: Request):
    """OAuth 2.0 Token Revocation (RFC 7009)"""
    try:
        form_data = await request.form()
        token = form_data.get("token")
        
        if not token:
            raise HTTPException(status_code=400, detail="token parameter required")
        
        await auth_manager.revoke_token(token)
        return {"revoked": True}
        
    except Exception as e:
        logger.error(f"Token revocation error: {e}")
        return {"revoked": False}

# MCP Streamable HTTP Transport endpoint
@app.api_route("/mcp", methods=["GET", "POST"])
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint implementing Streamable HTTP transport
    Handles both POST requests for JSON-RPC and GET requests for SSE streams
    """
    try:
        # Handle authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "Authentication required"},
                headers={
                    "WWW-Authenticate": f'Bearer realm="airtable-mcp", resource_metadata="{config.base_url}/.well-known/oauth-protected-resource"'
                }
            )
        
        token = auth_header.split(" ")[1]
        token_data = await auth_manager.verify_token(token)
        
        if not token_data:
            return JSONResponse(
                status_code=401,
                content={"error": "invalid_token", "message": "Invalid or expired token"},
                headers={
                    "WWW-Authenticate": f'Bearer realm="airtable-mcp", error="invalid_token"'
                }
            )
        
        # Handle MCP protocol
        if request.method == "POST":
            return await mcp_transport.handle_post_request(request, token_data)
        else:  # GET request for SSE
            return await mcp_transport.handle_get_request(request, token_data)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Backward compatibility with old SSE transport
@app.get("/sse")
async def sse_compatibility_endpoint():
    """Backward compatibility endpoint for old SSE transport"""
    logger.warning("Deprecated SSE endpoint accessed - client should use /mcp with Streamable HTTP")
    
    # Return endpoint event pointing to new transport
    def generate_sse():
        yield f"event: endpoint\n"
        yield f"data: {config.base_url}/mcp\n\n"
        yield f"event: deprecated\n"
        yield f"data: This endpoint is deprecated. Please use Streamable HTTP transport at /mcp\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "X-Deprecated": "true"
        }
    )

# Setup and testing endpoints
@app.get("/setup")
async def setup_info():
    """Setup information for testing and integration"""
    return {
        "service": "Airtable Remote MCP Server",
        "version": "2.0.0",
        "specification": "MCP 2025-03-26 with Streamable HTTP",
        "status": "production-ready",
        "for_claude": {
            "connector_url": config.base_url,
            "transport": "Streamable HTTP",
            "authentication": "OAuth 2.1 with Dynamic Client Registration",
            "oauth_client_id_field": "Leave empty - Dynamic Client Registration handles this automatically"
        },
        "endpoints": {
            "main_mcp": f"{config.base_url}/mcp",
            "oauth_metadata": f"{config.base_url}/.well-known/oauth-authorization-server",
            "resource_metadata": f"{config.base_url}/.well-known/oauth-protected-resource",
            "health": f"{config.base_url}/health"
        },
        "testing": {
            "register_client": f"curl -X POST {config.base_url}/oauth/register -H 'Content-Type: application/json' -d '{{\"client_name\": \"Test Client\", \"redirect_uris\": [\"https://example.com/callback\"]}}'",
            "check_health": f"curl {config.base_url}/health",
            "oauth_metadata": f"curl {config.base_url}/.well-known/oauth-authorization-server"
        },
        "tools_available": [
            "list_bases - List all accessible Airtable bases",
            "list_tables - List tables in a specific base",
            "describe_table - Get detailed table information",
            "list_records - List records from a table with filtering",
            "search_records - Search for records containing specific text",
            "get_record - Get a specific record by ID",
            "create_record - Create new records",
            "update_records - Update existing records",
            "delete_records - Delete records",
            "create_table - Create new tables",
            "update_table - Update table metadata",
            "create_field - Add new fields to tables",
            "update_field - Update field metadata"
        ]
    }

# Cleanup task for expired tokens and codes
@app.on_event("startup")
async def startup_event():
    """Initialize cleanup tasks and logging"""
    logger.info(f"Starting Airtable Remote MCP Server v2.0.0")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Base URL: {config.base_url}")
    logger.info(f"Airtable API configured: {'Yes' if airtable_client.config.api_key != 'placeholder' else 'No'}")
    
    # Start cleanup task
    asyncio.create_task(auth_manager.cleanup_expired_tokens())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Airtable Remote MCP Server")
    await airtable_client.close()

if __name__ == "__main__":
    port = config.port
    host = config.host
    
    print(f"🚀 Starting Airtable Remote MCP Server v2.0.0")
    print(f"📊 Environment: {config.environment}")
    print(f"🔑 Airtable API Key configured: {'Yes' if airtable_client.config.api_key != 'placeholder' else 'No'}")
    print(f"🌐 Base URL: {config.base_url}")
    print(f"🔧 OAuth 2.1 with Dynamic Client Registration enabled")
    print(f"🚦 Streamable HTTP transport with SSE support")
    print(f"📋 Setup info: {config.base_url}/setup")
    print(f"💚 Health check: {config.base_url}/health")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        reload=config.environment == "development",
        log_level="info",
        access_log=True
    )
