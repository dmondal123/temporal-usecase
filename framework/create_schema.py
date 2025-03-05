from typing import get_type_hints, Any, Dict, List, Optional, Union, TypedDict
from pydantic import BaseModel, create_model, Field
import inspect
from dataclasses import is_dataclass, fields
from anthropic import Anthropic
import os
from dotenv import load_dotenv
from langchain.tools import Tool, ToolFunctionInterface
import json

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

def generate_tool_schema(func, description: str = None) -> Dict[str, Any]:
    """
    Generate a tool schema from a function signature using Pydantic.
    Returns schema in exact format required by Anthropic.
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Create field definitions for the parameters model
    fields = {}
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
            
        param_type = type_hints.get(param_name, Any)
        param_description = generate_parameter_description(param_name, param_type)
        
        fields[param_name] = (
            param_type,
            Field(
                description=param_description,
                title=param_name.title(),
                default=... if param.default == inspect.Parameter.empty else param.default
            )
        )
    
    # Generate tool description if not provided
    if description is None:
        description = generate_parameter_description(func.__name__, is_tool=True)
    
    # Create the Pydantic model for parameters
    ParametersModel = create_model(
        f"{func.__name__}Parameters",
        **fields
    )
    
    # Get the JSON schema from the Pydantic model
    parameters_schema = ParametersModel.model_json_schema()
    
    # Create the exact schema format required
    schema = {
        "name": func.__name__,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                name: {
                    "type": prop.get("type", "string"),  # default to string if type not specified
                    "description": prop.get("description", ""),
                    "title": prop.get("title", name.title())
                }
                for name, prop in parameters_schema.get("properties", {}).items()
            },
            "required": parameters_schema.get("required", [])
        }
    }
    
    # Validate JSON serialization
    try:
        json.dumps(schema)
    except Exception as e:
        raise ValueError(f"Schema is not JSON-serializable: {e}")
    
    return schema

def create_schema_function(func, description: str = None) -> callable:
    """Creates a new function that returns the JSON schema."""
    schema = generate_tool_schema(func, description)
    
    exec_str = f"""def {func.__name__}():
    return {schema}"""
    
    namespace = {}
    exec(exec_str, namespace)
    return namespace[func.__name__]

def save_schema_function(func, output_path: str, description: str = None):
    """Creates and saves a function that returns the JSON schema to a new file."""
    schema = generate_tool_schema(func, description)
    
    function_code = f"""def {func.__name__}():
    return {schema}
"""
    
    with open(output_path, 'w') as f:
        f.write(function_code)

# Example usage:
if __name__ == "__main__":
    # Example function with type hints
    def send_opeator_message(
        thinking: str,
        operator_message: str
    ) -> str:
        """
        Process agent messages with thinking step.
        
        """
        pass
    
    # Generate schema
    schema = generate_tool_schema(
        send_opeator_message
    )
    
    # Print the generated schema
    #print(json.dumps(schema, indent=2))

    schema_func = create_schema_function(send_opeator_message)
    print(schema_func)
    '''
    # Example with a Pydantic model
    from pydantic import BaseModel
    
    
    class ProcessMessages(BaseModel):
        thinking: str
        operator_message: str
    
    def process_messages_pydantic(params: ProcessMessages) -> str:
        """Process messages using Pydantic model parameters."""
        pass
    
    # Generate schema for Pydantic version
    schema_pydantic = generate_tool_schema(
        process_messages_pydantic,
        "Process agent messages with included thinking step"
    )
    
    print("\nPydantic version:")
    print(json.dumps(schema_pydantic, indent=2))
    '''

# Save the schema function to tool_1.py
save_schema_function(send_opeator_message, "tool_1.py")
