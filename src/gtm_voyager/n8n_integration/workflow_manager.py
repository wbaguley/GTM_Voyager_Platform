from typing import Dict, Any, List, Optional
from .workflow_trigger import WorkflowTrigger
from .n8n_client import N8NClient

class WorkflowManager:
    """Workflow manager for GTM Voyager Platform n8n integration."""
    
    def __init__(self, n8n_base_url: str = "http://localhost:5678", api_key: str = None ):
        """Initialize the workflow manager."""
        self.n8n_client = N8NClient(base_url=n8n_base_url, api_key=api_key)
        self.active_workflows = {}
        self.workflow_triggers = {}
    
    def register_workflow(self, workflow_id: str, workflow_config: Dict[str, Any]):
        """Register a workflow with the manager."""
        self.active_workflows[workflow_id] = {
            'config': workflow_config,
            'status': 'registered',
            'executions': 0
        }
        
        # Create workflow trigger
        trigger = WorkflowTrigger(workflow_id=workflow_id)
        self.workflow_triggers[workflow_id] = trigger
        
        return f"Workflow {workflow_id} registered successfully"
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]):
        """Execute a registered workflow."""
        if workflow_id not in self.active_workflows:
            return {
                'success': False,
                'error': f"Workflow {workflow_id} not registered"
            }
        
        try:
            # Execute via n8n client
            result = self.n8n_client.execute_workflow(workflow_id, input_data)
            
            # Update workflow statistics
            self.active_workflows[workflow_id]['executions'] += 1
            self.active_workflows[workflow_id]['status'] = 'executed'
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'result': result,
                'execution_count': self.active_workflows[workflow_id]['executions']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Workflow execution failed: {str(e)}"
            }
    
    def get_workflow_status(self, workflow_id: str):
        """Get the status of a workflow."""
        if workflow_id not in self.active_workflows:
            return {
                'error': f"Workflow {workflow_id} not found"
            }
        
        return self.active_workflows[workflow_id]
    
    def list_workflows(self):
        """List all registered workflows."""
        return list(self.active_workflows.keys())
