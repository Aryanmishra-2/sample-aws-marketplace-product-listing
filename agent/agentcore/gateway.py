"""
Agentcore Gateway - Tool and action routing
Routes agent actions to appropriate handlers
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field


@dataclass
class Action:
    """Represents a single action/tool"""
    name: str
    description: str
    handler: Callable
    parameters: Dict[str, Any]


class ActionGroup:
    """
    Group of related actions
    
    Example: ListingManagement, KnowledgeBase, etc.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize ActionGroup
        
        Args:
            name: Action group name
            description: Action group description
        """
        self.name = name
        self.description = description
        self.actions: Dict[str, Action] = {}
    
    def add_action(
        self,
        name: str,
        description: str,
        handler: Callable,
        parameters: Dict[str, Any]
    ):
        """
        Add an action to this group
        
        Args:
            name: Action name
            description: Action description
            handler: Function to execute the action
            parameters: Parameter schema
        """
        self.actions[name] = Action(
            name=name,
            description=description,
            handler=handler,
            parameters=parameters
        )
    
    def get_action(self, name: str) -> Optional[Action]:
        """Get action by name"""
        return self.actions.get(name)


class Gateway:
    """
    Agentcore Gateway routes actions to handlers
    
    Responsibilities:
    - Register action groups and actions
    - Route action requests to appropriate handlers
    - Provide tool definitions for Bedrock
    - Handle action execution errors
    """
    
    def __init__(self):
        """Initialize Gateway"""
        self.action_groups: Dict[str, ActionGroup] = {}
    
    def register_action_group(self, action_group: ActionGroup):
        """
        Register an action group
        
        Args:
            action_group: ActionGroup to register
        """
        self.action_groups[action_group.name] = action_group
    
    def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action by name
        
        Args:
            action_name: Name of the action to execute
            parameters: Action parameters
            
        Returns:
            Action execution result
        """
        # Find action across all groups
        for group in self.action_groups.values():
            action = group.get_action(action_name)
            if action:
                try:
                    return action.handler(**parameters)
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "action": action_name
                    }
        
        return {
            "success": False,
            "error": f"Action not found: {action_name}"
        }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for Bedrock Converse API
        
        Returns:
            List of tool specifications
        """
        tools = []
        
        for group in self.action_groups.values():
            for action in group.actions.values():
                tool_spec = {
                    "toolSpec": {
                        "name": action.name,
                        "description": action.description,
                        "inputSchema": {
                            "json": self._build_schema(action.parameters)
                        }
                    }
                }
                tools.append(tool_spec)
        
        return tools
    
    def _build_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Build JSON schema from parameter definitions"""
        properties = {}
        required = []
        
        for param_name, param_def in parameters.items():
            properties[param_name] = {
                "type": param_def.get("type", "string"),
                "description": param_def.get("description", "")
            }
            
            if param_def.get("type") == "array":
                properties[param_name]["items"] = param_def.get("items", {"type": "string"})
            
            if param_def.get("enum"):
                properties[param_name]["enum"] = param_def["enum"]
            
            if param_def.get("default") is not None:
                properties[param_name]["default"] = param_def["default"]
            
            if param_def.get("required", False):
                required.append(param_name)
        
        schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            schema["required"] = required
        
        return schema
