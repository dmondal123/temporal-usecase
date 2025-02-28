def send_operator_message():
    return '''{
  "name": "send_operator_message",
  "description": "send_operator_message is a tool that allows you to send messages directly to the operator or administrator.",
  "input_schema": {
    "properties": {
      "thinking": {
        "description": "The 'thinking' parameter is a string that represents the thought process or reasoning behind a decision or action. It should be used to provide context or explanation for the function's output or behavior.",
        "title": "Thinking",
        "type": "string"
      },
      "operator_message": {
        "description": "operator_message' is a string parameter representing a message or instruction for an operator or user. It should contain clear and concise information or guidance related to the operation or task at hand.",
        "title": "Operator Message",
        "type": "string"
      }
    },
    "required": [
      "thinking",
      "operator_message"
    ],
    "title": "send_operator_messageInput",
    "type": "object"
  }
}'''
