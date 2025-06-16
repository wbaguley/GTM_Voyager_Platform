import requests
from typing import Dict, Any, Optional

class N8NClient:
    """n8n client for GTM Voyager Platform."""
    
    def __init__(self, base_url: str = "http://localhost:5678", api_key: str = None ):
        """Initialize the n8n client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                'X-N8N-API-KEY': api_key
            })
    
    def get_workflows(self):
        """Get list of available workflows."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/workflows")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': f"Failed to get workflows: {str(e)}"}
    
    def execute_workflow(self, workflow_id: str, data: Dict[str, Any]):
        """Execute a workflow with provided data."""
        try:
            payload = {'data': data}
            response = self.session.post(
                f"{self.base_url}/api/v1/workflows/{workflow_id}/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': f"Failed to execute workflow: {str(e)}"}
    
    def get_workflow_status(self, execution_id: str):
        """Get the status of a workflow execution."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/executions/{execution_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': f"Failed to get workflow status: {str(e)}"}
