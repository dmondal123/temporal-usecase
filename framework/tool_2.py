def send_agents_message():
    return '''{
  "name": "send_agents_message",
  "description": "Use this tool ONLY when absolutely necessary, i.e., when you cannot proceed without critical information or assistance from other agents. This should be a last resort when all other options have been exhausted.",
  "input_schema": {
    "$defs": {
      "AgentMessage": {
        "properties": {
          "to_id": {
            "title": "To Id"
          },
          "message": {
            "title": "Message",
            "type": "string"
          },
          "agent_type": {
            "title": "Agent Type",
            "type": "string"
          }
        },
        "required": [
          "to_id",
          "message",
          "agent_type"
        ],
        "title": "AgentMessage",
        "type": "object"
      }
    },
    "properties": {
      "thinking": {
        "description": "The 'thinking' parameter is a string that represents the thought process or reasoning behind a decision or action. It should be used to provide context or explanation for the function's output or behavior.",
        "title": "Thinking",
        "type": "string"
      },
      "agent_messages": {
        "description": "agent_messages' is a list containing messages or responses from an agent or system. It should be used to store and process the agent's outputs.",
        "items": {
          "$ref": "#/$defs/AgentMessage"
        },
        "title": "Agent_Messages",
        "type": "array"
      }
    },
    "required": [
      "thinking",
      "agent_messages"
    ],
    "title": "send_agents_messageInput",
    "type": "object"
  }
}'''
