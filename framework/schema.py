from typing import Any, Type
from pydantic import BaseModel, Field

class CalculatorRequest(BaseModel):
    """A calculator that can evaluate basic mathematical expressions"""
    expression: str = Field(..., description="The mathematical expression to evaluate")

class ToolFunctionInterface(BaseModel):
    name: str
    description: str
    parameters: Type[BaseModel]

class CalculatorTool(ToolFunctionInterface):
    name: str = "calculator"
    description: str = CalculatorRequest.__doc__
    parameters: Type[CalculatorRequest] = CalculatorRequest


def create_tool_schema(tool_class: Type[ToolFunctionInterface]) -> dict:
    """Create a complete tool schema for any given tool class."""
    tool_instance = tool_class()
    
    class ToolSchema(BaseModel):
        name: str
        description: str
        input_schema: dict
    
    schema = tool_instance.parameters.model_json_schema()
    # Remove the duplicate description from input_schema
    if "description" in schema:
        del schema["description"]
    
    return ToolSchema(
        name=tool_instance.name,
        description=tool_instance.description,
        input_schema=schema
    ).model_dump()

# Example usage for calculator
calculator_schema = create_tool_schema(CalculatorTool)
print(calculator_schema)
