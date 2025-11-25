"""
Base class for all sub-agents
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class BaseSubAgent(ABC):
    """
    Base class for stage-specific sub-agents
    
    Each sub-agent is responsible for:
    1. Collecting required information for its stage
    2. Validating inputs against AWS Marketplace rules
    3. Executing stage-specific actions
    4. Determining when stage is complete
    """
    
    def __init__(self, stage_number: int, stage_name: str):
        self.stage_number = stage_number
        self.stage_name = stage_name
        self.stage_data = {}
        self.is_complete = False
        self.validation_errors = []
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Return list of required field names"""
        pass
    
    @abstractmethod
    def get_optional_fields(self) -> List[str]:
        """Return list of optional field names"""
        pass
    
    @abstractmethod
    def get_field_validations(self) -> Dict[str, Dict[str, Any]]:
        """
        Return validation rules for each field
        
        Format:
        {
            "field_name": {
                "type": "string",
                "min_length": 5,
                "max_length": 255,
                "pattern": r"^[a-zA-Z].*",
                "description": "Field description"
            }
        }
        """
        pass
    
    @abstractmethod
    def get_stage_instructions(self) -> str:
        """Return instructions for this stage"""
        pass
    
    @abstractmethod
    def process_stage(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user input for this stage
        
        Args:
            user_input: User's message
            context: Current conversation context
            
        Returns:
            {
                "status": "collecting" | "validating" | "complete" | "error",
                "message": "Response to user",
                "data": {...},  # Collected data
                "next_question": "...",  # Next question to ask (if collecting)
                "errors": [...]  # Validation errors (if any)
            }
        """
        pass
    
    def validate_field(self, field_name: str, value: Any) -> Optional[str]:
        """
        Validate a single field value
        
        Returns:
            Error message if invalid, None if valid
        """
        validations = self.get_field_validations()
        
        if field_name not in validations:
            return None
        
        rules = validations[field_name]
        
        # Type validation
        expected_type = rules.get("type")
        if expected_type == "string" and not isinstance(value, str):
            return f"{field_name} must be a string"
        elif expected_type == "integer" and not isinstance(value, int):
            return f"{field_name} must be an integer"
        elif expected_type == "array" and not isinstance(value, list):
            return f"{field_name} must be an array"
        
        # String validations
        if isinstance(value, str):
            min_len = rules.get("min_length")
            max_len = rules.get("max_length")
            
            if min_len and len(value) < min_len:
                return f"{field_name} must be at least {min_len} characters"
            
            if max_len and len(value) > max_len:
                return f"{field_name} must be at most {max_len} characters"
            
            pattern = rules.get("pattern")
            if pattern:
                import re
                # Use case-insensitive matching for patterns
                if not re.match(pattern, value, re.IGNORECASE):
                    return f"{field_name} format is invalid"
        
        # Array validations
        if isinstance(value, list):
            min_items = rules.get("min_items")
            max_items = rules.get("max_items")
            
            if min_items and len(value) < min_items:
                return f"{field_name} must have at least {min_items} items"
            
            if max_items and len(value) > max_items:
                return f"{field_name} must have at most {max_items} items"
        
        return None
    
    def validate_all_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate all fields in data
        
        Returns:
            List of error messages
        """
        errors = []
        
        # Check required fields
        for field in self.get_required_fields():
            if field not in data or not data[field]:
                errors.append(f"Required field missing: {field}")
            else:
                error = self.validate_field(field, data[field])
                if error:
                    errors.append(error)
        
        # Validate optional fields if present
        for field in self.get_optional_fields():
            if field in data and data[field]:
                error = self.validate_field(field, data[field])
                if error:
                    errors.append(error)
        
        return errors
    
    def is_stage_complete(self) -> bool:
        """Check if all required data is collected and valid"""
        required = self.get_required_fields()
        
        # Check all required fields are present
        for field in required:
            if field not in self.stage_data or not self.stage_data[field]:
                return False
        
        # Check no validation errors
        errors = self.validate_all_fields(self.stage_data)
        return len(errors) == 0
    
    def get_progress_summary(self) -> str:
        """Get summary of stage progress"""
        required = self.get_required_fields()
        optional = self.get_optional_fields()
        
        collected_required = sum(1 for f in required if f in self.stage_data and self.stage_data[f])
        collected_optional = sum(1 for f in optional if f in self.stage_data and self.stage_data[f])
        
        summary = f"Stage {self.stage_number}: {self.stage_name}\n"
        summary += f"Required fields: {collected_required}/{len(required)}\n"
        summary += f"Optional fields: {collected_optional}/{len(optional)}\n"
        summary += f"Status: {'Complete ✅' if self.is_stage_complete() else 'In Progress ⏳'}"
        
        return summary
    
    def reset(self):
        """Reset stage data"""
        self.stage_data = {}
        self.is_complete = False
        self.validation_errors = []
