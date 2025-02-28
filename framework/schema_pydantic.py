from typing import Any, Dict, Optional, Type, get_type_hints
from pydantic import BaseModel, create_model, Field
import inspect
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

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

def generate_tool_schema(func, description: str = None) -> Dict[str, Any]:
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
        
        # Define if the field is required based on default value
        is_required = param.default == inspect.Parameter.empty
        
        fields[param_name] = (
            param_type,
            Field(
                description=param_description,
                default=... if is_required else param.default
            )
        )
    
    # Generate tool description if not provided
    if description is None:
        description = generate_parameter_description(func.__name__, is_tool=True)
    
    # Create a Pydantic model for the input schema
    InputModel = create_model(f"{func.__name__}Input", **fields)
    
    # Generate the complete schema
    return {
        "name": func.__name__,
        "description": description,
        "input_schema": InputModel.model_json_schema()
    }

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
    def send_operator_message(thinking: str, operator_message: str) -> str:
        """Process agent messages with thinking step."""
        pass
    
    schema = generate_tool_schema(send_operator_message)
    schema_func = create_schema_function(send_operator_message)
    save_schema_function(send_operator_message, "tool_2.py")