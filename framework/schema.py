from typing import Any, Type
from pydantic import BaseModel, Field
from base import ToolFunctionInterface

class CalculatorRequest(BaseModel):
    """A calculator that can evaluate basic mathematical expressions"""
    expression: str = Field(..., description="The mathematical expression to evaluate")

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
    
    return ToolSchema(
        name=tool_instance.name,
        description=tool_instance.parameters.__doc__,
        input_schema=tool_instance.parameters.model_json_schema()
    ).model_dump()

# Example usage for calculator
calculator_schema = create_tool_schema(CalculatorTool)
print(calculator_schema)
