def send_opeator_message():
    return '''{
  "name": "send_opeator_message",
  "description": "send_operator_message' is a tool that allows you to send messages directly to the operator or administrator of a system or application.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thinking": {
        "type": "string",
        "description": "The 'thinking' parameter is a string that represents the thought process or reasoning behind a decision or action. It should be used to provide context or explanation for the function's output or behavior."
      },
      "operator_message": {
        "type": "string",
        "description": "operator_message' is a string parameter representing a message or instruction for an operator or user. It should contain clear and concise information or guidance related to the operation or task at hand."
      }
    },
    "required": [
      "thinking",
      "operator_message"
    ],
    "additionalProperties": false
  }
}'''
