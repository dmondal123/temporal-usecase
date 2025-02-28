def send_agents_message(enums: list[str]) -> dict:
    return {
        "name": "send_agents_message",
        "description": "Use this tool ONLY when absolutely necessary, i.e., when you cannot proceed without critical feformation or assistance from other agents. This should be a last resort when all other options have been exhausted. Only use it if the task is impossible to complete without external agent input.",
        "input schema": {
            "type": "object",
            "properties": {
                "thinking":{
                    "type": "string",
                    "description": "Think out loud if and what action to take next.",
                },
                "agent_messages": {
                    "type": "array",
                    "description": "Messages to send to agents of other operators. Only communicate other agents if absolutely necessary.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "to_id": {
                                "type": "object",
                                "description": "user id of the agent.",
                            "enum": enums,
                            },
                            "message": {
                                "type": "string",
                                "description": "The message to send to agent.",
                            },
                            "agent_type": {
                                    "type": "string",
                                    "description": "The destination agent type",
                            },
                        },
                        "required": ["to_id", "message","agent_type"],
                        "additionalProperties": False,
                        },
                },
            },
            "required": ["thinking", "agent_messages"],
            }
        }

def my_custom_tool() -> dict:
    return {
        "name": "my_custom_tool",
        "description": "Description of what the tool does",
        "input_schema": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of parameter 1"
                },
                # ... other parameters ...
            },
            "required": ["param1"],
        }
    }

def calculator_tool() -> dict:
    return {
        "name": "calculator",
        "description": "Performs basic arithmetic calculations including addition, subtraction, multiplication, and division.",
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The arithmetic operation to perform: add, subtract, multiply, or divide",
                    "enum": ["add", "subtract", "multiply", "divide"]
                },
                "a": {
                    "type": "number",
                    "description": "The first number in the calculation"
                },
                "b": {
                    "type": "number",
                    "description": "The second number in the calculation"
                }
            },
            "required": ["operation", "a", "b"]
        }
    }


