import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

logger = logging.getLogger(__name__)

class MCPTransport:
    """
    Implements MCP Streamable HTTP transport according to specification 2025-03-26
    Handles both JSON-RPC batch responses and SSE streaming
    """
    
    def __init__(self, auth_manager, airtable_client):
        self.auth_manager = auth_manager
        self.airtable_client = airtable_client
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # MCP server capabilities
        self.server_info = {
            "name": "airtable-remote-mcp",
            "version": "2.0.0",
            "protocolVersion": "2025-03-26"
        }
        
        # Available tools
        self.tools = [
            {
                "name": "list_bases",
                "description": "List all accessible Airtable bases",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "list_tables",
                "description": "List all tables in a specific base",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "detailLevel": {
                            "type": "string", 
                            "enum": ["tableIdentifiersOnly", "identifiersOnly", "full"],
                            "default": "full",
                            "description": "Level of detail to return"
                        }
                    },
                    "required": ["baseId"]
                }
            },
            {
                "name": "describe_table",
                "description": "Get detailed information about a specific table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "detailLevel": {
                            "type": "string",
                            "enum": ["tableIdentifiersOnly", "identifiersOnly", "full"],
                            "default": "full"
                        }
                    },
                    "required": ["baseId", "tableId"]
                }
            },
            {
                "name": "list_records",
                "description": "List records from a table with optional filtering and sorting",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "filterByFormula": {"type": "string", "description": "Airtable formula to filter records"},
                        "maxRecords": {"type": "number", "description": "Maximum number of records to return"},
                        "sort": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "direction": {"type": "string", "enum": ["asc", "desc"]}
                                },
                                "required": ["field"]
                            }
                        },
                        "view": {"type": "string", "description": "View name or ID to use"}
                    },
                    "required": ["baseId", "tableId"]
                }
            },
            {
                "name": "search_records",
                "description": "Search for records containing specific text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "searchTerm": {"type": "string", "description": "Text to search for"},
                        "fieldIds": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific field IDs to search in"
                        },
                        "maxRecords": {"type": "number", "description": "Maximum number of records to return"},
                        "view": {"type": "string", "description": "View name or ID to use"}
                    },
                    "required": ["baseId", "tableId", "searchTerm"]
                }
            },
            {
                "name": "get_record",
                "description": "Get a specific record by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "recordId": {"type": "string", "description": "The record ID"}
                    },
                    "required": ["baseId", "tableId", "recordId"]
                }
            },
            {
                "name": "create_record",
                "description": "Create a new record in a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "fields": {"type": "object", "description": "Record fields as key-value pairs"}
                    },
                    "required": ["baseId", "tableId", "fields"]
                }
            },
            {
                "name": "update_records",
                "description": "Update existing records (up to 10 at once)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "records": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Record ID"},
                                    "fields": {"type": "object", "description": "Fields to update"}
                                },
                                "required": ["id", "fields"]
                            },
                            "maxItems": 10
                        }
                    },
                    "required": ["baseId", "tableId", "records"]
                }
            },
            {
                "name": "delete_records",
                "description": "Delete records from a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "recordIds": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of record IDs to delete"
                        }
                    },
                    "required": ["baseId", "tableId", "recordIds"]
                }
            },
            {
                "name": "create_table",
                "description": "Create a new table in a base",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "name": {"type": "string", "description": "Table name"},
                        "description": {"type": "string", "description": "Table description"},
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "options": {"type": "object"}
                                },
                                "required": ["name", "type"]
                            },
                            "description": "Table fields definition"
                        }
                    },
                    "required": ["baseId", "name", "fields"]
                }
            },
            {
                "name": "update_table",
                "description": "Update table name or description",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "name": {"type": "string", "description": "New table name"},
                        "description": {"type": "string", "description": "New table description"}
                    },
                    "required": ["baseId", "tableId"]
                }
            },
            {
                "name": "create_field",
                "description": "Add a new field to a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "field": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "options": {"type": "object"}
                            },
                            "required": ["name", "type"]
                        }
                    },
                    "required": ["baseId", "tableId", "field"]
                }
            },
            {
                "name": "update_field",
                "description": "Update field name or description",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseId": {"type": "string", "description": "The Airtable base ID"},
                        "tableId": {"type": "string", "description": "The table ID"},
                        "fieldId": {"type": "string", "description": "The field ID"},
                        "name": {"type": "string", "description": "New field name"},
                        "description": {"type": "string", "description": "New field description"}
                    },
                    "required": ["baseId", "tableId", "fieldId"]
                }
            }
        ]
    
    async def handle_post_request(self, request: Request, token_data: Dict[str, Any]) -> JSONResponse:
        """Handle POST request for JSON-RPC messages"""
        try:
            # Parse JSON-RPC message
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                raise HTTPException(status_code=400, detail="Content-Type must be application/json")
            
            body = await request.body()
            if not body:
                raise HTTPException(status_code=400, detail="Request body is required")
            
            try:
                message = json.loads(body)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
            
            # Check for MCP protocol version header
            protocol_version = request.headers.get("mcp-protocol-version")
            if protocol_version and protocol_version != "2025-03-26":
                logger.warning(f"Unsupported protocol version: {protocol_version}")
            
            # Handle single message or batch
            if isinstance(message, list):
                # Batch request
                responses = []
                session_id = None
                
                for msg in message:
                    response = await self._handle_jsonrpc_message(msg, token_data, request)
                    responses.append(response)
                    
                    # Extract session ID from first response if available
                    if not session_id and hasattr(response, 'get') and response.get('session_id'):
                        session_id = response['session_id']
                
                # Return batch response
                response_headers = {}
                if session_id:
                    response_headers["Mcp-Session-Id"] = session_id
                
                return JSONResponse(content=responses, headers=response_headers)
            else:
                # Single request
                response = await self._handle_jsonrpc_message(message, token_data, request)
                
                response_headers = {}
                if hasattr(response, 'get') and response.get('session_id'):
                    response_headers["Mcp-Session-Id"] = response['session_id']
                
                return JSONResponse(content=response, headers=response_headers)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def handle_get_request(self, request: Request, token_data: Dict[str, Any]) -> StreamingResponse:
        """Handle GET request for SSE streaming"""
        try:
            # Check if client wants to resume a session
            last_event_id = request.headers.get("last-event-id")
            session_id = request.headers.get("mcp-session-id")
            
            if not session_id:
                session_id = str(uuid.uuid4())
            
            logger.info(f"Opening SSE stream for session {session_id}")
            
            async def generate_sse():
                try:
                    # Send initial connection event
                    yield f"id: {uuid.uuid4()}\n"
                    yield f"event: connection\n"
                    yield f"data: {json.dumps({'type': 'connection', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    
                    # Keep connection alive and handle any server-initiated messages
                    while True:
                        # Send periodic ping to keep connection alive
                        yield f"id: {uuid.uuid4()}\n"
                        yield f"event: ping\n"
                        yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                        
                        await asyncio.sleep(30)  # Ping every 30 seconds
                        
                except asyncio.CancelledError:
                    logger.info(f"SSE stream cancelled for session {session_id}")
                    raise
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    yield f"event: error\n"
                    yield f"data: {json.dumps({'error': 'Stream error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_sse(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Mcp-Session-Id": session_id,
                    "Access-Control-Expose-Headers": "Mcp-Session-Id"
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            if "mcp:read" not in scopes and "mcp:write" not in scopes and "mcp:admin" not in scopes:
                return self._create_error_response(msg_id, -32603, "Insufficient permissions", "mcp:read or mcp:write scope required")
            
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return self._create_error_response(msg_id, -32602, "Invalid params", "Tool name is required")
            
            # Check if tool exists
            tool_names = [tool["name"] for tool in self.tools]
            if tool_name not in tool_names:
                return self._create_error_response(msg_id, -32601, "Tool not found", f"Tool '{tool_name}' not found")
            
            # Execute tool
            result = await self._execute_tool(tool_name, arguments, token_data)
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in tools/call: {e}")
            return self._create_error_response(msg_id, -32603, "Internal error", str(e))
    
    async def _handle_resources_list(self, msg_id: str, params: Dict[str, Any], token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list method"""
        try:
            # Check scope authorization
            scopes = token_data.get("scope", "").split()
            if "mcp:read" not in scopes and "mcp:admin" not in scopes:
                return self._create_error_response(msg_id, -32603, "Insufficient permissions", "mcp:read scope required")
            
            # For now, return empty resources list
            # Could be extended to expose Airtable schemas as resources
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "resources": []
                }
            }
            
        except Exception as e:
            logger.error(f"Error in resources/list: {e}")
            return self._create_error_response(msg_id, -32603, "Internal error", str(e))
    
    async def _handle_resources_read(self, msg_id: str, params: Dict[str, Any], token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read method"""
        try:
            return self._create_error_response(msg_id, -32601, "Method not found", "resources/read not implemented")
            
        except Exception as e:
            logger.error(f"Error in resources/read: {e}")
            return self._create_error_response(msg_id, -32603, "Internal error", str(e))
    
    async def _handle_prompts_list(self, msg_id: str, params: Dict[str, Any], token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list method"""
        try:
            # Check scope authorization
            scopes = token_data.get("scope", "").split()
            if "mcp:read" not in scopes and "mcp:admin" not in scopes:
                return self._create_error_response(msg_id, -32603, "Insufficient permissions", "mcp:read scope required")
            
            # For now, return empty prompts list
            # Could be extended to provide Airtable-specific prompts
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "prompts": []
                }
            }
            
        except Exception as e:
            logger.error(f"Error in prompts/list: {e}")
            return self._create_error_response(msg_id, -32603, "Internal error", str(e))
    
    async def _handle_prompts_get(self, msg_id: str, params: Dict[str, Any], token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get method"""
        try:
            return self._create_error_response(msg_id, -32601, "Method not found", "prompts/get not implemented")
            
        except Exception as e:
            logger.error(f"Error in prompts/get: {e}")
            return self._create_error_response(msg_id, -32603, "Internal error", str(e))
    
    async def _handle_ping(self, msg_id: str, params: Dict[str, Any], token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping method"""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "status": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any], token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the specified tool with given arguments"""
        try:
            # Check write permissions for write operations
            write_tools = ["create_record", "update_records", "delete_records", "create_table", "update_table", "create_field", "update_field"]
            if tool_name in write_tools:
                scopes = token_data.get("scope", "").split()
                if "mcp:write" not in scopes and "mcp:admin" not in scopes:
                    raise ValueError("Write operations require mcp:write or mcp:admin scope")
            
            # Execute the appropriate Airtable operation
            if tool_name == "list_bases":
                return await self.airtable_client.list_bases()
            
            elif tool_name == "list_tables":
                base_id = arguments.get("baseId")
                detail_level = arguments.get("detailLevel", "full")
                return await self.airtable_client.list_tables(base_id, detail_level)
            
            elif tool_name == "describe_table":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                detail_level = arguments.get("detailLevel", "full")
                return await self.airtable_client.describe_table(base_id, table_id, detail_level)
            
            elif tool_name == "list_records":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                filter_by_formula = arguments.get("filterByFormula")
                max_records = arguments.get("maxRecords")
                sort = arguments.get("sort")
                view = arguments.get("view")
                return await self.airtable_client.list_records(
                    base_id, table_id, filter_by_formula, max_records, sort, view
                )
            
            elif tool_name == "search_records":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                search_term = arguments.get("searchTerm")
                field_ids = arguments.get("fieldIds")
                max_records = arguments.get("maxRecords")
                view = arguments.get("view")
                return await self.airtable_client.search_records(
                    base_id, table_id, search_term, field_ids, max_records, view
                )
            
            elif tool_name == "get_record":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                record_id = arguments.get("recordId")
                return await self.airtable_client.get_record(base_id, table_id, record_id)
            
            elif tool_name == "create_record":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                fields = arguments.get("fields")
                return await self.airtable_client.create_record(base_id, table_id, fields)
            
            elif tool_name == "update_records":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                records = arguments.get("records")
                return await self.airtable_client.update_records(base_id, table_id, records)
            
            elif tool_name == "delete_records":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                record_ids = arguments.get("recordIds")
                return await self.airtable_client.delete_records(base_id, table_id, record_ids)
            
            elif tool_name == "create_table":
                base_id = arguments.get("baseId")
                name = arguments.get("name")
                description = arguments.get("description")
                fields = arguments.get("fields")
                return await self.airtable_client.create_table(base_id, name, description, fields)
            
            elif tool_name == "update_table":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                name = arguments.get("name")
                description = arguments.get("description")
                return await self.airtable_client.update_table(base_id, table_id, name, description)
            
            elif tool_name == "create_field":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                field = arguments.get("field")
                return await self.airtable_client.create_field(base_id, table_id, field)
            
            elif tool_name == "update_field":
                base_id = arguments.get("baseId")
                table_id = arguments.get("tableId")
                field_id = arguments.get("fieldId")
                name = arguments.get("name")
                description = arguments.get("description")
                return await self.airtable_client.update_field(base_id, table_id, field_id, name, description)
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise
    
    def _create_error_response(self, msg_id: Optional[str], code: int, message: str, data: Optional[str] = None) -> Dict[str, Any]:
        """Create a JSON-RPC error response"""
        error = {
            "code": code,
            "message": message
        }
        if data:
            error["data"] = data
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": error
        }
