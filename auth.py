        # Store authorization code with PKCE challenge
        self.authorization_codes[auth_code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "created_at": time.time(),
            "expires_at": time.time() + self.config.oauth_code_expiry,
            "used": False
        }
        
        # Build redirect URL
        redirect_url = f"{redirect_uri}?code={auth_code}"
        if state:
            redirect_url += f"&state={state}"
        
        logger.info(f"Authorization code created for client {client_id}")
        return auth_code, redirect_url
    
    async def exchange_code_for_token(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Exchange authorization code for access token with PKCE verification"""
        
        grant_type = form_data.get("grant_type")
        code = form_data.get("code")
        client_id = form_data.get("client_id")
        redirect_uri = form_data.get("redirect_uri")
        code_verifier = form_data.get("code_verifier")
        
        if grant_type != "authorization_code":
            raise ValueError("Unsupported grant_type")
        
        if not all([code, client_id, redirect_uri, code_verifier]):
            raise ValueError("Missing required parameters")
        
        # Validate authorization code
        code_data = self.authorization_codes.get(code)
        if not code_data:
            raise ValueError("Invalid authorization code")
        
        # Check if code is expired
        if time.time() > code_data["expires_at"]:
            del self.authorization_codes[code]
            raise ValueError("Authorization code expired")
        
        # Check if code was already used
        if code_data["used"]:
            del self.authorization_codes[code]
            raise ValueError("Authorization code already used")
        
        # Validate client and redirect URI
        if (code_data["client_id"] != client_id or 
            code_data["redirect_uri"] != redirect_uri):
            raise ValueError("Invalid client or redirect_uri")
        
        # Verify PKCE challenge using constant-time comparison
        if not self._verify_pkce(code_verifier, code_data["code_challenge"]):
            raise ValueError("Invalid code_verifier")
        
        # Mark code as used
        code_data["used"] = True
        
        # Generate tokens
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        # Store access token
        token_expires_at = time.time() + self.config.oauth_token_expiry
        self.access_tokens[access_token] = {
            "client_id": client_id,
            "scope": code_data["scope"],
            "created_at": time.time(),
            "expires_at": token_expires_at,
            "token_type": "Bearer"
        }
        
        # Store refresh token
        self.refresh_tokens[refresh_token] = {
            "client_id": client_id,
            "scope": code_data["scope"],
            "created_at": time.time(),
            "expires_at": time.time() + self.config.oauth_refresh_token_expiry,
            "access_token": access_token
        }
        
        # Clean up authorization code
        del self.authorization_codes[code]
        
        logger.info(f"Access token issued for client {client_id}")
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.config.oauth_token_expiry,
            "refresh_token": refresh_token,
            "scope": code_data["scope"]
        }
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify an access token and return token data"""
        token_data = self.access_tokens.get(token)
        
        if not token_data:
            return None
        
        # Check expiration
        if time.time() > token_data["expires_at"]:
            del self.access_tokens[token]
            return None
        
        return token_data
    
    async def introspect_token(self, token: str) -> Dict[str, Any]:
        """OAuth 2.0 Token Introspection (RFC 7662)"""
        token_data = await self.verify_token(token)
        
        if not token_data:
            return {"active": False}
        
        return {
            "active": True,
            "client_id": token_data["client_id"],
            "scope": token_data["scope"],
            "token_type": token_data["token_type"],
            "exp": int(token_data["expires_at"]),
            "iat": int(token_data["created_at"])
        }
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke an access or refresh token"""
        # Try access token first
        if token in self.access_tokens:
            del self.access_tokens[token]
            logger.info(f"Access token revoked: {token[:8]}...")
            return True
        
        # Try refresh token
        if token in self.refresh_tokens:
            refresh_data = self.refresh_tokens[token]
            access_token = refresh_data.get("access_token")
            
            # Remove both refresh and associated access token
            del self.refresh_tokens[token]
            if access_token and access_token in self.access_tokens:
                del self.access_tokens[access_token]
            
            logger.info(f"Refresh token revoked: {token[:8]}...")
            return True
        
        return False
    
    def check_rate_limit(self, key: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Check if a request is within rate limits"""
        if not self.config.rate_limit_enabled:
            return True
        
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old entries
        if key in self.rate_limits:
            self.rate_limits[key] = [
                timestamp for timestamp in self.rate_limits[key] 
                if timestamp > window_start
            ]
        else:
            self.rate_limits[key] = []
        
        # Check limit
        if len(self.rate_limits[key]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limits[key].append(now)
        return True
    
    def _verify_pkce(self, code_verifier: str, code_challenge: str) -> bool:
        """Verify PKCE code challenge using constant-time comparison"""
        try:
            # Compute code challenge from verifier
            challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip('=')
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(challenge, code_challenge)
        except Exception:
            return False
    
    def _is_valid_redirect_uri(self, uri: str) -> bool:
        """Validate redirect URI according to OAuth 2.1 security requirements"""
        if not uri:
            return False
        
        # HTTPS required except for localhost
        if uri.startswith("https://"):
            return True
        
        # Allow localhost for development
        if uri.startswith("http://localhost") or uri.startswith("http://127.0.0.1"):
            return True
        
        # Custom schemes are allowed for native apps
        if "://" in uri and not uri.startswith("http://"):
            return True
        
        return False
    
    async def cleanup_expired_tokens(self):
        """Background task to clean up expired tokens and codes"""
        while True:
            try:
                now = time.time()
                
                # Clean expired authorization codes
                expired_codes = [
                    code for code, data in self.authorization_codes.items()
                    if now > data["expires_at"]
                ]
                for code in expired_codes:
                    del self.authorization_codes[code]
                
                # Clean expired access tokens
                expired_tokens = [
                    token for token, data in self.access_tokens.items()
                    if now > data["expires_at"]
                ]
                for token in expired_tokens:
                    del self.access_tokens[token]
                
                # Clean expired refresh tokens
                expired_refresh = [
                    token for token, data in self.refresh_tokens.items()
                    if now > data["expires_at"]
                ]
                for token in expired_refresh:
                    del self.refresh_tokens[token]
                
                # Clean old rate limit entries
                for key in list(self.rate_limits.keys()):
                    self.rate_limits[key] = [
                        timestamp for timestamp in self.rate_limits[key]
                        if timestamp > now - 3600  # Keep last hour
                    ]
                    if not self.rate_limits[key]:
                        del self.rate_limits[key]
                
                if expired_codes or expired_tokens or expired_refresh:
                    logger.info(f"Cleaned up {len(expired_codes)} codes, {len(expired_tokens)} tokens, {len(expired_refresh)} refresh tokens")
                
                # Sleep for cleanup interval
                await asyncio.sleep(self.config.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
