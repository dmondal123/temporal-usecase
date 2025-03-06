from typing import get_type_hints, Any, Dict, List, Optional, Union, TypedDict
from pydantic import BaseModel, create_model
import inspect
from dataclasses import is_dataclass, fields
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

def get_type_schema(type_hint: Any) -> Dict[str, Any]:
    """Convert Python type hints to JSON schema types."""
    if type_hint == str:
        return {"type": "string"}
    elif type_hint == int:
        return {"type": "integer"}
    elif type_hint == float:
        return {"type": "number"}
    elif type_hint == bool:
        return {"type": "boolean"}
    elif type_hint == list or getattr(type_hint, "__origin__", None) == list:
        item_type = Any
        if hasattr(type_hint, "__args__"):
            item_type = type_hint.__args__[0]
            # If the item_type is a Dict or TypedDict, handle its structure
            if (item_type == dict or getattr(item_type, "__origin__", None) == dict) and hasattr(item_type, "__annotations__"):
                return {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            key: get_type_schema(value) 
                            for key, value in item_type.__annotations__.items()
                        },
                        "required": list(item_type.__annotations__.keys()),
                        "additionalProperties": False
                    }
                }
        return {
            "type": "array",
            "items": get_type_schema(item_type)
        }
    elif type_hint == dict or getattr(type_hint, "__origin__", None) == dict:
        # Handle Dict type with specific key-value types
        if hasattr(type_hint, "__annotations__"):
            return {
                "type": "object",
                "properties": {
                    key: get_type_schema(value) 
                    for key, value in type_hint.__annotations__.items()
                },
                "required": list(type_hint.__annotations__.keys()),
                "additionalProperties": False
            }
        return {
            "type": "object",
            "additionalProperties": True
        }
    elif is_dataclass(type_hint):
        properties = {}
        required = []
        for field in fields(type_hint):
            properties[field.name] = get_type_schema(field.type)
            if field.default == field.default_factory:  # No default value
                required.append(field.name)
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    elif isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
        schema = type_hint.model_json_schema()
        return {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }
    else:
        return {"type": "string"}  # fallback

def generate_parameter_description(name: str, type_hint: Any = None, is_tool: bool = False) -> str:
    """Generate a natural description using Claude."""
    client = Anthropic()
    
    if is_tool:
        prompt = f"""Write a clear, concise description of a tool named '{name}'. 
        Keep the description under 100 characters and focus on being helpful and precise."""
    else:
        type_name = getattr(type_hint, '__name__', str(type_hint))
        prompt = f"""Given a function parameter named '{name}' of type {type_name}, 
        write a clear, concise description of what this parameter represents and how it should be used. 
        Keep the description under 100 characters and focus on being helpful and precise."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    # Extract just the description text from the response
    response = message.content[0].text
    # Remove any quotes if present
    return response.strip("'\"")

def generate_tool_schema(func, description: str = None, tool_description: str = None) -> Dict[str, Any]:
    """
    Generate a tool schema from a function signature.
    
    Args:
        func: The function to generate a schema for
        description: Description of the tool's purpose. If None, will be generated.
        tool_description: Optional description of what the tool does. If provided, overrides description.
    
    Returns:
        dict: The tool schema
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    properties = {}
    required = []
    
    # Parse docstring for parameter descriptions
    param_descriptions = {}
    if func.__doc__:
        docstring_lines = func.__doc__.split('\n')
        for line in docstring_lines:
            for param_name in sig.parameters:
                param_marker = f":param {param_name}:"
                if param_marker in line:
                    param_descriptions[param_name] = line.split(param_marker)[1].strip()
    
    for param_name, param in sig.parameters.items():
        if param.name == 'self':  # Skip self for class methods
            continue
            
        param_type = type_hints.get(param_name, Any)
        param_schema = get_type_schema(param_type)
        
        # Add parameter description from docstring or generate using Claude
        if param_name in param_descriptions:
            param_schema['description'] = param_descriptions[param_name]
        else:
            param_schema['description'] = generate_parameter_description(param_name, param_type)
        
        properties[param_name] = param_schema
        
        # If parameter has no default value, it's required
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    # Use tool_description if provided, otherwise use description or generate one
    final_description = tool_description or description
    if final_description is None:
        final_description = generate_parameter_description(func.__name__, is_tool=True)
    
    return {
        "name": func.__name__,
        "description": final_description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
    }

def create_schema_function(func, description: str = None, tool_description: str = None) -> callable:
    """
    Creates a new function that returns the JSON schema for the given function.
    
    Args:
        func: The function to generate a schema for
        description: Optional description of the tool's purpose
        tool_description: Optional description of what the tool does. If provided, overrides description.
    
    Returns:
        callable: A new function named the same as the input function that returns the JSON schema
    """
    import json
    
    # Generate the schema
    schema = generate_tool_schema(func, description, tool_description)
    schema_str = json.dumps(schema, indent=2)
    
    # Create the function definition
    exec_str = f"""def {func.__name__}():
    return '''{schema_str}'''"""
    
    # Create namespace for exec
    namespace = {}
    exec(exec_str, namespace)
    
    # Return the created function
    return namespace[func.__name__]

def save_schema_function(func, output_path: str, description: str = None):
    """Creates and saves a function that returns the JSON schema to a new file."""
    import json
    
    schema = generate_tool_schema(func, description)
    schema_str = json.dumps(schema, indent=2)
    
    function_code = f"""def {func.__name__}():
    return '''{schema_str}'''
"""
    
    with open(output_path, 'w') as f:
        f.write(function_code)

# Example usage:
if __name__ == "__main__":
    # Example function with type hints
    def wait_for_assistance(
        thinking: str,
        wait_message: str
    ) :
        """
        Process agent messages with thinking step.
        
        """
        pass
    
    # Generate schema
    #schema = generate_tool_schema(
    #    wait_for_assistance
    #)
    
    # Print the generated schema
    import json
    #print(json.dumps(schema, indent=2))
    tool_description = "Use this tool to wait for assistance from the operator."
    #schema_func = create_schema_function(wait_for_assistance, tool_description)
    #print(schema_func)

    save_schema_function(wait_for_assistance, "wait_for_assistance.py", tool_description)