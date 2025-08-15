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

# Session Models
class MCPSession(BaseModel):
    """MCP Session Information"""
    session_id: str
    client_info: MCPClientInfo
    protocol_version: str
    client_capabilities: MCPCapabilities
    token_data: Dict[str, Any]
    created_at: str
    last_activity: str

class OAuthClient(BaseModel):
    """OAuth Client Information"""
    client_id: str
    client_name: str
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    scope: str
    token_endpoint_auth_method: str
    created_at: float
    application_type: Optional[str] = None
    contacts: Optional[List[str]] = None
    logo_uri: Optional[str] = None
    client_uri: Optional[str] = None
    policy_uri: Optional[str] = None
    tos_uri: Optional[str] = None

class AuthorizationCode(BaseModel):
    """Authorization Code Information"""
    client_id: str
    redirect_uri: str
    scope: str
    code_challenge: str
    code_challenge_method: str
    created_at: float
    expires_at: float
    used: bool = False

class AccessToken(BaseModel):
    """Access Token Information"""
    client_id: str
    scope: str
    created_at: float
    expires_at: float
    token_type: str = "Bearer"

class RefreshToken(BaseModel):
    """Refresh Token Information"""
    client_id: str
    scope: str
    created_at: float
    expires_at: float
    access_token: str

# Webhook Models (for future extension)
class WebhookPayload(BaseModel):
    """Webhook Payload"""
    event: str
    timestamp: str
    data: Dict[str, Any]

class WebhookSubscription(BaseModel):
    """Webhook Subscription"""
    id: str
    url: str
    events: List[str]
    active: bool = True
    created_at: str

# Configuration Models
class ServerConfiguration(BaseModel):
    """Server Configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "production"
    base_url: str
    secret_key: str
    allowed_origins: List[str]
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    oauth_code_expiry: int = 60
    oauth_token_expiry: int = 3600
    oauth_refresh_token_expiry: int = 86400
    cleanup_interval: int = 300
    log_level: str = "INFO"

# Utility Models
class PaginationInfo(BaseModel):
    """Pagination Information"""
    offset: Optional[str] = None
    limit: Optional[int] = None
    total: Optional[int] = None
    has_more: Optional[bool] = None

class AirtableListResponse(BaseModel):
    """Generic Airtable List Response"""
    records: Optional[List[AirtableRecord]] = None
    tables: Optional[List[AirtableTable]] = None
    bases: Optional[List[AirtableBase]] = None
    offset: Optional[str] = None

class BatchOperationResult(BaseModel):
    """Batch Operation Result"""
    successful: List[str]
    failed: List[Dict[str, Any]]
    total_processed: int
    total_successful: int
    total_failed: int

# Metrics Models (for monitoring)
class RequestMetrics(BaseModel):
    """Request Metrics"""
    method: str
    endpoint: str
    status_code: int
    response_time_ms: float
    timestamp: str
    client_id: Optional[str] = None
    error: Optional[str] = None

class SystemMetrics(BaseModel):
    """System Metrics"""
    uptime_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_sessions: int
    total_requests: int
    error_rate: float
    timestamp: str
