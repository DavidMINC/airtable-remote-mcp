from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

# OAuth Models
class ClientRegistrationRequest(BaseModel):
    """OAuth 2.1 Dynamic Client Registration Request"""
    client_name: str = Field(..., description="Human-readable client name")
    redirect_uris: List[str] = Field(..., description="Array of redirection URI strings")
    application_type: Optional[str] = Field("web", description="Native or web application")
    token_endpoint_auth_method: Optional[str] = Field("none", description="Authentication method")
    grant_types: Optional[List[str]] = Field(["authorization_code"], description="Grant types")
    response_types: Optional[List[str]] = Field(["code"], description="Response types")
    scope: Optional[str] = Field("mcp:read mcp:write", description="Requested scope")
    contacts: Optional[List[str]] = Field(None, description="Contact email addresses")
    logo_uri: Optional[str] = Field(None, description="Logo URI")
    client_uri: Optional[str] = Field(None, description="Client homepage URI")
    policy_uri: Optional[str] = Field(None, description="Privacy policy URI")
    tos_uri: Optional[str] = Field(None, description="Terms of service URI")

    @validator('redirect_uris')
    def validate_redirect_uris(cls, v):
        if not v:
            raise ValueError('At least one redirect URI is required')
        for uri in v:
            if not (uri.startswith('https://') or 
                   uri.startswith('http://localhost') or 
                   uri.startswith('http://127.0.0.1') or
                   '://' in uri):  # Allow custom schemes for native apps
                raise ValueError(f'Invalid redirect URI: {uri}')
        return v

class ClientRegistrationResponse(BaseModel):
    """OAuth 2.1 Dynamic Client Registration Response"""
    client_id: str
    client_name: str
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    scope: str
    token_endpoint_auth_method: str
    client_id_issued_at: int

class TokenRequest(BaseModel):
    """OAuth 2.1 Token Request"""
    grant_type: str = Field(..., description="Authorization grant type")
    code: Optional[str] = Field(None, description="Authorization code")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI")
    client_id: Optional[str] = Field(None, description="Client identifier")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier")
    refresh_token: Optional[str] = Field(None, description="Refresh token for refresh grant")

class TokenResponse(BaseModel):
    """OAuth 2.1 Token Response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class TokenIntrospectionResponse(BaseModel):
    """OAuth 2.1 Token Introspection Response"""
    active: bool
    client_id: Optional[str] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    sub: Optional[str] = None

# MCP Models
class MCPError(BaseModel):
    """MCP JSON-RPC Error"""
    code: int
    message: str
    data: Optional[Any] = None

class MCPRequest(BaseModel):
    """MCP JSON-RPC Request"""
    jsonrpc: str = Field("2.0", description="JSON-RPC version")
    method: str = Field(..., description="Method name")
    params: Optional[Dict[str, Any]] = Field(None, description="Method parameters")
    id: Optional[Union[str, int]] = Field(None, description="Request identifier")

class MCPResponse(BaseModel):
    """MCP JSON-RPC Response"""
    jsonrpc: str = Field("2.0", description="JSON-RPC version")
    id: Optional[Union[str, int]] = Field(None, description="Request identifier")
    result: Optional[Any] = Field(None, description="Method result")
    error: Optional[MCPError] = Field(None, description="Error information")

class MCPServerInfo(BaseModel):
    """MCP Server Information"""
    name: str
    version: str
    protocolVersion: str = "2025-03-26"

class MCPClientInfo(BaseModel):
    """MCP Client Information"""
    name: str
    version: str

class MCPCapabilities(BaseModel):
    """MCP Capabilities"""
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None

class MCPInitializeParams(BaseModel):
    """MCP Initialize Parameters"""
    protocolVersion: str
    clientInfo: MCPClientInfo
    capabilities: MCPCapabilities

class MCPInitializeResult(BaseModel):
    """MCP Initialize Result"""
    protocolVersion: str
    serverInfo: MCPServerInfo
    capabilities: MCPCapabilities

class MCPTool(BaseModel):
    """MCP Tool Definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPToolsListResult(BaseModel):
    """MCP Tools List Result"""
    tools: List[MCPTool]

class MCPToolCallParams(BaseModel):
    """MCP Tool Call Parameters"""
    name: str
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MCPContentItem(BaseModel):
    """MCP Content Item"""
    type: str
    text: Optional[str] = None
    data: Optional[str] = None
    mimeType: Optional[str] = None

