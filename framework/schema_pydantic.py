from typing import Any, Dict, Optional, Type, get_type_hints, TypedDict, Union
from pydantic import BaseModel, create_model, Field
import inspect
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class ToolFunctionInterface(BaseModel):
    name: str
    description: str
    parameters: Type[BaseModel]

    def invoke(self, params: Any, *args, **kwargs):
        raise NotImplementedError("invoke() not implemented")

class Tool(BaseModel):
    type: str = "function"
    function: ToolFunctionInterface

# Base AgentMessage type with string for to_id
class AgentMessage(TypedDict):
    to_id: str  # Just use str type
    message: str
    agent_type: str

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
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text.strip("'\"")

def generate_tool_schema(func, description: str = None, schema_description: str = None, enums: Dict[str, list] = None) -> Dict[str, Any]:
    """Generate a tool schema from a function signature using Pydantic."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Create field definitions for the input model
    fields = {}
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
            
        param_type = type_hints.get(param_name, Any)
        param_description = generate_parameter_description(param_name, param_type)
        
        field_def = {
            "type": "number" if param_type in (int, float) else "string",
            "description": param_description
        }
        
        # Add enums if provided for this parameter
        if enums and param_name in enums:
            field_def["enum"] = enums[param_name]
        
        fields[param_name] = (
            param_type,
            Field(
                description=param_description,
                default=... if param.default == inspect.Parameter.empty else param.default
            )
        )
    
    # Generate tool description if not provided
    if description is None:
        description = generate_parameter_description(func.__name__, is_tool=True)
    
    # Create the Pydantic model for the input schema
    InputModel = create_model(
        f"{func.__name__}Input",
        **fields
    )
    
    # Generate the simplified schema
    schema = {
        "name": func.__name__.replace("_tool", ""),
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
    
    # Convert Pydantic schema to simplified format
    pydantic_schema = InputModel.model_json_schema()
    for prop_name, prop in pydantic_schema.get("properties", {}).items():
        schema["parameters"]["properties"][prop_name] = {
            "type": prop.get("type", "string"),
            "description": prop.get("description", "")
        }
        if prop_name in pydantic_schema.get("required", []):
            schema["parameters"]["required"].append(prop_name)
        
        # Add enums if they exist for this parameter
        if enums and prop_name in enums:
            schema["parameters"]["properties"][prop_name]["enum"] = enums[prop_name]
    
    return schema

def create_schema_function(func, description: str = None) -> callable:
    """Creates a new function that returns the JSON schema."""
    import json
    
    schema = generate_tool_schema(func, description)
    schema_str = json.dumps(schema, indent=2)
    
    # Create the function definition
    exec_str = f"""def {func.__name__}():
    return '''{schema_str}'''"""
    
    namespace = {}
    exec(exec_str, namespace)
    return namespace[func.__name__]

def save_schema_function(func, output_path: str, description: str = None, enums: list[str] = None):
    """Creates and saves a function that returns the JSON schema to a new file."""
    import json
    
    schema = generate_tool_schema(func, description, enums=enums)
    schema_str = json.dumps(schema, indent=2)
    
    function_code = f"""def {func.__name__}():
    return '''{schema_str}'''
"""
    
    with open(output_path, 'w') as f:
        f.write(function_code)

# Example usage:
if __name__ == "__main__":
    def calculator_tool(operation: str, a: float, b: float) -> None:
        pass
    
    tool_description = "A calculator tool for performing basic arithmetic operations."
    enums = {
        "operation": ["+", "-", "*", "/"]
    }
    
    # Generate calculator tool schema
    save_schema_function(
        calculator_tool,
        "calculator_tool.py",
        description=tool_description,
        enums=enums
    )