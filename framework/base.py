from typing import Any, Literal, Optional, Type
from pydantic import BaseModel

class ToolFunctionInterface(BaseModel):
    name: str
    description: str
    parameters: Type[BaseModel]

    def invoke(self, params: Any, *args, **kwargs):
        raise NotImplementedError("invoke() not implemented")
    
class Tool(BaseModel):
    type: Literal["function"] = "function"
    function: ToolFunctionInterface
