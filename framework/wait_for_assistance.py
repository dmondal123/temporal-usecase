def wait_for_assistance():
    return '''{
  "name": "wait_message",
  "description": "Use this tool ONLY when absolutely necessary, i.e., when you cannot proceed without critical information or assistance from other agents. This should be a last resort when all other options have been exhausted.",
  "input_schema": {
    "properties": {
      "thinking": {
        "description": "The 'thinking' parameter is a string that represents the thought process or reasoning behind a decision or action. It should be used to provide context or explanation for the function's output or behavior.",
        "title": "Thinking",
        "type": "string"
      },
      "wait_message": {
        "description": "wait_message' is a string parameter that represents a message to be displayed while the program is waiting or processing something. It should be a clear and informative message for the user.",
        "title": "Wait_Message",
        "type": "string"
      }
    },
    "required": [
      "thinking",
      "wait_message"
    ],
    "title": "wait_messageInput",
    "type": "object"
  }
}'''
