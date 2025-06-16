# n8n Integration Module
"""
n8n workflow integration for GTM Voyager Platform.

This module handles workflow triggering, n8n API communication,
and business process automation integration.
"""

from .workflow_trigger import WorkflowTrigger
from .n8n_client import N8NClient
from .workflow_manager import WorkflowManager

__all__ = ["WorkflowTrigger", "N8NClient", "WorkflowManager"]

