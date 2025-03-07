from typing import Any, Callable, get_type_hints
from pydantic import BaseModel, Field
from dataclasses import is_dataclass, fields
from activities import calculator

def get_type_schema(type_annotation: Any) -> dict:
    """Convert Python type annotations to JSON schema types."""
    if type_annotation == str:
        return {"type": "string"}
    elif type_annotation == int:
        return {"type": "number", "format": "integer"}
    elif type_annotation == float:
        return {"type": "number"}
    elif type_annotation == bool:
        return {"type": "boolean"}
    elif type_annotation == list:
        return {"type": "array"}
    elif type_annotation == dict:
        return {"type": "object"}
    # Add more type mappings as needed
    return {"type": "string"}  # default to string for unknown types

def generate_schema_from_params(params_class: Any) -> dict:
    """Generate JSON schema from a dataclass parameters."""
    if not is_dataclass(params_class):
        raise ValueError("Input must be a dataclass")
    
    properties = {}
    required = []
    
    for field in fields(params_class):
        field_schema = get_type_schema(field.type)
        properties[field.name] = field_schema
        # Assume all fields are required for now
        required.append(field.name)
    
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }

def create_tool_schema(
    function: Callable,
    tool_name: str,
    description: str
) -> dict:
    """Create a complete tool schema for any given activity function."""
    # Get the first parameter type hint (assuming it's the params class)
    type_hints = get_type_hints(function)
    params_class = next(iter(type_hints.values()))
    
    # Create a dynamic schema class with the provided values
    schema_dict = {
        "name": tool_name,
        "description": description,
        "input_schema": generate_schema_from_params(params_class),
        "function": function.__name__
    }
    
    class ToolSchema(BaseModel):
        name: str
        description: str
        input_schema: dict
        function: str
    
    return ToolSchema(**schema_dict).model_dump()

# Example usage for calculator
calculator_schema = create_tool_schema(
    calculator,
    "calculator",
    "A calculator that can evaluate basic mathematical expressions"
)

# You can now use this for any other activity function as well
print(calculator_schema)