class MCPToolCallResult(BaseModel):
    """MCP Tool Call Result"""
    content: List[MCPContentItem]
    isError: Optional[bool] = False

class MCPResource(BaseModel):
    """MCP Resource Definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class MCPResourcesListResult(BaseModel):
    """MCP Resources List Result"""
    resources: List[MCPResource]

class MCPResourceReadParams(BaseModel):
    """MCP Resource Read Parameters"""
    uri: str

class MCPResourceReadResult(BaseModel):
    """MCP Resource Read Result"""
    contents: List[MCPContentItem]

class MCPPrompt(BaseModel):
    """MCP Prompt Definition"""
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None

class MCPPromptsListResult(BaseModel):
    """MCP Prompts List Result"""
    prompts: List[MCPPrompt]

class MCPPromptGetParams(BaseModel):
    """MCP Prompt Get Parameters"""
    name: str
    arguments: Optional[Dict[str, Any]] = None

class MCPPromptGetResult(BaseModel):
    """MCP Prompt Get Result"""
    description: Optional[str] = None
    messages: List[Dict[str, Any]]

# Airtable Models
class AirtableBase(BaseModel):
    """Airtable Base Information"""
    id: str
    name: str
    permissionLevel: str

class AirtableField(BaseModel):
    """Airtable Field Definition"""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class AirtableTable(BaseModel):
    """Airtable Table Information"""
    id: str
    name: str
    description: Optional[str] = None
    primaryFieldId: Optional[str] = None
    fields: Optional[List[AirtableField]] = None
    views: Optional[List[Dict[str, Any]]] = None

class AirtableRecord(BaseModel):
    """Airtable Record"""
    id: str
    fields: Dict[str, Any]
    createdTime: Optional[str] = None

class AirtableRecordCreate(BaseModel):
    """Airtable Record Creation"""
    fields: Dict[str, Any]

class AirtableRecordUpdate(BaseModel):
    """Airtable Record Update"""
    id: str
    fields: Dict[str, Any]

class AirtableFieldCreate(BaseModel):
    """Airtable Field Creation"""
    name: str
    type: str
    description: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

    @validator('type')
    def validate_field_type(cls, v):
        valid_types = [
            'singleLineText', 'multilineText', 'email', 'url', 'phoneNumber',
            'number', 'currency', 'percent', 'duration', 'rating',
            'singleSelect', 'multipleSelects', 'checkbox', 'date', 'dateTime',
            'multipleAttachments', 'autoNumber', 'barcode', 'formula',
            'lookup', 'count', 'rollup', 'multipleRecordLinks',
            'singleCollaborator', 'multipleCollaborators', 'lastModifiedTime',
            'lastModifiedBy', 'createdTime', 'createdBy', 'richText', 'aiText'
        ]
        if v not in valid_types:
            raise ValueError(f'Invalid field type: {v}')
        return v

class AirtableSort(BaseModel):
    """Airtable Sort Definition"""
    field: str
    direction: Optional[str] = Field("asc", regex="^(asc|desc)$")

# API Response Models
class HealthCheckResponse(BaseModel):
    """Health Check Response"""
    status: str
    service: str
    version: str
    timestamp: str
    components: Dict[str, str]
    environment: str

class SetupInfoResponse(BaseModel):
    """Setup Information Response"""
    service: str
    version: str
    specification: str
    status: str
    for_claude: Dict[str, str]
    endpoints: Dict[str, str]
    testing: Dict[str, str]
    tools_available: List[str]

# Error Models
class APIError(BaseModel):
    """Generic API Error"""
    error: str
    message: str
    details: Optional[Any] = None
    timestamp: Optional[str] = None

class ValidationError(BaseModel):
    """Validation Error"""
    error: str = "validation_error"
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None

class AuthenticationError(BaseModel):
    """Authentication Error"""
    error: str = "authentication_error"
    message: str
    www_authenticate: Optional[str] = None

class AuthorizationError(BaseModel):
    """Authorization Error"""
    error: str = "authorization_error"
    message: str
    required_scope: Optional[str] = None

class RateLimitError(BaseModel):
    """Rate Limit Error"""
    error: str = "rate_limit_exceeded"
    message: str
    retry_after: Optional[int] = None
