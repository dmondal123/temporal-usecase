from typing import Any, Type
from pydantic import BaseModel, Field
from base import ToolFunctionInterface

class CalculatorRequest(BaseModel):
    expression: str = Field(..., description="The mathematical expression to evaluate")

class CalculatorTool(ToolFunctionInterface):
    name: str = "calculator"
    description: str = "A calculator that can evaluate basic mathematical expressions"
    parameters: Type[CalculatorRequest] = CalculatorRequest


def create_tool_schema(tool_class: Type[ToolFunctionInterface]) -> dict:
    """Create a complete tool schema for any given tool class."""
    tool_instance = tool_class()
    
    schema_dict = {
        "name": tool_instance.name,
        "description": tool_instance.description,
        "input_schema": tool_instance.parameters.model_json_schema(),
    }
    
    class ToolSchema(BaseModel):
        name: str
        description: str
        input_schema: dict
    
    return ToolSchema(**schema_dict).model_dump()

# Example usage for calculator
calculator_schema = create_tool_schema(CalculatorTool)
print(calculator_schema)
