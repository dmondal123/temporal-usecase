def wait_for_assistance():
    return '''{
  "name": "wait_for_assistance",
  "description": "Use this tool to wait for assistance from the operator.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thinking": {
        "type": "string",
        "description": "The 'thinking' parameter is a string that represents the thought process or reasoning behind a decision or action. It should be used to provide context or explanation for the function's output or behavior."
      },
      "wait_message": {
        "type": "string",
        "description": "wait_message' is a string parameter that represents a message to be displayed while the program is waiting or processing something. It should be a clear and informative message for the user."
      }
    },
    "required": [
      "thinking",
      "wait_message"
    ],
    "additionalProperties": false
  }
}'''
