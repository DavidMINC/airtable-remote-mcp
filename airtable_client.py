import os
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

class AirtableConfig:
    """Configuration for Airtable API client"""
    
    def __init__(self):
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_url = os.getenv("AIRTABLE_BASE_URL", "https://api.airtable.com/v0")
        self.timeout = int(os.getenv("AIRTABLE_TIMEOUT", 30))
        
        if not self.api_key:
            logger.warning("AIRTABLE_API_KEY not found - some functionality will be limited")
            self.api_key = "placeholder"
        else:
            logger.info("Airtable configuration loaded successfully")

class AirtableClient:
    """Enhanced Airtable API client with comprehensive error handling and all API operations"""
    
    def __init__(self, config: AirtableConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Airtable-Remote-MCP/2.0.0"
            },
            timeout=config.timeout
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Airtable API with comprehensive error handling"""
        if self.config.api_key == "placeholder":
            raise ValueError("Airtable API key not configured. Please set AIRTABLE_API_KEY environment variable.")
        
        try:
            response = await self.client.request(method, url, **kwargs)
            
            # Handle different response status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 204:
                return {"success": True}
            elif response.status_code == 401:
                raise ValueError("Invalid Airtable API key")
            elif response.status_code == 403:
                raise ValueError("Access forbidden - check API key permissions")
            elif response.status_code == 404:
                raise ValueError("Resource not found")
            elif response.status_code == 422:
                error_detail = response.json() if response.content else {"error": "Validation error"}
                raise ValueError(f"Validation error: {error_detail}")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded - please wait before retrying")
            else:
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Airtable API HTTP error: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Airtable API error: {e.response.text}")
        except httpx.TimeoutException:
            logger.error("Airtable API timeout")
            raise ValueError("Request timeout - Airtable API is not responding")
        except httpx.NetworkError as e:
            logger.error(f"Network error: {e}")
            raise ValueError("Network error - unable to connect to Airtable API")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")

    # Base Operations
    async def list_bases(self) -> Dict[str, Any]:
        """List all accessible Airtable bases"""
        url = f"{self.config.base_url}/meta/bases"
        return await self._request("GET", url)

    # Table Operations
    async def list_tables(self, base_id: str, detail_level: str = "full") -> Dict[str, Any]:
        """List all tables in a specific base"""
        url = f"{self.config.base_url}/meta/bases/{base_id}/tables"
        params = {}
        if detail_level != "full":
            params["detailLevel"] = detail_level
        return await self._request("GET", url, params=params)

    async def describe_table(self, base_id: str, table_id: str, detail_level: str = "full") -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        url = f"{self.config.base_url}/meta/bases/{base_id}/tables/{table_id}"
        params = {}
        if detail_level != "full":
            params["detailLevel"] = detail_level
        return await self._request("GET", url, params=params)

    async def create_table(self, base_id: str, name: str, description: Optional[str] = None, fields: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new table in a base"""
        url = f"{self.config.base_url}/meta/bases/{base_id}/tables"
        data = {
            "name": name,
            "fields": fields or []
        }
        if description:
            data["description"] = description
        return await self._request("POST", url, json=data)

    async def update_table(self, base_id: str, table_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Update table name or description"""
        url = f"{self.config.base_url}/meta/bases/{base_id}/tables/{table_id}"
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        
        if not data:
            raise ValueError("At least one of name or description must be provided")
        
        return await self._request("PATCH", url, json=data)

    # Field Operations
    async def create_field(self, base_id: str, table_id: str, field: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new field to a table"""
        url = f"{self.config.base_url}/meta/bases/{base_id}/tables/{table_id}/fields"
        return await self._request("POST", url, json=field)

    async def update_field(self, base_id: str, table_id: str, field_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Update field name or description"""
        url = f"{self.config.base_url}/meta/bases/{base_id}/tables/{table_id}/fields/{field_id}"
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        
        if not data:
            raise ValueError("At least one of name or description must be provided")
        
        return await self._request("PATCH", url, json=data)

    # Record Operations
    async def list_records(
        self, 
        base_id: str, 
        table_id: str, 
        filter_by_formula: Optional[str] = None,
        max_records: Optional[int] = None,
        sort: Optional[List[Dict[str, str]]] = None,
        view: Optional[str] = None
    ) -> Dict[str, Any]:
        """List records from a table with optional filtering and sorting"""
        url = f"{self.config.base_url}/{base_id}/{table_id}"
        params = {}
        
        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula
        if max_records:
            params["maxRecords"] = str(max_records)
        if view:
            params["view"] = view
        if sort:
            # Convert sort array to Airtable format
            for i, sort_item in enumerate(sort):
                params[f"sort[{i}][field]"] = sort_item["field"]
                if "direction" in sort_item:
                    params[f"sort[{i}][direction]"] = sort_item["direction"]
        
        return await self._request("GET", url, params=params)

    async def search_records(
        self,
        base_id: str,
        table_id: str,
        search_term: str,
        field_ids: Optional[List[str]] = None,
        max_records: Optional[int] = None,
        view: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for records containing specific text"""
        url = f"{self.config.base_url}/{base_id}/{table_id}"
        params = {
            "filterByFormula": f'SEARCH("{search_term}", CONCATENATE({", ".join(field_ids) if field_ids else "RECORD_ID()"})) != ""'
        }
        
        if max_records:
            params["maxRecords"] = str(max_records)
        if view:
            params["view"] = view
        
        return await self._request("GET", url, params=params)

    async def get_record(self, base_id: str, table_id: str, record_id: str) -> Dict[str, Any]:
        """Get a specific record by ID"""
        url = f"{self.config.base_url}/{base_id}/{table_id}/{record_id}"
        return await self._request("GET", url)

    async def create_record(self, base_id: str, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record"""
        url = f"{self.config.base_url}/{base_id}/{table_id}"
        data = {"fields": fields}
        return await self._request("POST", url, json=data)

    async def update_records(self, base_id: str, table_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update existing records (up to 10 at once)"""
        if len(records) > 10:
            raise ValueError("Cannot update more than 10 records at once")
        
        url = f"{self.config.base_url}/{base_id}/{table_id}"
        data = {"records": records}
        return await self._request("PATCH", url, json=data)

    async def delete_records(self, base_id: str, table_id: str, record_ids: List[str]) -> Dict[str, Any]:
        """Delete records from a table"""
        if len(record_ids) > 10:
            raise ValueError("Cannot delete more than 10 records at once")
        
        url = f"{self.config.base_url}/{base_id}/{table_id}"
        params = {}
        for i, record_id in enumerate(record_ids):
            params[f"records[{i}]"] = record_id
        
        return await self._request("DELETE", url, params=params)

    # Batch Operations
    async def create_records_batch(self, base_id: str, table_id: str, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple records in batches of 10"""
        if len(records) <= 10:
            result = await self._request("POST", f"{self.config.base_url}/{base_id}/{table_id}", json={"records": records})
            return result.get("records", [])
        
        # Split into batches of 10
        results = []
        for i in range(0, len(records), 10):
            batch = records[i:i+10]
            batch_result = await self._request("POST", f"{self.config.base_url}/{base_id}/{table_id}", json={"records": batch})
            results.extend(batch_result.get("records", []))
        
        return results

    async def update_records_batch(self, base_id: str, table_id: str, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update multiple records in batches of 10"""
        if len(records) <= 10:
            result = await self._request("PATCH", f"{self.config.base_url}/{base_id}/{table_id}", json={"records": records})
            return result.get("records", [])
        
        # Split into batches of 10
        results = []
        for i in range(0, len(records), 10):
            batch = records[i:i+10]
            batch_result = await self._request("PATCH", f"{self.config.base_url}/{base_id}/{table_id}", json={"records": batch})
            results.extend(batch_result.get("records", []))
        
        return results

    async def delete_records_batch(self, base_id: str, table_id: str, record_ids: List[str]) -> List[str]:
        """Delete multiple records in batches of 10"""
        if len(record_ids) <= 10:
            params = {}
            for i, record_id in enumerate(record_ids):
                params[f"records[{i}]"] = record_id
            result = await self._request("DELETE", f"{self.config.base_url}/{base_id}/{table_id}", params=params)
            return result.get("records", [])
        
        # Split into batches of 10
        results = []
        for i in range(0, len(record_ids), 10):
            batch = record_ids[i:i+10]
            params = {}
            for j, record_id in enumerate(batch):
                params[f"records[{j}]"] = record_id
            batch_result = await self._request("DELETE", f"{self.config.base_url}/{base_id}/{table_id}", params=params)
            results.extend(batch_result.get("records", []))
        
        return results
