def calculator_tool():
    return '''{
  "name": "calculator_tool",
  "description": "Use this tool ONLY when absolutely necessary, i.e., when you cannot proceed without critical information or assistance from other agents. This should be a last resort when all other options have been exhausted.",
  "input_schema": {
    "properties": {
      "operation": {
        "description": "The 'operation' parameter is a string representing the mathematical operation to be performed on given operands. It should be one of the valid operation symbols like '+', '-', '*', or '/'.",
        "title": "Operation",
        "type": "string"
      },
      "a": {
        "description": "a' is an integer parameter representing a numerical value to be used as input for the function's operations.",
        "title": "A",
        "type": "float"
      },
      "b": {
        "description": "b' is an integer parameter representing a numerical value to be used in the function's operations or calculations.",
        "title": "B",
        "type": "float"
      },
      "output": {
        "description": "The 'output' parameter is an integer that should be used to store or return the result of a computation or operation performed within the function.",
        "title": "Output",
        "type": "float"
      }
    },
    "required": [
      "operation",
      "a",
      "b",
      "output"
    ],
    "title": "calculator_toolInput",
    "type": "object"
  }
}'''
