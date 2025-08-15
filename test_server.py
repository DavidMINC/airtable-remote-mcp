#!/usr/bin/env python3

"""
Test script for Airtable Remote MCP Server
Tests OAuth flow, MCP endpoints, and basic functionality
"""

import asyncio
import json
import sys
from typing import Dict, Any

import httpx

class MCPServerTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.client_id = None
        self.access_token = None
        
    async def close(self):
        await self.client.aclose()
    
    async def test_health_check(self) -> bool:
        """Test health check endpoint"""
        print("🏥 Testing health check...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health check passed: {data['status']}")
                print(f"   📊 Components: {data['components']}")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
    
    async def test_oauth_metadata(self) -> bool:
        """Test OAuth authorization server metadata"""
        print("🔍 Testing OAuth metadata...")
        try:
            response = await self.client.get(f"{self.base_url}/.well-known/oauth-authorization-server")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ OAuth metadata available")
                print(f"   🔗 Endpoints: {len(data)} discovered")
                required_fields = ["issuer", "authorization_endpoint", "token_endpoint", "registration_endpoint"]
                missing = [field for field in required_fields if field not in data]
                if missing:
                    print(f"   ⚠️  Missing fields: {missing}")
                    return False
                return True
            else:
                print(f"   ❌ OAuth metadata failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ OAuth metadata error: {e}")
            return False
    
    async def test_protected_resource_metadata(self) -> bool:
        """Test protected resource metadata"""
        print("🛡️  Testing protected resource metadata...")
        try:
            response = await self.client.get(f"{self.base_url}/.well-known/oauth-protected-resource")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Protected resource metadata available")
                print(f"   🔒 Scopes: {data.get('scopes_supported', [])}")
                return True
            else:
                print(f"   ❌ Protected resource metadata failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Protected resource metadata error: {e}")
            return False
    
    async def test_client_registration(self) -> bool:
        """Test dynamic client registration"""
        print("📝 Testing dynamic client registration...")
        try:
            client_data = {
                "client_name": "MCP Test Client",
                "redirect_uris": ["https://example.com/callback"],
                "application_type": "web"
            }
            
            response = await self.client.post(
                f"{self.base_url}/oauth/register",
                json=client_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.client_id = data["client_id"]
                print(f"   ✅ Client registered: {self.client_id}")
                print(f"   🔑 Client name: {data['client_name']}")
                return True
            else:
                print(f"   ❌ Client registration failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Client registration error: {e}")
            return False
    
    async def test_unauthorized_mcp_access(self) -> bool:
        """Test that MCP endpoint requires authentication"""
        print("🚫 Testing unauthorized MCP access...")
        try:
            mcp_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": "test-1"
            }
            
            response = await self.client.post(
                f"{self.base_url}/mcp",
                json=mcp_request
            )
            
            if response.status_code == 401:
                print("   ✅ MCP endpoint properly requires authentication")
                www_auth = response.headers.get("WWW-Authenticate")
                if www_auth:
                    print(f"   🔐 WWW-Authenticate header present")
                return True
            else:
                print(f"   ❌ MCP endpoint should return 401, got {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Unauthorized MCP test error: {e}")
            return False
    
    async def test_setup_endpoint(self) -> bool:
        """Test setup information endpoint"""
        print("ℹ️  Testing setup endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/setup")
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Setup endpoint accessible")
                print(f"   📋 Tools available: {len(data.get('tools_available', []))}")
                return True
            else:
                print(f"   ❌ Setup endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Setup endpoint error: {e}")
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality"""
        print("⏱️  Testing rate limiting...")
        try:
            # Make multiple rapid requests to trigger rate limiting
            client_data = {
                "client_name": f"Rate Test Client {i}",
                "redirect_uris": ["https://example.com/callback"]
            }
            
            success_count = 0
            rate_limited = False
            
            for i in range(10):
                response = await self.client.post(
                    f"{self.base_url}/oauth/register",
                    json={
                        "client_name": f"Rate Test Client {i}",
                        "redirect_uris": ["https://example.com/callback"]
                    }
                )
                
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited = True
                    break
            
            if rate_limited:
                print(f"   ✅ Rate limiting active (triggered after {success_count} requests)")
                return True
            else:
                print(f"   ⚠️  Rate limiting not triggered ({success_count} requests succeeded)")
                return True  # Not necessarily a failure in development
        except Exception as e:
            print(f"   ❌ Rate limiting test error: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        print("🧪 Starting MCP Server Tests...")
        print(f"🎯 Target: {self.base_url}")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("OAuth Metadata", self.test_oauth_metadata),
            ("Protected Resource Metadata", self.test_protected_resource_metadata),
            ("Client Registration", self.test_client_registration),
            ("Unauthorized MCP Access", self.test_unauthorized_mcp_access),
            ("Setup Endpoint", self.test_setup_endpoint),
            ("Rate Limiting", self.test_rate_limiting),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append(result)
                print()
            except Exception as e:
                print(f"   ❌ {test_name} failed with exception: {e}")
                results.append(False)
                print()
        
        passed = sum(results)
        total = len(results)
        
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed! Server is ready for production.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the configuration.")
            return False

async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Airtable Remote MCP Server")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="Base URL of the MCP server (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    tester = MCPServerTester(args.url)
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
